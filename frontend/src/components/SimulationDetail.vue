<template>
  <div class="sim-detail" v-if="sim">
    <!-- Header -->
    <div class="sim-header">
      <div class="sim-header-left">
        <router-link to="/" class="back-link">← Library</router-link>
        <h1>{{ sim.title }}</h1>
        <span :class="`tag tag-${sim.status}`">{{ sim.status }}</span>
      </div>
      <div class="sim-controls">
        <button v-if="sim.status === 'ready' || sim.status === 'paused'" class="btn btn-success" @click="handleStart">
          ▶ {{ sim.status === 'paused' ? 'Resume' : 'Start' }}
        </button>
        <button v-if="sim.status === 'running'" class="btn btn-ghost" @click="handlePause">⏸ Pause</button>
        <button v-if="['completed','paused','running'].includes(sim.status)" class="btn btn-ghost" @click="handleReport" :disabled="reportLoading">
          <span v-if="reportLoading" class="pulse">Generating...</span>
          <span v-else>📊 Report</span>
        </button>
        <button v-if="sim.status === 'running' || sim.status === 'paused'" class="btn btn-amber" @click="showInjectPanel = !showInjectPanel">
          ⚡ Inject
        </button>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="tick-bar">
      <div class="tick-fill" :style="{ width: tickProgress + '%' }" :class="{ 'tick-running': sim.status === 'running' }"></div>
    </div>
    <div class="tick-label">Tick {{ sim.current_tick }} / {{ sim.total_ticks }}<span class="dim" v-if="sim.status === 'running'"> — running</span></div>

    <!-- Workflow steps for pre-run states -->
    <div v-if="['extracting','validating','generating','ready'].includes(sim.status)" class="workflow-panel">
      <WorkflowStepper :sim="sim" @proceed="handleProceed" />
    </div>

    <!-- Simulation workspace -->
    <div v-else class="workspace">
      <div class="tab-row">
        <button v-for="tab in TABS" :key="tab.id" :class="['tab-btn', { active: activeTab === tab.id }]" @click="activeTab = tab.id">
          {{ tab.label }}
        </button>
      </div>

      <div class="tab-panel">

        <!-- ══ MASTER CONSOLE TAB ══ -->
        <div v-if="activeTab === 'console'" class="master-console">

          <!-- TOP STATS BAR -->
          <div class="stats-bar">
            <div class="stat-pill">
              <span class="stat-dot" :class="sim.status === 'running' ? 'dot-green' : 'dot-dim'"></span>
              <span class="stat-label">TICK</span>
              <span class="stat-val">{{ sim.current_tick }} / {{ sim.total_ticks }}</span>
            </div>
            <div class="stat-pill">
              <span class="stat-dot dot-blue"></span>
              <span class="stat-label">DEEP</span>
              <span class="stat-val">{{ deepCount }}</span>
            </div>
            <div class="stat-pill">
              <span class="stat-dot dot-purple"></span>
              <span class="stat-label">SHALLOW</span>
              <span class="stat-val">{{ shallowCount }}</span>
            </div>
            <div class="stat-pill">
              <span class="stat-dot dot-amber"></span>
              <span class="stat-label">INTERACTIONS</span>
              <span class="stat-val">{{ totalInteractions }}</span>
            </div>
            <div class="emotion-gauge">
              <span class="stat-label">AVG EMOTION</span>
              <div class="gauge-track">
                <div class="gauge-fill" :style="gaugeStyle"></div>
                <div class="gauge-center"></div>
              </div>
              <span class="gauge-val" :style="{ color: avgEmotionColor }">{{ avgEmotion >= 0 ? '+' : '' }}{{ avgEmotion.toFixed(2) }}</span>
            </div>
          </div>

          <!-- MAIN GRID -->
          <div class="console-grid">

            <!-- LEFT: NETWORK CANVAS -->
            <div class="net-pane">
              <div class="pane-hdr">AGENT NETWORK</div>
              <canvas ref="networkCanvas" class="net-canvas"></canvas>
              <div class="net-overlay" v-if="activeInteraction">
                <span class="live-dot"></span> LIVE
              </div>
            </div>

            <!-- RIGHT: LIVE FEED -->
            <div class="feed-pane">
              <div class="pane-hdr">LIVE INTERACTIONS</div>

              <!-- Active interaction — typing animation -->
              <transition name="card-slide">
                <div v-if="activeInteraction" class="active-card" :key="activeInteraction.uid">
                  <div class="card-agents">
                    <div class="abadge deep">◈ {{ activeInteraction.agent_a?.name || 'Agent A' }}</div>
                    <span class="vs">⇄</span>
                    <div class="abadge" :class="activeInteraction.agent_b?.tier === 'deep' ? 'deep' : 'shallow'">◉ {{ activeInteraction.agent_b?.name || 'Agent B' }}</div>
                    <span class="tick-chip">T{{ activeInteraction.tick }}</span>
                  </div>

                  <div class="dialogue" v-if="activeInteraction.a_says">
                    <div class="spk-label">{{ activeInteraction.agent_a?.name }}</div>
                    <div class="bubble bubble-a">{{ displayedTextA }}<span class="cur" v-if="isTypingA">|</span></div>
                  </div>

                  <div class="dialogue" v-if="activeInteraction.b_says && !isTypingA">
                    <div class="spk-label right">{{ activeInteraction.agent_b?.name }}</div>
                    <div class="bubble bubble-b">{{ displayedTextB }}<span class="cur" v-if="isTypingB">|</span></div>
                  </div>

                  <div class="shifts" v-if="!isTypingA && !isTypingB && activeInteraction.emotion_delta_a !== undefined">
                    <div class="shift" :class="activeInteraction.emotion_delta_a >= 0 ? 'pos' : 'neg'">
                      {{ activeInteraction.agent_a?.name }} {{ activeInteraction.emotion_delta_a >= 0 ? '↑' : '↓' }} {{ Math.abs(activeInteraction.emotion_delta_a || 0).toFixed(3) }}
                    </div>
                    <div class="shift" :class="(activeInteraction.emotion_delta_b || 0) >= 0 ? 'pos' : 'neg'">
                      {{ activeInteraction.agent_b?.name }} {{ (activeInteraction.emotion_delta_b || 0) >= 0 ? '↑' : '↓' }} {{ Math.abs(activeInteraction.emotion_delta_b || 0).toFixed(3) }}
                    </div>
                  </div>
                </div>
              </transition>

              <!-- History feed -->
              <div class="feed-list" ref="feedScroll">
                <div v-for="(ev, i) in liveEvents.slice(0, 60)" :key="ev.id || i" class="feed-row" :class="{ 'row-deep': ev.data?.agent_a?.tier === 'deep', 'row-stat': ev.data?.type === 'statistical' }">
                  <span class="row-tick">T{{ ev.tick }}</span>
                  <div class="row-body">
                    <div class="row-agents" v-if="ev.data?.agent_a">
                      <span class="rn">{{ ev.data.agent_a.name }}</span>
                      <span class="rarr">→</span>
                      <span class="rn">{{ ev.data.agent_b?.name }}</span>
                    </div>
                    <div class="row-text" v-if="ev.data?.a_says">"{{ (ev.data.a_says || '').slice(0,80) }}{{ (ev.data.a_says || '').length > 80 ? '...' : '' }}"</div>
                    <div class="row-text italic" v-else>statistical interaction</div>
                  </div>
                  <span v-if="ev.data?.emotion_delta_a !== undefined" :class="(ev.data.emotion_delta_a || 0) >= 0 ? 'em-pos' : 'em-neg'">{{ (ev.data.emotion_delta_a || 0) >= 0 ? '▲' : '▼' }}</span>
                </div>
                <div v-if="liveEvents.length === 0" class="feed-empty">Waiting for agent interactions...</div>
              </div>
            </div>
          </div>

          <!-- BELIEF DRIFT TIMELINE -->
          <div class="timeline-wrap">
            <div class="pane-hdr">EMOTION DRIFT OVER TIME</div>
            <canvas ref="timelineCanvas" class="timeline-canvas"></canvas>
          </div>

          <!-- INJECT PANEL -->
          <div v-if="showInjectPanel" class="inject-wrap">
            <div class="inject-lbl">⚡ INJECT EVENT INTO SIMULATION</div>
            <div class="inject-row">
              <input v-model="injectContent" placeholder="e.g. A whistleblower leaks classified documents to the press..." @keydown.enter="handleInject" />
              <button class="btn btn-primary" @click="handleInject" :disabled="!injectContent.trim()">Inject</button>
              <button class="btn btn-ghost" @click="showInjectPanel = false">×</button>
            </div>
          </div>
        </div>

        <!-- AGENTS TAB -->
        <div v-else-if="activeTab === 'agents'" class="agents-panel">
          <div class="agents-filter">
            <button v-for="tier in ['all', 'deep', 'shallow']" :key="tier" :class="['tab-btn', { active: agentFilter === tier }]" @click="agentFilter = tier">
              {{ tier.toUpperCase() }} ({{ agentCounts[tier] }})
            </button>
          </div>
          <div class="agents-grid">
            <div v-for="agent in filteredAgents" :key="agent.id" class="agent-card" :class="{ 'agent-deep': agent.tier === 'deep' }" @click="selectedAgent = agent">
              <div class="agent-header">
                <span class="agent-name">{{ agent.name }}</span>
                <span :class="`tag tag-${agent.tier === 'deep' ? 'completed' : 'pending'}`">{{ agent.tier }}</span>
              </div>
              <div class="agent-meta">{{ agent.age }}y · {{ agent.occupation }} · {{ agent.location }}</div>
              <div class="agent-emotion"><span class="dim">Emotion</span><EmotionBar :value="agent.current_emotion" /></div>
              <div class="agent-lean"><span class="dim">Lean</span><PoliticalLean :value="agent.political_lean" /></div>
              <div class="agent-provider dim">{{ agent.provider }} · {{ agent.model?.split('/').pop()?.split(':')[0] }}</div>
            </div>
          </div>
        </div>

        <!-- NETWORK TAB -->
        <div v-else-if="activeTab === 'network'" class="network-panel">
          <NetworkGraph :sim-id="sim.id" />
        </div>

        <!-- REPORT TAB -->
        <div v-else-if="activeTab === 'report'" class="report-panel">
          <div v-if="!report" class="dim" style="padding:32px;text-align:center">
            <p>No report generated yet.</p>
            <button class="btn btn-primary" style="margin-top:12px" @click="handleReport" :disabled="reportLoading">Generate Report</button>
          </div>
          <div v-else class="report-content">
            <h2>{{ report.title }}</h2>
            <div class="report-stats">
              <div class="stat"><span class="stat-val">{{ report.ticks_completed }}</span><span class="dim">ticks</span></div>
              <div class="stat"><span class="stat-val">{{ report.stats?.total_interactions }}</span><span class="dim">interactions</span></div>
              <div class="stat"><span class="stat-val">{{ report.stats?.avg_emotion_final?.toFixed(3) }}</span><span class="dim">avg emotion</span></div>
            </div>
            <div class="report-narrative">{{ report.narrative }}</div>
            <div class="report-section" v-if="report.patterns?.dominant_narratives?.length">
              <h4>Dominant Narratives</h4>
              <ul><li v-for="n in report.patterns.dominant_narratives" :key="n">{{ n }}</li></ul>
            </div>
            <div class="report-section" v-if="report.influence_ranking?.length">
              <h4>Top Influencers</h4>
              <div class="influencer-list">
                <div v-for="(inf, i) in report.influence_ranking.slice(0,10)" :key="inf.id" class="influencer">
                  <span class="inf-rank">#{{ i + 1 }}</span>
                  <span class="inf-name">{{ inf.name }}</span>
                  <span class="inf-score dim">{{ inf.influence.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Agent inspector modal -->
    <div v-if="selectedAgent" class="modal-overlay" @click.self="selectedAgent = null">
      <AgentInspector :agent="selectedAgent" @close="selectedAgent = null" />
    </div>
  </div>

  <div v-else-if="loading" class="empty-state pulse">Loading simulation...</div>
  <div v-else class="empty-state">Simulation not found.</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useSimulationStore } from '../stores'
import WorkflowStepper from '../components/WorkflowStepper.vue'
import EmotionBar from '../components/EmotionBar.vue'
import PoliticalLean from '../components/PoliticalLean.vue'
import NetworkGraph from '../components/NetworkGraph.vue'
import AgentInspector from '../components/AgentInspector.vue'

const route = useRoute()
const store = useSimulationStore()

const sim = computed(() => store.current)
const loading = computed(() => store.loading)
const agents = computed(() => store.agents)

const activeTab = ref('console')
const agentFilter = ref('all')
const liveEvents = ref([])
const injectContent = ref('')
const selectedAgent = ref(null)
const report = ref(null)
const reportLoading = ref(false)
const showInjectPanel = ref(false)

// Console state
const networkCanvas = ref(null)
const timelineCanvas = ref(null)
const feedScroll = ref(null)
const activeInteraction = ref(null)
const displayedTextA = ref('')
const displayedTextB = ref('')
const isTypingA = ref(false)
const isTypingB = ref(false)
const totalInteractions = ref(0)
const beliefHistory = ref([])
let networkAnimFrame = null
let networkNodes = []
let networkEdges = []
let ripples = []
let lastEventId = null

const TABS = [
  { id: 'console', label: '📡 Console' },
  { id: 'agents', label: '👥 Agents' },
  { id: 'network', label: '🕸 Network' },
  { id: 'report', label: '📊 Report' },
]

const simId = computed(() => route.params.id)
const tickProgress = computed(() => !sim.value ? 0 : (sim.value.current_tick / sim.value.total_ticks) * 100)

const deepCount = computed(() => agents.value.filter(a => a.tier === 'deep').length)
const shallowCount = computed(() => agents.value.filter(a => a.tier === 'shallow').length)
const avgEmotion = computed(() => {
  if (!agents.value.length) return 0
  return agents.value.reduce((s, a) => s + (a.current_emotion || 0), 0) / agents.value.length
})
const avgEmotionColor = computed(() => {
  const v = avgEmotion.value
  if (v > 0.2) return '#00ff88'
  if (v < -0.2) return '#ff4060'
  return '#6a8099'
})
const gaugeStyle = computed(() => {
  const v = avgEmotion.value
  if (v >= 0) return { left: '50%', width: `${Math.min(v * 50, 50)}%`, background: '#00ff88' }
  return { right: '50%', width: `${Math.min(Math.abs(v) * 50, 50)}%`, background: '#ff4060' }
})
const filteredAgents = computed(() => agentFilter.value === 'all' ? agents.value : agents.value.filter(a => a.tier === agentFilter.value))
const agentCounts = computed(() => ({
  all: agents.value.length,
  deep: agents.value.filter(a => a.tier === 'deep').length,
  shallow: agents.value.filter(a => a.tier === 'shallow').length,
}))

// ── Canvas Network ────────────────────────────────────────────────────────────
function buildNetwork(agentList) {
  const c = networkCanvas.value
  if (!c) return
  const W = c.width, H = c.height
  const list = agentList.slice(0, 100)
  networkNodes = list.map((a, i) => {
    const angle = (i / list.length) * Math.PI * 2
    const r = a.tier === 'deep' ? W * 0.22 : W * 0.38
    const jitter = (Math.random() - 0.5) * 35
    return {
      id: a.id, name: a.name || '', tier: a.tier,
      cluster: a.cluster_id || 0,
      emotion: a.current_emotion || 0,
      influence: a.influence_score || 1,
      x: W / 2 + Math.cos(angle) * (r + jitter),
      y: H / 2 + Math.sin(angle) * (r + jitter),
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      phase: Math.random() * Math.PI * 2,
    }
  })
  networkEdges = []
  for (let i = 0; i < networkNodes.length; i++) {
    for (let j = i + 1; j < networkNodes.length; j++) {
      const dx = networkNodes[i].x - networkNodes[j].x
      const dy = networkNodes[i].y - networkNodes[j].y
      const d = Math.sqrt(dx * dx + dy * dy)
      if (d < 70 && Math.random() < 0.35) networkEdges.push({ a: i, b: j, s: 1 - d / 70 })
    }
  }
}

const CLUSTER_COLORS = ['#00d4ff', '#9b59ff', '#00ff88', '#ffaa00', '#ff6b9d', '#4ecdc4', '#ff9f43']

function addRipple(agentId) {
  const n = networkNodes.find(n => n.id === agentId)
  if (n) ripples.push({ x: n.x, y: n.y, r: 0, a: 1 })
}

function drawNet() {
  const c = networkCanvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  const W = c.width, H = c.height
  ctx.clearRect(0, 0, W, H)

  // Edges
  for (const e of networkEdges) {
    const a = networkNodes[e.a], b = networkNodes[e.b]
    if (!a || !b) continue
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y)
    ctx.strokeStyle = `rgba(30,45,61,${e.s * 0.9})`; ctx.lineWidth = 0.5; ctx.stroke()
  }

  // Ripples
  for (let i = ripples.length - 1; i >= 0; i--) {
    const rip = ripples[i]
    rip.r += 1.8; rip.a -= 0.028
    if (rip.a <= 0) { ripples.splice(i, 1); continue }
    ctx.beginPath(); ctx.arc(rip.x, rip.y, rip.r, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(0,212,255,${rip.a})`; ctx.lineWidth = 1.5; ctx.stroke()
  }

  // Nodes
  for (const n of networkNodes) {
    n.x += n.vx; n.y += n.vy
    if (n.x < 15 || n.x > W - 15) n.vx *= -1
    if (n.y < 15 || n.y > H - 15) n.vy *= -1
    n.phase += 0.025
    const pulse = Math.sin(n.phase) * 0.25 + 0.75
    const baseR = n.tier === 'deep' ? 5 + n.influence * 2.5 : 2.5
    const r = baseR * pulse
    const col = CLUSTER_COLORS[n.cluster % CLUSTER_COLORS.length]

    if (n.tier === 'deep') {
      ctx.beginPath(); ctx.arc(n.x, n.y, r * 2.8, 0, Math.PI * 2)
      ctx.fillStyle = col + '14'; ctx.fill()
    }
    ctx.beginPath(); ctx.arc(n.x, n.y, r, 0, Math.PI * 2)
    ctx.fillStyle = col; ctx.globalAlpha = n.tier === 'deep' ? 0.92 : 0.45; ctx.fill(); ctx.globalAlpha = 1

    if (n.tier === 'deep') {
      ctx.beginPath(); ctx.arc(n.x, n.y, r + 2.5, 0, Math.PI * 2)
      ctx.strokeStyle = n.emotion > 0.1 ? '#00ff88' : n.emotion < -0.1 ? '#ff4060' : '#1e2d3d'
      ctx.lineWidth = 1; ctx.globalAlpha = Math.abs(n.emotion) * 0.7 + 0.2; ctx.stroke(); ctx.globalAlpha = 1
    }
  }
  networkAnimFrame = requestAnimationFrame(drawNet)
}

// ── Timeline ──────────────────────────────────────────────────────────────────
function drawTimeline() {
  const c = timelineCanvas.value
  if (!c) return
  const ctx = c.getContext('2d')
  const W = c.width, H = c.height
  const data = beliefHistory.value
  ctx.clearRect(0, 0, W, H)

  // Grid lines
  ctx.strokeStyle = '#1e2d3d'; ctx.lineWidth = 0.5
  for (let i = 0; i <= 4; i++) {
    const y = H / 2 + (i - 2) * H / 4
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke()
  }
  // Zero line
  ctx.strokeStyle = '#2a3f57'; ctx.lineWidth = 1
  ctx.beginPath(); ctx.moveTo(0, H / 2); ctx.lineTo(W, H / 2); ctx.stroke()

  if (data.length < 2) return
  const xStep = W / (data.length - 1)

  // Fill
  ctx.beginPath()
  data.forEach((p, i) => {
    const x = i * xStep, y = H / 2 - p.v * H * 0.42
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.lineTo((data.length - 1) * xStep, H / 2); ctx.lineTo(0, H / 2); ctx.closePath()
  ctx.fillStyle = 'rgba(0,212,255,0.07)'; ctx.fill()

  // Line
  ctx.beginPath()
  data.forEach((p, i) => {
    const x = i * xStep, y = H / 2 - p.v * H * 0.42
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
  })
  ctx.strokeStyle = '#00d4ff'; ctx.lineWidth = 2; ctx.stroke()

  // Latest dot
  const lx = (data.length - 1) * xStep
  const ly = H / 2 - data[data.length - 1].v * H * 0.42
  ctx.beginPath(); ctx.arc(lx, ly, 4, 0, Math.PI * 2)
  ctx.fillStyle = '#00d4ff'; ctx.fill()
}

// ── Typing animation ──────────────────────────────────────────────────────────
async function showInteraction(event) {
  activeInteraction.value = { ...event.data, uid: Date.now(), tick: event.tick }
  displayedTextA.value = ''; displayedTextB.value = ''
  isTypingA.value = true; isTypingB.value = false
  const tA = (event.data.a_says || '').slice(0, 180)
  const tB = (event.data.b_says || '').slice(0, 180)
  for (const ch of tA) { displayedTextA.value += ch; await sleep(15) }
  isTypingA.value = false
  await sleep(250)
  if (tB) {
    isTypingB.value = true
    for (const ch of tB) { displayedTextB.value += ch; await sleep(15) }
    isTypingB.value = false
  }
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

// ── WebSocket & lifecycle ─────────────────────────────────────────────────────
let pollInterval = null

onMounted(async () => {
  await store.fetchSimulation(simId.value)
  if (sim.value?.status && !['extracting','validating','generating'].includes(sim.value.status)) {
    await store.fetchAgents(simId.value)
    await store.fetchInteractions(simId.value)
    liveEvents.value = store.interactions.map(i => ({
      id: i.id, tick: i.tick,
      data: typeof i.content === 'string' ? JSON.parse(i.content || '{}') : i.content,
    })).reverse()
    totalInteractions.value = liveEvents.value.length
  }

  store.connectWebSocket(simId.value, handleWsMessage)

  pollInterval = setInterval(async () => {
    if (['extracting','validating','generating','running'].includes(sim.value?.status)) {
      await store.fetchSimulation(simId.value)
    }
  }, 3000)

  nextTick(() => {
    if (networkCanvas.value) {
      networkCanvas.value.width = networkCanvas.value.offsetWidth || 400
      networkCanvas.value.height = networkCanvas.value.offsetHeight || 300
    }
    if (timelineCanvas.value) {
      timelineCanvas.value.width = timelineCanvas.value.offsetWidth || 800
      timelineCanvas.value.height = timelineCanvas.value.offsetHeight || 60
    }
    if (agents.value.length) buildNetwork(agents.value)
    drawNet()
    drawTimeline()
  })
})

watch(() => agents.value, (list) => {
  if (list.length && networkCanvas.value) buildNetwork(list)
}, { deep: true })

function handleWsMessage(msg) {
  if (msg.type === 'interaction') {
    const evId = msg.id || msg.tick + '-' + Math.random()
    if (evId === lastEventId) return
    lastEventId = evId
    totalInteractions.value++
    liveEvents.value.unshift({ ...msg, id: evId })
    if (liveEvents.value.length > 200) liveEvents.value.pop()
    if (msg.data?.a_says) showInteraction(msg)
    if (msg.data?.agent_a?.id) addRipple(msg.data.agent_a.id)
    beliefHistory.value.push({ tick: sim.value?.current_tick || 0, v: avgEmotion.value })
    if (beliefHistory.value.length > 60) beliefHistory.value.shift()
    nextTick(drawTimeline)
  }
  if (msg.type === 'tick_update' && sim.value) sim.value.current_tick = msg.tick
}

onUnmounted(() => {
  store.disconnectWebSocket()
  if (pollInterval) clearInterval(pollInterval)
  if (networkAnimFrame) cancelAnimationFrame(networkAnimFrame)
})

async function handleStart() { await store.startSimulation(simId.value) }
async function handlePause() { await store.pauseSimulation(simId.value) }
async function handleReport() {
  reportLoading.value = true
  try { report.value = await store.generateReport(simId.value); activeTab.value = 'report' }
  finally { reportLoading.value = false }
}
async function handleInject() {
  if (!injectContent.value.trim()) return
  await store.injectEvent(simId.value, injectContent.value)
  liveEvents.value.unshift({ id: Date.now(), tick: sim.value?.current_tick, data: { a_says: `[INJECTED] ${injectContent.value}`, agent_a: { name: 'OPERATOR', tier: 'deep' }, agent_b: { name: 'SIMULATION', tier: 'deep' } } })
  injectContent.value = ''
}
function handleProceed(action) {
  if (action === 'generate') store.generateAgents(simId.value)
  if (action === 'start') handleStart()
}
</script>

<style scoped>
.sim-detail { padding: 24px 32px; min-height: 100vh; }

.sim-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.sim-header-left { display: flex; flex-direction: column; gap: 6px; }
.sim-header-left h1 { font-size: 24px; }
.back-link { font-size: 11px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em; }
.back-link:hover { color: var(--accent); }
.sim-controls { display: flex; gap: 8px; align-items: center; }

.btn-amber { background: rgba(255,170,0,0.1); color: #ffaa00; border: 1px solid #ffaa00; }
.btn-amber:hover { background: #ffaa00; color: #000; }

.tick-bar { height: 2px; background: var(--bg-4); border-radius: 1px; margin-bottom: 6px; overflow: hidden; }
.tick-fill { height: 100%; background: var(--accent); transition: width 1s linear; }
.tick-running { background: #00ff88; animation: pulse 1.5s ease infinite; }
.tick-label { font-size: 11px; color: var(--text-dim); margin-bottom: 20px; }
.workflow-panel { max-width: 700px; }

/* WORKSPACE */
.workspace { display: flex; flex-direction: column; }
.tab-row { display: flex; gap: 2px; border-bottom: 1px solid var(--border); }
.tab-btn { padding: 8px 16px; background: transparent; color: var(--text-dim); font-size: 12px; font-weight: 700; letter-spacing: 0.04em; border-radius: var(--radius) var(--radius) 0 0; border: 1px solid transparent; border-bottom: none; }
.tab-btn.active { background: var(--bg-2); color: var(--accent); border-color: var(--border); border-bottom-color: var(--bg-2); margin-bottom: -1px; }
.tab-panel { background: var(--bg-2); border: 1px solid var(--border); border-top: none; border-radius: 0 0 var(--radius-lg) var(--radius-lg); min-height: 400px; }

/* ══ MASTER CONSOLE ══ */
.master-console { display: flex; flex-direction: column; }

/* Stats bar */
.stats-bar { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-bottom: 1px solid var(--border); flex-wrap: wrap; background: var(--bg-3); }
.stat-pill { display: flex; align-items: center; gap: 6px; padding: 4px 10px; background: var(--bg-2); border: 1px solid var(--border); border-radius: 20px; }
.stat-dot { width: 7px; height: 7px; border-radius: 50%; }
.dot-green { background: #00ff88; animation: dot-pulse 1.5s ease-in-out infinite; }
.dot-dim { background: #2a3f57; }
.dot-blue { background: #00d4ff; }
.dot-purple { background: #9b59ff; }
.dot-amber { background: #ffaa00; }
@keyframes dot-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(0,255,136,0.5)} 50%{box-shadow:0 0 0 5px rgba(0,255,136,0)} }
.stat-label { font-size: 9px; letter-spacing: 0.1em; color: var(--text-dim); }
.stat-val { font-size: 12px; font-weight: 700; color: var(--text-bright); }
.emotion-gauge { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.gauge-track { width: 100px; height: 6px; background: var(--bg-4); border-radius: 3px; position: relative; overflow: hidden; }
.gauge-fill { position: absolute; height: 100%; border-radius: 3px; transition: width 0.5s ease, right 0.5s ease; }
.gauge-center { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: var(--border-bright); }
.gauge-val { font-size: 11px; font-weight: 700; min-width: 44px; }

/* Console grid */
.console-grid { display: grid; grid-template-columns: 1fr 1.3fr; min-height: 380px; }

/* Network pane */
.net-pane { display: flex; flex-direction: column; border-right: 1px solid var(--border); position: relative; }
.net-canvas { flex: 1; width: 100%; min-height: 340px; display: block; }
.net-overlay { position: absolute; bottom: 10px; left: 12px; display: flex; align-items: center; gap: 6px; font-size: 10px; letter-spacing: 0.1em; color: #00d4ff; background: rgba(0,212,255,0.08); border: 1px solid rgba(0,212,255,0.2); border-radius: 20px; padding: 3px 10px; }
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: #00d4ff; animation: dot-pulse 1.2s ease-in-out infinite; }

/* Feed pane */
.feed-pane { display: flex; flex-direction: column; overflow: hidden; }
.pane-hdr { font-size: 9px; letter-spacing: 0.15em; color: var(--text-dim); padding: 8px 14px 4px; text-transform: uppercase; }

/* Active card */
.active-card { margin: 4px 12px 8px; background: var(--bg-3); border: 1px solid var(--border-bright); border-radius: var(--radius); padding: 12px; flex-shrink: 0; }
.card-agents { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.abadge { display: flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: var(--radius); background: var(--bg-4); color: var(--text-dim); }
.abadge.deep { background: var(--accent-dim); color: var(--accent); }
.abadge.shallow { background: var(--purple-dim); color: var(--purple); }
.vs { color: var(--text-dim); font-size: 14px; }
.tick-chip { margin-left: auto; font-size: 10px; color: var(--accent); letter-spacing: 0.06em; }
.dialogue { margin-bottom: 8px; }
.spk-label { font-size: 10px; color: var(--text-dim); letter-spacing: 0.06em; margin-bottom: 3px; text-transform: uppercase; }
.spk-label.right { text-align: right; }
.bubble { padding: 8px 12px; border-radius: var(--radius); font-size: 12px; line-height: 1.6; color: var(--text); word-break: break-word; }
.bubble-a { background: rgba(0,212,255,0.06); border-left: 2px solid var(--accent); }
.bubble-b { background: rgba(155,89,255,0.06); border-left: 2px solid var(--purple); }
.cur { display: inline-block; color: var(--accent); animation: blink 0.7s step-end infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.shifts { display: flex; gap: 12px; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }
.shift { font-size: 10px; letter-spacing: 0.04em; }
.shift.pos { color: #00ff88; }
.shift.neg { color: #ff4060; }

/* Feed list */
.feed-list { flex: 1; overflow-y: auto; padding: 0 12px 12px; display: flex; flex-direction: column; gap: 4px; }
.feed-row { display: flex; align-items: flex-start; gap: 8px; padding: 6px 10px; border-radius: var(--radius); background: var(--bg-3); border-left: 2px solid var(--border); font-size: 11px; animation: fadeUp 0.25s ease forwards; }
.row-deep { border-left-color: var(--accent); }
.row-stat { opacity: 0.45; }
.row-tick { font-size: 10px; color: var(--accent); font-weight: 700; min-width: 28px; flex-shrink: 0; }
.row-body { flex: 1; overflow: hidden; }
.row-agents { display: flex; align-items: center; gap: 4px; margin-bottom: 2px; }
.rn { color: var(--text-bright); font-weight: 700; }
.rarr { color: var(--text-dim); }
.row-text { color: var(--text-dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.italic { font-style: italic; }
.em-pos { color: #00ff88; flex-shrink: 0; }
.em-neg { color: #ff4060; flex-shrink: 0; }
.feed-empty { color: var(--text-dim); font-size: 12px; padding: 20px; text-align: center; }

/* Timeline */
.timeline-wrap { border-top: 1px solid var(--border); }
.timeline-canvas { width: 100%; height: 60px; display: block; }

/* Inject */
.inject-wrap { padding: 10px 16px; border-top: 1px solid var(--border); background: var(--bg-3); }
.inject-lbl { font-size: 10px; letter-spacing: 0.1em; color: #ffaa00; margin-bottom: 8px; }
.inject-row { display: flex; gap: 8px; }

/* Animations */
.card-slide-enter-active { animation: slideIn 0.28s ease forwards; }
.card-slide-leave-active { animation: slideOut 0.18s ease forwards; }
@keyframes slideIn { from{opacity:0;transform:translateY(-8px)} to{opacity:1;transform:translateY(0)} }
@keyframes slideOut { from{opacity:1;transform:translateY(0)} to{opacity:0;transform:translateY(-6px)} }
@keyframes fadeUp { from{opacity:0;transform:translateY(5px)} to{opacity:1;transform:translateY(0)} }

/* AGENTS TAB */
.agents-panel { padding: 16px; }
.agents-filter { display: flex; gap: 4px; margin-bottom: 16px; }
.agents-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; max-height: 500px; overflow-y: auto; }
.agent-card { background: var(--bg-3); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px; cursor: pointer; transition: var(--transition); display: flex; flex-direction: column; gap: 6px; }
.agent-card:hover { border-color: var(--accent); }
.agent-deep { border-left: 2px solid var(--accent); }
.agent-header { display: flex; justify-content: space-between; align-items: center; }
.agent-name { font-weight: 700; font-size: 13px; }
.agent-meta { font-size: 11px; color: var(--text-dim); }
.agent-emotion, .agent-lean { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.agent-provider { font-size: 10px; margin-top: 2px; }

/* NETWORK TAB */
.network-panel { min-height: 500px; }

/* REPORT TAB */
.report-panel { padding: 24px; }
.report-content { display: flex; flex-direction: column; gap: 20px; }
.report-content h2 { font-size: 22px; }
.report-stats { display: flex; gap: 32px; }
.stat { display: flex; flex-direction: column; }
.stat-val { font-size: 24px; font-weight: 700; color: var(--accent); font-family: var(--font-display); }
.report-narrative { background: var(--bg-3); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; line-height: 1.8; white-space: pre-wrap; }
.report-section h4 { color: var(--accent); margin-bottom: 10px; font-size: 13px; letter-spacing: 0.05em; }
.report-section ul { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.report-section li { padding: 6px 10px; background: var(--bg-3); border-radius: var(--radius); font-size: 12px; }
.influencer-list { display: flex; flex-direction: column; gap: 4px; }
.influencer { display: flex; align-items: center; gap: 10px; padding: 6px 10px; background: var(--bg-3); border-radius: var(--radius); font-size: 12px; }
.inf-rank { color: var(--accent); font-weight: 700; min-width: 28px; }
.inf-name { flex: 1; }
.inf-score { font-size: 11px; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
.empty-state { padding: 80px 32px; text-align: center; color: var(--text-dim); }
</style>