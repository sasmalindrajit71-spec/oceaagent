<template>
  <div class="stepper">
    <div class="steps">
      <div
        v-for="(step, i) in steps"
        :key="step.id"
        class="step"
        :class="{
          'step-done': stepIndex > i,
          'step-active': stepIndex === i,
          'step-pending': stepIndex < i,
        }"
      >
        <div class="step-dot">
          <span v-if="stepIndex > i">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <div class="step-info">
          <div class="step-name">{{ step.label }}</div>
          <div class="step-desc dim">{{ step.desc }}</div>
        </div>
      </div>
    </div>

    <!-- Active step content -->
    <div class="step-content">
      <!-- Extracting -->
      <div v-if="sim.status === 'extracting'" class="state-block">
        <div class="pulse state-icon">⚡</div>
        <p>Running multi-pass Graph RAG extraction...</p>
        <p class="dim">This usually takes 15–30 seconds.</p>
      </div>

      <!-- Validating (graph review) -->
      <div v-else-if="sim.status === 'validating'" class="state-block">
        <div class="graph-validate">
          <div class="graph-header">
            <h3>Knowledge Graph — Review & Approve</h3>
            <p class="dim">Verify the extracted entities and relationships. Edit or remove any incorrect nodes before proceeding.</p>
          </div>

          <div class="graph-sections">
            <!-- Entities -->
            <div class="graph-section">
              <div class="gsec-title">
                Entities
                <button class="btn btn-ghost mini-btn" @click="addEntity">+ Add</button>
              </div>
              <div class="entity-list">
                <div
                  v-for="(entity, i) in entities"
                  :key="entity.id || i"
                  class="entity-item"
                >
                  <span :class="`tag tag-${typeColor(entity.type)}`">{{ entity.type }}</span>
                  <input v-model="entity.label" class="inline-input" />
                  <button class="mini-del" @click="entities.splice(i, 1)">×</button>
                </div>
              </div>
            </div>

            <!-- Topics -->
            <div class="graph-section">
              <div class="gsec-title">Core Topics</div>
              <div class="topics">
                <span
                  v-for="(t, i) in topics"
                  :key="i"
                  class="topic-chip"
                >
                  {{ t }}
                  <button @click="topics.splice(i, 1)">×</button>
                </span>
              </div>
              <input
                v-model="newTopic"
                class="topic-input"
                placeholder="Add topic..."
                @keydown.enter="addTopic"
              />
            </div>

            <!-- Tensions -->
            <div class="graph-section" v-if="tensions.length">
              <div class="gsec-title">Narrative Tensions</div>
              <div v-for="t in tensions" :key="t.description" class="tension-item">
                <span class="tension-bar" :style="{ width: (t.intensity * 100) + '%' }"></span>
                {{ t.description }}
              </div>
            </div>

            <!-- Sentiment -->
            <div class="graph-section">
              <div class="gsec-title">Overall Sentiment</div>
              <div class="sentiment-row">
                <span class="dim">Negative</span>
                <div class="sentiment-bar">
                  <div class="sentiment-fill" :style="{
                    left: '50%',
                    width: Math.abs(sentiment) * 50 + '%',
                    background: sentiment >= 0 ? 'var(--green)' : 'var(--red)',
                    transform: sentiment < 0 ? 'translateX(-100%)' : 'none',
                  }"></div>
                </div>
                <span class="dim">Positive</span>
                <span class="sentiment-val">{{ sentiment?.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <div class="validate-actions">
            <button class="btn btn-primary" @click="approveGraph">
              ✓ Approve & Generate Agents
            </button>
          </div>
        </div>
      </div>

      <!-- Generating agents -->
      <div v-else-if="sim.status === 'generating'" class="state-block">
        <div class="pulse state-icon">🧬</div>
        <p>Generating agent population...</p>
        <p class="dim">Creating {{ sim.deep_agent_count }} deep agents and {{ sim.shallow_agent_count }} shallow agents.</p>
      </div>

      <!-- Ready to start -->
      <div v-else-if="sim.status === 'ready'" class="state-block">
        <div class="state-icon">🚀</div>
        <p>Agents generated. Social network built. Ready to simulate.</p>
        <button class="btn btn-primary" style="margin-top:12px" @click="$emit('proceed', 'start')">
          ▶ Start Simulation
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useSimulationStore } from '../stores'

const props = defineProps({ sim: Object })
const emit = defineEmits(['proceed'])
const store = useSimulationStore()

const STEPS = [
  { id: 'extract', label: 'Graph Extraction', desc: 'Multi-pass RAG pipeline', status: 'extracting' },
  { id: 'validate', label: 'Graph Validation', desc: 'Operator review & approval', status: 'validating' },
  { id: 'generate', label: 'Agent Generation', desc: 'Persona & network creation', status: 'generating' },
  { id: 'ready', label: 'Ready', desc: 'Simulation prepared', status: 'ready' },
]
const steps = STEPS

const stepIndex = computed(() => {
  const idx = STEPS.findIndex(s => s.status === props.sim?.status)
  return idx === -1 ? 0 : idx
})

const kg = computed(() => props.sim?.knowledge_graph || {})
const entities = ref([])
const topics = ref([])
const tensions = ref([])
const sentiment = ref(0)
const newTopic = ref('')

watch(kg, (val) => {
  entities.value = [...(val.entities || [])]
  topics.value = [...(val.core_topics || [])]
  tensions.value = [...(val.narrative_tensions || [])]
  sentiment.value = val.overall_sentiment || 0
}, { immediate: true })

function typeColor(type) {
  const map = { person: 'completed', organization: 'pending', location: 'running', concept: 'paused', event: 'failed', policy: 'extracting' }
  return map[type] || 'pending'
}

function addEntity() {
  entities.value.push({ id: `e${Date.now()}`, label: 'New Entity', type: 'concept', description: '' })
}

function addTopic() {
  if (newTopic.value.trim()) {
    topics.value.push(newTopic.value.trim())
    newTopic.value = ''
  }
}

async function approveGraph() {
  const updatedGraph = {
    ...kg.value,
    entities: entities.value,
    core_topics: topics.value,
    narrative_tensions: tensions.value,
    overall_sentiment: sentiment.value,
  }
  await store.updateGraph(props.sim.id, updatedGraph)
  emit('proceed', 'generate')
  await store.generateAgents(props.sim.id)
}
</script>

<style scoped>
.stepper { display: flex; flex-direction: column; gap: 24px; }

.steps {
  display: flex;
  gap: 0;
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 16px;
  gap: 8px;
}

.step {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  padding: 8px;
  border-radius: var(--radius);
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  color: var(--text-dim);
}

.step-done .step-dot { border-color: var(--green); color: var(--green); background: var(--green-dim); }
.step-active .step-dot { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }

.step-name { font-size: 12px; font-weight: 700; }
.step-desc { font-size: 10px; }
.step-pending .step-name, .step-pending .step-desc { color: var(--text-dim); }

.step-content {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.state-block { text-align: center; padding: 32px; }
.state-icon { font-size: 36px; margin-bottom: 16px; }

/* Graph validation */
.graph-validate { display: flex; flex-direction: column; gap: 20px; }
.graph-header h3 { font-size: 16px; margin-bottom: 6px; }

.graph-sections { display: flex; flex-direction: column; gap: 16px; }

.graph-section {
  background: var(--bg-3);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
}

.gsec-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.entity-list { display: flex; flex-direction: column; gap: 6px; max-height: 200px; overflow-y: auto; }
.entity-item { display: flex; align-items: center; gap: 8px; }

.inline-input {
  flex: 1;
  padding: 4px 8px;
  font-size: 12px;
  background: var(--bg-4);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
}

.mini-del {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
}
.mini-del:hover { color: var(--red); }

.mini-btn { padding: 2px 8px; font-size: 10px; }

.topics { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.topic-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  background: var(--accent-dim);
  color: var(--accent);
  border-radius: 20px;
  font-size: 11px;
}
.topic-chip button { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 14px; line-height: 1; }
.topic-input { font-size: 12px; padding: 4px 8px; }

.tension-item {
  position: relative;
  padding: 6px 10px;
  font-size: 12px;
  background: var(--bg-4);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}
.tension-bar {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  background: var(--red-dim);
  opacity: 0.5;
}

.sentiment-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}
.sentiment-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-4);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}
.sentiment-fill {
  position: absolute;
  height: 100%;
  top: 0;
  border-radius: 4px;
}
.sentiment-val { min-width: 40px; text-align: right; color: var(--accent); font-weight: 700; }

.validate-actions { display: flex; gap: 10px; }
</style>
