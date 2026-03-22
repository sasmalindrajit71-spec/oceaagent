<template>
  <div class="network-wrap">
    <div class="network-controls">
      <div class="legend">
        <span class="legend-item"><span class="dot deep"></span>Deep Agent</span>
        <span class="legend-item"><span class="dot shallow"></span>Shallow Agent</span>
      </div>
      <div class="network-stats dim" v-if="stats">
        {{ stats.node_count }} nodes · {{ stats.edge_count }} edges
        <span v-if="stats.avg_clustering"> · clustering {{ stats.avg_clustering?.toFixed(3) }}</span>
      </div>
    </div>
    <div ref="container" class="graph-container"></div>
    <div v-if="!graphData" class="no-graph dim">
      Network graph available after agent generation.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'

const props = defineProps({ simId: String })

const container = ref(null)
const graphData = ref(null)
const stats = ref(null)
let simulation = null
let svg = null

onMounted(async () => {
  await loadGraph()
})

onUnmounted(() => {
  if (simulation) simulation.stop()
})

async function loadGraph() {
  try {
    const { data } = await axios.get(`/api/simulations/${props.simId}`)
    const kg = data.knowledge_graph
    if (!kg) return

    // Social graph is stored as JSON string inside knowledge_graph
    // We need to fetch agents to build node data
    const { data: agents } = await axios.get(`/api/simulations/${props.simId}/agents`)
    if (!agents.length) return

    // Build a simplified graph from agents (cluster-based)
    buildGraphFromAgents(agents)
  } catch (e) {
    console.error('Graph load error:', e)
  }
}

function buildGraphFromAgents(agents) {
  const nodes = agents.map(a => ({
    id: a.id,
    name: a.name,
    tier: a.tier,
    cluster: a.cluster_id,
    emotion: a.current_emotion,
    influence: a.influence_score,
    lean: a.political_lean,
  }))

  // Build edges: within-cluster connections + some cross-cluster
  const edges = []
  const byCluster = {}
  for (const n of nodes) {
    if (!byCluster[n.cluster]) byCluster[n.cluster] = []
    byCluster[n.cluster].push(n)
  }

  for (const cid in byCluster) {
    const members = byCluster[cid]
    // Connect each to a few cluster-mates
    for (let i = 0; i < members.length; i++) {
      for (let j = i + 1; j < Math.min(i + 4, members.length); j++) {
        edges.push({ source: members[i].id, target: members[j].id, cross: false })
      }
    }
  }

  // Add a few cross-cluster weak ties
  const clusterIds = Object.keys(byCluster)
  for (let i = 0; i < clusterIds.length - 1; i++) {
    const a = byCluster[clusterIds[i]]
    const b = byCluster[clusterIds[i + 1]]
    if (a.length && b.length) {
      edges.push({ source: a[0].id, target: b[0].id, cross: true })
    }
  }

  graphData.value = { nodes, edges }
  stats.value = { node_count: nodes.length, edge_count: edges.length }

  // Limit to 300 nodes for performance
  const displayNodes = nodes.slice(0, 300)
  const nodeIds = new Set(displayNodes.map(n => n.id))
  const displayEdges = edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))

  renderD3(displayNodes, displayEdges)
}

function renderD3(nodes, edges) {
  if (!container.value) return

  // Dynamically import D3
  import('d3').then(d3 => {
    const el = container.value
    el.innerHTML = ''

    const W = el.clientWidth || 700
    const H = el.clientHeight || 460

    svg = d3.select(el)
      .append('svg')
      .attr('width', W)
      .attr('height', H)
      .style('background', 'var(--bg-3)')

    // Zoom
    const g = svg.append('g')
    svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => g.attr('transform', e.transform)))

    // Color by cluster
    const clusterIds = [...new Set(nodes.map(n => n.cluster))]
    const colors = ['#00d4ff', '#00ff88', '#ff4060', '#ffaa00', '#9b59ff', '#ff6b9d', '#4ecdc4']
    const colorMap = Object.fromEntries(clusterIds.map((id, i) => [id, colors[i % colors.length]]))

    // Edges
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', d => d.cross ? '#2a3f57' : '#1e2d3d')
      .attr('stroke-width', d => d.cross ? 1.5 : 0.5)
      .attr('stroke-dasharray', d => d.cross ? '4 2' : null)
      .attr('opacity', 0.6)

    // Nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', d => d.tier === 'deep' ? Math.max(4, d.influence * 5) : 2.5)
      .attr('fill', d => colorMap[d.cluster])
      .attr('opacity', d => d.tier === 'deep' ? 0.95 : 0.5)
      .attr('stroke', d => d.tier === 'deep' ? '#fff' : 'none')
      .attr('stroke-width', 0.5)
      .style('cursor', 'pointer')

    // Labels for deep agents only
    const label = g.append('g')
      .selectAll('text')
      .data(nodes.filter(n => n.tier === 'deep'))
      .join('text')
      .text(d => d.name.split(' ')[0])
      .attr('font-size', 8)
      .attr('fill', '#6a8099')
      .attr('dy', -6)
      .style('pointer-events', 'none')

    // Tooltip
    const tooltip = d3.select(el)
      .append('div')
      .style('position', 'absolute')
      .style('background', 'var(--bg-2)')
      .style('border', '1px solid var(--border)')
      .style('border-radius', '6px')
      .style('padding', '8px 12px')
      .style('font-size', '11px')
      .style('color', 'var(--text)')
      .style('pointer-events', 'none')
      .style('opacity', 0)

    node
      .on('mouseover', (e, d) => {
        tooltip.style('opacity', 1)
          .html(`<strong>${d.name}</strong><br>${d.tier} · cluster ${d.cluster}<br>emotion: ${d.emotion?.toFixed(2)}`)
      })
      .on('mousemove', e => {
        tooltip.style('left', (e.offsetX + 10) + 'px').style('top', (e.offsetY - 20) + 'px')
      })
      .on('mouseout', () => tooltip.style('opacity', 0))

    // D3 force simulation
    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(d => d.cross ? 120 : 40).strength(0.5))
      .force('charge', d3.forceManyBody().strength(d => d.tier === 'deep' ? -80 : -15))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide().radius(d => d.tier === 'deep' ? 10 : 4))
      .on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y)

        node.attr('cx', d => d.x).attr('cy', d => d.y)
        label.attr('x', d => d.x).attr('y', d => d.y)
      })

    // Drag
    node.call(
      d3.drag()
        .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
        .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
    )
  })
}
</script>

<style scoped>
.network-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 520px;
}

.network-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.legend { display: flex; gap: 16px; }

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-dim);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.deep { background: var(--accent); border: 1px solid #fff; }
.dot.shallow { background: var(--accent); opacity: 0.5; }

.network-stats { font-size: 11px; }

.graph-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.graph-container svg { display: block; }

.no-graph {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
}
</style>
