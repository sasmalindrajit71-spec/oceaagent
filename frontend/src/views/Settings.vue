<template>
  <div class="page-bg">
    <div class="inner">
      <div class="eyebrow">— System Configuration</div>

      <!-- ══ NVIDIA NIM ══ -->
      <div class="grp nvidia-grp" :class="{ 'grp-active': nvidiaActive }">
        <div class="grp-hdr">
          <div class="grp-hdr-left">
            <div class="provider-logo nvidia-logo">NV</div>
            <div>
              <div class="grp-t">NVIDIA NIM <span class="recommended-pill">RECOMMENDED</span></div>
              <div class="grp-s">400+ models · Nemotron · Llama · DeepSeek R1 · Qwen3 · Mistral</div>
            </div>
          </div>
          <span class="status-badge" :class="nvidiaActive ? 'badge-on' : 'badge-off'">
            {{ nvidiaActive ? '● Active' : '○ Inactive' }}
          </span>
        </div>

        <div class="grp-body">
          <!-- Saved key display -->
          <div v-if="nvidiaSavedKey && !nvidiaEdit" class="saved-key-box">
            <div class="saved-key-label">Saved API Key</div>
            <div class="saved-key-row">
              <code class="saved-key-val">{{ nvidiaSavedKey }}</code>
              <button class="btn-xs" @click="nvidiaEdit = true">Change</button>
            </div>
            <div class="saved-ok">✓ Key active — NVIDIA NIM is your primary provider</div>
          </div>

          <div v-if="!nvidiaSavedKey || nvidiaEdit">
            <div class="flabel">NVIDIA API Key (starts with nvapi-)</div>
            <div class="key-row">
              <input class="sinp" :type="showNV ? 'text' : 'password'" placeholder="nvapi-..." v-model="nvidiaKey" />
              <button class="btn-xs" @click="showNV = !showNV">{{ showNV ? 'Hide' : 'Show' }}</button>
              <button class="btn-xs primary" @click="saveNvidia" :disabled="savingNV || !nvidiaKey.trim()">
                {{ savingNV ? 'Saving...' : 'Save Key' }}
              </button>
            </div>
            <div class="field-hint">
              Get free key at
              <a href="https://build.nvidia.com" target="_blank">build.nvidia.com</a>
              → Sign In → Get API Key
            </div>
            <button v-if="nvidiaEdit" class="btn-xs" style="margin-top:8px" @click="nvidiaEdit=false">Cancel</button>
          </div>

          <div v-if="nvMsg" :class="nvMsg.startsWith('✓') ? 'msg-ok' : 'msg-err'">{{ nvMsg }}</div>

          <!-- Model assignment per role -->
          <div class="model-assignment" v-if="nvidiaActive || nvidiaSavedKey">
            <div class="ma-title">Model Assignment by Role</div>
            <div class="ma-grid">
              <div v-for="role in roles" :key="role.key" class="ma-row">
                <div class="ma-role">
                  <div class="ma-role-name">{{ role.label }}</div>
                  <div class="ma-role-desc">{{ role.desc }}</div>
                </div>
                <select class="fsel-sm" v-model="nvidiaModels[role.key]" @change="saveNvidiaModels">
                  <optgroup v-for="(group, gname) in groupedModels" :key="gname" :label="gname">
                    <option v-for="m in group" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </optgroup>
                </select>
              </div>
            </div>
            <div class="ma-tip">
              💡 Use <strong>Nemotron Super 49B</strong> or <strong>DeepSeek R1</strong> for deep agents and reports.
              Use <strong>Llama 3.1 8B</strong> for shallow/fast roles.
            </div>
          </div>
        </div>
      </div>

      <!-- ══ GROQ ══ -->
      <div class="grp" :class="{ 'grp-active': groqActive }">
        <div class="grp-hdr">
          <div class="grp-hdr-left">
            <div class="provider-logo">GQ</div>
            <div>
              <div class="grp-t">Groq <span class="fallback-pill">FALLBACK</span></div>
              <div class="grp-s">llama-3.3-70b-versatile · Fast inference</div>
            </div>
          </div>
          <span class="status-badge" :class="groqActive ? 'badge-on' : 'badge-off'">
            {{ groqActive ? '● Active' : '○ Inactive' }}
          </span>
        </div>
        <div class="grp-body">
          <div v-if="groqSavedKey && !groqEdit" class="saved-key-box">
            <div class="saved-key-label">Saved API Key</div>
            <div class="saved-key-row">
              <code class="saved-key-val">{{ groqSavedKey }}</code>
              <button class="btn-xs" @click="groqEdit = true">Change</button>
            </div>
            <div class="saved-ok">✓ Key saved</div>
          </div>
          <div v-if="!groqSavedKey || groqEdit">
            <div class="flabel">Groq API Key</div>
            <div class="key-row">
              <input class="sinp" :type="showGQ ? 'text' : 'password'" placeholder="gsk_..." v-model="groqKey" />
              <button class="btn-xs" @click="showGQ = !showGQ">{{ showGQ ? 'Hide' : 'Show' }}</button>
              <button class="btn-xs primary" @click="saveGroq" :disabled="savingGQ || !groqKey.trim()">
                {{ savingGQ ? 'Saving...' : 'Save Key' }}
              </button>
            </div>
            <div class="field-hint">Get free key at <a href="https://console.groq.com" target="_blank">console.groq.com</a></div>
            <button v-if="groqEdit" class="btn-xs" style="margin-top:8px" @click="groqEdit=false">Cancel</button>
          </div>
          <div v-if="gqMsg" :class="gqMsg.startsWith('✓') ? 'msg-ok' : 'msg-err'">{{ gqMsg }}</div>

          <!-- ── Groq model selector (NEW) ── -->
          <div class="model-assignment" v-if="groqActive || groqSavedKey">
            <div class="ma-title">Model Selection</div>
            <div class="ma-grid">
              <div v-for="role in roles" :key="role.key" class="ma-row">
                <div class="ma-role">
                  <div class="ma-role-name">{{ role.label }}</div>
                  <div class="ma-role-desc">{{ role.desc }}</div>
                </div>
                <select class="fsel-sm" v-model="groqModels[role.key]" @change="saveGroqModels">
                  <option v-for="m in groqModelList" :key="m.id" :value="m.id">{{ m.name }}</option>
                </select>
              </div>
            </div>
            <div class="ma-tip">💡 <strong>llama-3.3-70b-versatile</strong> is best for deep agents. Use <strong>llama-3.1-8b-instant</strong> for fast/shallow roles.</div>
          </div>
        </div>
      </div>

      <!-- ══ OPENROUTER ══ -->
      <div class="grp" :class="{ 'grp-active': orActive }">
        <div class="grp-hdr">
          <div class="grp-hdr-left">
            <div class="provider-logo">OR</div>
            <div>
              <div class="grp-t">OpenRouter <span class="fallback-pill">FALLBACK</span></div>
              <div class="grp-s">Access 200+ models including free-tier options</div>
            </div>
          </div>
          <span class="status-badge" :class="orActive ? 'badge-on' : 'badge-off'">
            {{ orActive ? '● Active' : '○ Inactive' }}
          </span>
        </div>
        <div class="grp-body">
          <div v-if="orSavedKey && !orEdit" class="saved-key-box">
            <div class="saved-key-label">Saved API Key</div>
            <div class="saved-key-row">
              <code class="saved-key-val">{{ orSavedKey }}</code>
              <button class="btn-xs" @click="orEdit = true">Change</button>
            </div>
            <div class="saved-ok">✓ Key saved</div>
          </div>
          <div v-if="!orSavedKey || orEdit">
            <div class="flabel">OpenRouter API Key</div>
            <div class="key-row">
              <input class="sinp" :type="showOR ? 'text' : 'password'" placeholder="sk-or-v1-..." v-model="orKey" />
              <button class="btn-xs" @click="showOR = !showOR">{{ showOR ? 'Hide' : 'Show' }}</button>
              <button class="btn-xs primary" @click="saveOR" :disabled="savingOR || !orKey.trim()">
                {{ savingOR ? 'Saving...' : 'Save Key' }}
              </button>
            </div>
            <div class="field-hint">Get free key at <a href="https://openrouter.ai" target="_blank">openrouter.ai</a></div>
            <button v-if="orEdit" class="btn-xs" style="margin-top:8px" @click="orEdit=false">Cancel</button>
          </div>
          <div v-if="orMsg" :class="orMsg.startsWith('✓') ? 'msg-ok' : 'msg-err'">{{ orMsg }}</div>

          <!-- ── OpenRouter model selector (NEW) ── -->
          <div class="model-assignment" v-if="orActive || orSavedKey">
            <div class="ma-title">Model Selection</div>
            <div class="ma-grid">
              <div v-for="role in roles" :key="role.key" class="ma-row">
                <div class="ma-role">
                  <div class="ma-role-name">{{ role.label }}</div>
                  <div class="ma-role-desc">{{ role.desc }}</div>
                </div>
                <select class="fsel-sm" v-model="orModels[role.key]" @change="saveORModels">
                  <optgroup label="Free models">
                    <option v-for="m in orModelList.filter(x => x.free)" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </optgroup>
                  <optgroup label="Paid models">
                    <option v-for="m in orModelList.filter(x => !x.free)" :key="m.id" :value="m.id">{{ m.name }}</option>
                  </optgroup>
                </select>
              </div>
            </div>
            <div class="ma-tip">💡 <strong>deepseek-chat-v3:free</strong> is a strong free option. <strong>claude-3.5-sonnet</strong> gives best quality for reports.</div>
          </div>
        </div>
      </div>

      <!-- ══ PROVIDER PRIORITY ══ -->
      <div class="grp">
        <div class="grp-hdr">
          <div>
            <div class="grp-t">Provider Priority</div>
            <div class="grp-s">Auto-failover order</div>
          </div>
        </div>
        <div class="grp-body priority-list">
          <div class="priority-row" v-for="(p, i) in priorityOrder" :key="p.name" :class="{ 'p-active': p.active }">
            <span class="p-num">{{ i + 1 }}</span>
            <span class="p-name">{{ p.name }}</span>
            <span class="p-status" :class="p.active ? 'p-on' : 'p-off'">{{ p.active ? 'Ready' : 'Not configured' }}</span>
          </div>
          <p class="priority-note">OCEAN tries providers in this order. If one fails or rate-limits, it automatically falls back to the next.</p>
        </div>
      </div>

      <!-- ══ SIMULATION DEFAULTS ══ -->
      <div class="grp">
        <div class="grp-hdr"><span class="grp-t">Simulation Defaults</span></div>
        <div class="grp-body">
          <div v-for="r in simRows" :key="r.key" class="srow">
            <div><div class="sname">{{ r.label }}</div><div class="sdesc">{{ r.desc }}</div></div>
            <input class="sinp sm" type="text" v-model="r.val" />
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE } from '../api.js'

const API = API_BASE

// ── NVIDIA state ──────────────────────────────────────────────────────────────
const nvidiaKey      = ref('')
const nvidiaSavedKey = ref('')
const nvidiaEdit     = ref(false)
const nvidiaActive   = ref(false)
const showNV         = ref(false)
const savingNV       = ref(false)
const nvMsg          = ref('')
const nvidiaModels   = reactive({
  deep_agent:    'meta/llama-3.3-70b-instruct',
  shallow_agent: 'meta/llama-3.1-8b-instruct',
  evaluator:     'nvidia/llama-3.3-nemotron-super-49b-v1',
  graph_rag:     'meta/llama-3.3-70b-instruct',
  report_engine: 'nvidia/nemotron-3-super-120b-a12b',
})
const allNvidiaModels = ref([])
const modelInfo       = ref({})

// ── Groq state ────────────────────────────────────────────────────────────────
const groqKey      = ref('')
const groqSavedKey = ref('')
const groqEdit     = ref(false)
const groqActive   = ref(false)
const showGQ       = ref(false)
const savingGQ     = ref(false)
const gqMsg        = ref('')
const groqModels   = reactive({
  deep_agent:    'llama-3.3-70b-versatile',
  shallow_agent: 'llama-3.1-8b-instant',
  evaluator:     'llama-3.3-70b-versatile',
  graph_rag:     'llama-3.3-70b-versatile',
  report_engine: 'llama-3.3-70b-versatile',
})

// Available Groq models
const groqModelList = [
  { id: 'llama-3.3-70b-versatile',   name: 'Llama 3.3 70B Versatile (best)' },
  { id: 'llama-3.1-70b-versatile',   name: 'Llama 3.1 70B Versatile' },
  { id: 'llama-3.1-8b-instant',      name: 'Llama 3.1 8B Instant (fast)' },
  { id: 'mixtral-8x7b-32768',        name: 'Mixtral 8x7B' },
  { id: 'gemma2-9b-it',              name: 'Gemma 2 9B' },
]

// ── OpenRouter state ──────────────────────────────────────────────────────────
const orKey      = ref('')
const orSavedKey = ref('')
const orEdit     = ref(false)
const orActive   = ref(false)
const showOR     = ref(false)
const savingOR   = ref(false)
const orMsg      = ref('')
const orModels   = reactive({
  deep_agent:    'deepseek/deepseek-chat-v3-0324:free',
  shallow_agent: 'deepseek/deepseek-chat-v3-0324:free',
  evaluator:     'deepseek/deepseek-chat-v3-0324:free',
  graph_rag:     'deepseek/deepseek-chat-v3-0324:free',
  report_engine: 'deepseek/deepseek-chat-v3-0324:free',
})

// Available OpenRouter models
const orModelList = [
  { id: 'deepseek/deepseek-chat-v3-0324:free',       name: 'DeepSeek Chat V3 (free)',          free: true  },
  { id: 'meta-llama/llama-3.3-70b-instruct:free',    name: 'Llama 3.3 70B (free)',             free: true  },
  { id: 'mistralai/mistral-7b-instruct:free',         name: 'Mistral 7B (free)',                free: true  },
  { id: 'anthropic/claude-3.5-sonnet',               name: 'Claude 3.5 Sonnet (paid)',         free: false },
  { id: 'anthropic/claude-3-haiku',                  name: 'Claude 3 Haiku (paid)',            free: false },
  { id: 'openai/gpt-4o',                             name: 'GPT-4o (paid)',                    free: false },
  { id: 'openai/gpt-4o-mini',                        name: 'GPT-4o Mini (paid)',               free: false },
  { id: 'google/gemini-pro-1.5',                     name: 'Gemini Pro 1.5 (paid)',            free: false },
  { id: 'meta-llama/llama-3.1-70b-instruct',         name: 'Llama 3.1 70B (paid)',             free: false },
]

// ── Role definitions ───────────────────────────────────────────────────────────
const roles = [
  { key: 'deep_agent',    label: 'Deep Agent',    desc: 'LLM-powered agent reasoning and dialogue' },
  { key: 'shallow_agent', label: 'Shallow Agent',  desc: 'Statistical agent — use fast/small model' },
  { key: 'evaluator',     label: 'Evaluator',     desc: 'Assesses belief shifts and emotion changes' },
  { key: 'graph_rag',     label: 'Graph RAG',     desc: 'Extracts knowledge graph from seed text' },
  { key: 'report_engine', label: 'Report Engine', desc: 'Generates final intelligence briefing' },
]

const simRows = ref([
  { key: 'ticks',   label: 'Default tick count',  desc: 'ticks per simulation run',   val: '30'   },
  { key: 'decay',   label: 'Memory decay rate',   desc: 'exponential coefficient',    val: '0.05' },
  { key: 'agents',  label: 'Default agent count', desc: 'deep agents per simulation', val: '20'   },
])

// Group NVIDIA models by tier for dropdown
const groupedModels = computed(() => {
  const info = modelInfo.value
  const groups = { 'Flagship': [], 'Reasoning': [], 'Balanced': [], 'Fast': [] }
  const tierMap = { flagship: 'Flagship', reasoning: 'Reasoning', balanced: 'Balanced', fast: 'Fast' }
  Object.entries(info).forEach(([id, meta]) => {
    const g = tierMap[meta.tier] || 'Balanced'
    groups[g].push({ id, name: `${meta.name} (${meta.ctx})` })
  })
  return groups
})

// Priority order display
const priorityOrder = computed(() => [
  { name: 'NVIDIA NIM',   active: nvidiaActive.value },
  { name: 'OpenRouter',   active: orActive.value },
  { name: 'Groq',         active: groqActive.value },
])

// ── Load on mount ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadProviderState(), loadNvidiaModels()])
})

async function loadProviderState() {
  try {
    const [{ data: prov }, { data: active }] = await Promise.all([
      axios.get(`${API}/settings/providers`),
      axios.get(`${API}/settings/active-providers`),
    ])

    const activeList = active.providers || []

    // NVIDIA
    if (prov.nvidia?.api_key && prov.nvidia.api_key !== '****' && prov.nvidia.enabled) {
      nvidiaSavedKey.value = prov.nvidia.api_key
      if (prov.nvidia.models) Object.assign(nvidiaModels, prov.nvidia.models)
    }
    nvidiaActive.value = activeList.includes('nvidia')

    // Groq
    if (prov.groq?.api_key && prov.groq.api_key !== '****' && prov.groq.enabled) {
      groqSavedKey.value = prov.groq.api_key
      if (prov.groq.models) Object.assign(groqModels, prov.groq.models)
    }
    groqActive.value = activeList.includes('groq')

    // OpenRouter
    if (prov.openrouter?.api_key && prov.openrouter.api_key !== '****' && prov.openrouter.enabled) {
      orSavedKey.value = prov.openrouter.api_key
      if (prov.openrouter.models) Object.assign(orModels, prov.openrouter.models)
    }
    orActive.value = activeList.includes('openrouter')

  } catch (e) { console.error('Failed to load settings:', e) }
}

async function loadNvidiaModels() {
  try {
    const { data } = await axios.get(`${API}/settings/nvidia/models`)
    modelInfo.value = data.info || {}
    allNvidiaModels.value = Object.keys(data.info || {})
  } catch (e) { console.error('Failed to load NVIDIA models:', e) }
}

// ── Save functions ─────────────────────────────────────────────────────────────
async function saveNvidia() {
  const key = nvidiaKey.value.trim()
  if (!key) return
  if (!key.startsWith('nvapi-')) {
    nvMsg.value = '✗ Key must start with nvapi-'
    return
  }
  savingNV.value = true; nvMsg.value = ''
  try {
    await axios.patch(`${API}/settings/providers/nvidia`, {
      api_key: key,
      enabled: true,
      models: { ...nvidiaModels },
    })
    await loadProviderState()
    nvidiaKey.value = ''; nvidiaEdit.value = false
    nvMsg.value = '✓ NVIDIA NIM key saved — now your primary provider'
    setTimeout(() => nvMsg.value = '', 5000)
  } catch (e) {
    nvMsg.value = '✗ ' + (e.response?.data?.detail || e.message)
  } finally { savingNV.value = false }
}

async function saveNvidiaModels() {
  if (!nvidiaSavedKey.value && !nvidiaKey.value) return
  try {
    await axios.patch(`${API}/settings/providers/nvidia`, { models: { ...nvidiaModels } })
  } catch (e) { console.error('Failed to save NVIDIA model assignments:', e) }
}

async function saveGroq() {
  const key = groqKey.value.trim()
  if (!key) return
  savingGQ.value = true; gqMsg.value = ''
  try {
    await axios.patch(`${API}/settings/providers/groq`, {
      api_key: key,
      enabled: true,
      models: { ...groqModels },
    })
    await loadProviderState()
    groqKey.value = ''; groqEdit.value = false
    gqMsg.value = '✓ Groq key saved'
    setTimeout(() => gqMsg.value = '', 4000)
  } catch (e) {
    gqMsg.value = '✗ ' + (e.response?.data?.detail || e.message)
  } finally { savingGQ.value = false }
}

async function saveGroqModels() {
  if (!groqSavedKey.value) return
  try {
    await axios.patch(`${API}/settings/providers/groq`, { models: { ...groqModels } })
  } catch (e) { console.error('Failed to save Groq model assignments:', e) }
}

async function saveOR() {
  const key = orKey.value.trim()
  if (!key) return
  savingOR.value = true; orMsg.value = ''
  try {
    await axios.patch(`${API}/settings/providers/openrouter`, {
      api_key: key,
      enabled: true,
      models: { ...orModels },
    })
    await loadProviderState()
    orKey.value = ''; orEdit.value = false
    orMsg.value = '✓ OpenRouter key saved'
    setTimeout(() => orMsg.value = '', 4000)
  } catch (e) {
    orMsg.value = '✗ ' + (e.response?.data?.detail || e.message)
  } finally { savingOR.value = false }
}

async function saveORModels() {
  if (!orSavedKey.value) return
  try {
    await axios.patch(`${API}/settings/providers/openrouter`, { models: { ...orModels } })
  } catch (e) { console.error('Failed to save OpenRouter model assignments:', e) }
}
</script>

<style scoped>
.page-bg { min-height: calc(100vh - 54px); background: rgba(0,0,0,0.82); padding: 3rem 2rem; overflow-y: auto; }
.inner { max-width: 700px; margin: 0 auto; }

.eyebrow { font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.28em; text-transform: uppercase; color: rgba(255,255,255,0.30); margin-bottom: 2.2rem; }

/* Groups */
.grp { border: 1px solid rgba(255,255,255,0.10); margin-bottom: 2px; transition: border-color 0.2s; }
.grp-active { border-color: rgba(255,255,255,0.22); }
.nvidia-grp.grp-active { border-color: rgba(118,185,0,0.35); }

.grp-hdr { padding: 1.1rem 1.4rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; }
.grp-hdr-left { display: flex; align-items: center; gap: 14px; }
.provider-logo { width: 40px; height: 40px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.14); display: flex; align-items: center; justify-content: center; font-family: 'Courier New', monospace; font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0; }
.nvidia-logo { background: rgba(118,185,0,0.10); border-color: rgba(118,185,0,0.35); color: #76b900; }
.grp-t { font-family: 'Courier New', monospace; font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.70); }
.grp-s { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.35); margin-top: 3px; }

.recommended-pill { font-size: 9px; padding: 2px 7px; background: rgba(118,185,0,0.15); color: #76b900; border: 1px solid rgba(118,185,0,0.35); border-radius: 1px; margin-left: 8px; letter-spacing: 0.1em; }
.fallback-pill    { font-size: 9px; padding: 2px 7px; background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.50); border: 1px solid rgba(255,255,255,0.14); border-radius: 1px; margin-left: 8px; letter-spacing: 0.1em; }

.status-badge { font-family: 'Courier New', monospace; font-size: 10px; padding: 4px 12px; border-radius: 1px; border: 1px solid; white-space: nowrap; }
.badge-on  { color: rgba(255,255,255,0.85); border-color: rgba(255,255,255,0.25); background: rgba(255,255,255,0.07); }
.badge-off { color: rgba(255,255,255,0.30); border-color: rgba(255,255,255,0.08); background: transparent; }

.grp-body { padding: 1.4rem; border-top: 1px solid rgba(255,255,255,0.07); display: flex; flex-direction: column; gap: 14px; }

/* Saved key */
.saved-key-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.10); border-radius: 2px; padding: 14px; display: flex; flex-direction: column; gap: 8px; }
.saved-key-label { font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.35); }
.saved-key-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.saved-key-val { font-family: 'Courier New', monospace; font-size: 13px; color: rgba(255,255,255,0.85); background: rgba(255,255,255,0.06); padding: 4px 10px; border-radius: 2px; }
.saved-ok { font-family: 'Courier New', monospace; font-size: 11px; color: rgba(118,185,0,0.85); }

/* Key input */
.flabel { font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.45); margin-bottom: 8px; display: block; }
.key-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.sinp { flex: 1; min-width: 160px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.14); border-radius: 2px; color: #fff; font-family: 'Courier New', monospace; font-size: 13px; padding: 10px 14px; outline: none; transition: border-color 0.2s; }
.sinp:focus { border-color: rgba(255,255,255,0.38); }
.sinp.sm { flex: 0 0 70px; text-align: center; }
.field-hint { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.32); }
.field-hint a { color: rgba(255,255,255,0.60); }

/* Buttons */
.btn-xs { padding: 9px 14px; background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15); border-radius: 2px; color: rgba(255,255,255,0.75); font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
.btn-xs:hover { border-color: rgba(255,255,255,0.38); color: #fff; }
.btn-xs.primary { background: #fff; color: #000; border-color: #fff; }
.btn-xs.primary:hover { background: rgba(255,255,255,0.88); }
.btn-xs:disabled { opacity: 0.35; cursor: not-allowed; }

/* Messages */
.msg-ok  { font-family: 'Courier New', monospace; font-size: 11px; color: rgba(118,185,0,0.90); letter-spacing: 0.06em; }
.msg-err { font-family: 'Courier New', monospace; font-size: 11px; color: rgba(255,100,100,0.90); letter-spacing: 0.06em; }

/* Model assignment */
.model-assignment { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 2px; padding: 16px; }
.ma-title { font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.38); margin-bottom: 14px; }
.ma-grid  { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.ma-row   { display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
.ma-row:last-child { border-bottom: none; }
.ma-role-name { font-size: 13px; font-weight: 700; color: #fff; }
.ma-role-desc { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.32); margin-top: 3px; }
.fsel-sm  { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.14); border-radius: 2px; color: #fff; font-family: 'Courier New', monospace; font-size: 11px; padding: 8px 12px; outline: none; min-width: 220px; appearance: none; cursor: pointer; }
.fsel-sm option   { background: #111; }
.fsel-sm optgroup { background: #000; color: rgba(255,255,255,0.4); font-size: 10px; }
.ma-tip   { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.30); line-height: 1.7; border-top: 1px solid rgba(255,255,255,0.07); padding-top: 12px; }
.ma-tip strong { color: rgba(255,255,255,0.58); font-weight: 400; }

/* Priority */
.priority-row { display: flex; align-items: center; gap: 14px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); flex-wrap: wrap; }
.priority-row:last-of-type { border-bottom: none; }
.p-num  { font-family: 'Courier New', monospace; font-size: 14px; font-weight: 900; color: rgba(255,255,255,0.18); width: 22px; flex-shrink: 0; }
.p-active .p-num  { color: rgba(255,255,255,0.75); }
.p-name { font-size: 14px; font-weight: 700; color: rgba(255,255,255,0.45); flex: 1; }
.p-active .p-name { color: #fff; }
.p-status { font-family: 'Courier New', monospace; font-size: 10px; }
.p-on  { color: rgba(118,185,0,0.85); }
.p-off { color: rgba(255,255,255,0.28); }
.priority-note { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.22); line-height: 1.8; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.07); padding-top: 12px; }

/* Sim defaults */
.srow { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); gap: 16px; }
.srow:last-child { border-bottom: none; padding-bottom: 0; }
.sname { font-size: 13px; font-weight: 700; color: #fff; }
.sdesc { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.32); margin-top: 2px; }

/* ── Mobile ── */
@media (max-width: 768px) {
  .page-bg { padding: 1.5rem 1rem; }
  .inner { max-width: 100%; }
  .grp-hdr { flex-direction: column; align-items: flex-start; }
  .grp-body { padding: 1rem; }
  .key-row { flex-direction: column; align-items: stretch; }
  .key-row .sinp   { min-width: 0; width: 100%; }
  .key-row .btn-xs { width: 100%; text-align: center; }
  .saved-key-row { flex-wrap: wrap; }
  .ma-row { grid-template-columns: 1fr; gap: 6px; }
  .fsel-sm { min-width: 0; width: 100%; }
  .srow { flex-direction: column; align-items: flex-start; }
  .srow .sinp { width: 100%; }
  .priority-row { gap: 8px; }
}

@media (max-width: 480px) {
  .page-bg { padding: 1rem 0.75rem; }
  .provider-logo { width: 34px; height: 34px; font-size: 10px; }
}
</style>