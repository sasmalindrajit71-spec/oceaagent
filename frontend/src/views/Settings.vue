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
            <button v-if="nvidiaEdit" class="btn-xs" style="margin-top:6px" @click="nvidiaEdit=false">Cancel</button>
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
              💡 Use <strong>Nemotron 3 Super 120B</strong> or <strong>DeepSeek R1</strong> for deep agents and reports.
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
            <button v-if="groqEdit" class="btn-xs" style="margin-top:6px" @click="groqEdit=false">Cancel</button>
          </div>
          <div v-if="gqMsg" :class="gqMsg.startsWith('✓') ? 'msg-ok' : 'msg-err'">{{ gqMsg }}</div>
        </div>
      </div>

      <!-- ══ OPENROUTER ══ -->
      <div class="grp" :class="{ 'grp-active': orActive }">
        <div class="grp-hdr">
          <div class="grp-hdr-left">
            <div class="provider-logo">OR</div>
            <div>
              <div class="grp-t">OpenRouter <span class="fallback-pill">FALLBACK</span></div>
              <div class="grp-s">deepseek/deepseek-chat-v3-0324:free · Free tier</div>
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
            <button v-if="orEdit" class="btn-xs" style="margin-top:6px" @click="orEdit=false">Cancel</button>
          </div>
          <div v-if="orMsg" :class="orMsg.startsWith('✓') ? 'msg-ok' : 'msg-err'">{{ orMsg }}</div>
        </div>
      </div>

      <!-- ══ PROVIDER PRIORITY ══ -->
      <div class="grp">
        <div class="grp-hdr">
          <span class="grp-t">Provider Priority</span>
          <span class="grp-s">Auto-failover order</span>
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

const API = '/api'
const GROQ_MODEL = 'llama-3.3-70b-versatile'
const OR_MODEL   = 'deepseek/deepseek-chat-v3-0324:free'

// ── NVIDIA state ──────────────────────────────────────────────────────────────
const nvidiaKey     = ref('')
const nvidiaSavedKey = ref('')
const nvidiaEdit    = ref(false)
const nvidiaActive  = ref(false)
const showNV        = ref(false)
const savingNV      = ref(false)
const nvMsg         = ref('')
const nvidiaModels  = reactive({
  deep_agent:    'meta/llama-3.3-70b-instruct',
  shallow_agent: 'meta/llama-3.1-8b-instruct',
  evaluator:     'nvidia/llama-3.3-nemotron-super-49b-v1',
  graph_rag:     'meta/llama-3.3-70b-instruct',
  report_engine: 'nvidia/nemotron-3-super-120b-a12b',
})

// All NVIDIA models for dropdown
const allNvidiaModels = ref([])
const modelInfo = ref({})

// ── Groq state ────────────────────────────────────────────────────────────────
const groqKey     = ref('')
const groqSavedKey = ref('')
const groqEdit    = ref(false)
const groqActive  = ref(false)
const showGQ      = ref(false)
const savingGQ    = ref(false)
const gqMsg       = ref('')

// ── OpenRouter state ──────────────────────────────────────────────────────────
const orKey     = ref('')
const orSavedKey = ref('')
const orEdit    = ref(false)
const orActive  = ref(false)
const showOR    = ref(false)
const savingOR  = ref(false)
const orMsg     = ref('')

// ── Role definitions ───────────────────────────────────────────────────────────
const roles = [
  { key: 'deep_agent',    label: 'Deep Agent',    desc: 'LLM-powered agent reasoning and dialogue' },
  { key: 'shallow_agent', label: 'Shallow Agent',  desc: 'Statistical agent — use fast/small model' },
  { key: 'evaluator',     label: 'Evaluator',     desc: 'Assesses belief shifts and emotion changes' },
  { key: 'graph_rag',     label: 'Graph RAG',     desc: 'Extracts knowledge graph from seed text' },
  { key: 'report_engine', label: 'Report Engine', desc: 'Generates final intelligence briefing' },
]

const simRows = ref([
  { key: 'ticks',   label: 'Default tick count',  desc: 'ticks per simulation run',  val: '30'   },
  { key: 'decay',   label: 'Memory decay rate',   desc: 'exponential coefficient',   val: '0.05' },
  { key: 'agents',  label: 'Default agent count', desc: 'deep agents per simulation', val: '20'  },
])

// Group models by tier for dropdown
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
      if (prov.nvidia.models) {
        Object.assign(nvidiaModels, prov.nvidia.models)
      }
    }
    nvidiaActive.value = activeList.includes('nvidia')

    // Groq
    if (prov.groq?.api_key && prov.groq.api_key !== '****' && prov.groq.enabled) {
      groqSavedKey.value = prov.groq.api_key
    }
    groqActive.value = activeList.includes('groq')

    // OpenRouter
    if (prov.openrouter?.api_key && prov.openrouter.api_key !== '****' && prov.openrouter.enabled) {
      orSavedKey.value = prov.openrouter.api_key
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
    nvidiaKey.value = ''
    nvidiaEdit.value = false
    nvMsg.value = '✓ NVIDIA NIM key saved — now your primary provider'
    setTimeout(() => nvMsg.value = '', 5000)
  } catch (e) {
    nvMsg.value = '✗ ' + (e.response?.data?.detail || e.message)
  } finally { savingNV.value = false }
}

async function saveNvidiaModels() {
  if (!nvidiaSavedKey.value && !nvidiaKey.value) return
  try {
    await axios.patch(`${API}/settings/providers/nvidia`, {
      models: { ...nvidiaModels },
    })
  } catch (e) { console.error('Failed to save model assignments:', e) }
}

async function saveGroq() {
  const key = groqKey.value.trim()
  if (!key) return
  savingGQ.value = true; gqMsg.value = ''
  try {
    await axios.patch(`${API}/settings/providers/groq`, {
      api_key: key, enabled: true,
      models: {
        deep_agent: GROQ_MODEL, shallow_agent: GROQ_MODEL,
        evaluator: GROQ_MODEL, graph_rag: GROQ_MODEL, report_engine: GROQ_MODEL,
      },
    })
    await loadProviderState()
    groqKey.value = ''; groqEdit.value = false
    gqMsg.value = '✓ Groq key saved'
    setTimeout(() => gqMsg.value = '', 4000)
  } catch (e) {
    gqMsg.value = '✗ ' + (e.response?.data?.detail || e.message)
  } finally { savingGQ.value = false }
}

async function saveOR() {
  const key = orKey.value.trim()
  if (!key) return
  savingOR.value = true; orMsg.value = ''
  try {
    await axios.patch(`${API}/settings/providers/openrouter`, {
      api_key: key, enabled: true,
      models: {
        deep_agent: OR_MODEL, shallow_agent: OR_MODEL,
        evaluator: OR_MODEL, graph_rag: OR_MODEL, report_engine: OR_MODEL,
      },
    })
    await loadProviderState()
    orKey.value = ''; orEdit.value = false
    orMsg.value = '✓ OpenRouter key saved'
    setTimeout(() => orMsg.value = '', 4000)
  } catch (e) {
    orMsg.value = '✗ ' + (e.response?.data?.detail || e.message)
  } finally { savingOR.value = false }
}
</script>

<style scoped>
.page-bg { min-height: calc(100vh - 54px); background: rgba(0,0,0,0.82); padding: 3rem 2rem; overflow-y: auto; }
.inner { max-width: 700px; margin: 0 auto; }
.eyebrow { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.28em; text-transform: uppercase; color: rgba(255,255,255,0.18); margin-bottom: 2.2rem; }

.grp { border: 1px solid rgba(255,255,255,0.08); margin-bottom: 2px; transition: border-color 0.2s; }
.grp-active { border-color: rgba(255,255,255,0.2); }
.nvidia-grp.grp-active { border-color: rgba(118,185,0,0.3); }

.grp-hdr { padding: 1rem 1.4rem; display: flex; align-items: center; justify-content: space-between; }
.grp-hdr-left { display: flex; align-items: center; gap: 14px; }
.provider-logo { width: 38px; height: 38px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.12); display: flex; align-items: center; justify-content: center; font-family: 'Courier New', monospace; font-size: 11px; font-weight: 700; color: #fff; flex-shrink: 0; }
.nvidia-logo { background: rgba(118,185,0,0.1); border-color: rgba(118,185,0,0.3); color: #76b900; }

.grp-t { font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.55); }
.grp-s { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.2); margin-top: 2px; }

.recommended-pill { font-size: 8px; padding: 2px 6px; background: rgba(118,185,0,0.15); color: #76b900; border: 1px solid rgba(118,185,0,0.3); border-radius: 1px; margin-left: 8px; letter-spacing: 0.1em; }
.fallback-pill { font-size: 8px; padding: 2px 6px; background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.35); border: 1px solid rgba(255,255,255,0.1); border-radius: 1px; margin-left: 8px; letter-spacing: 0.1em; }

.status-badge { font-family: 'Courier New', monospace; font-size: 9px; padding: 3px 10px; border-radius: 1px; border: 1px solid; }
.badge-on  { color: rgba(255,255,255,0.8); border-color: rgba(255,255,255,0.2); background: rgba(255,255,255,0.06); }
.badge-off { color: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.06); background: transparent; }

.grp-body { padding: 1.4rem; border-top: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: 12px; }

/* Saved key */
.saved-key-box { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 2px; padding: 12px; display: flex; flex-direction: column; gap: 6px; }
.saved-key-label { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.25); }
.saved-key-row { display: flex; align-items: center; gap: 10px; }
.saved-key-val { font-family: 'Courier New', monospace; font-size: 12px; color: rgba(255,255,255,0.8); background: rgba(255,255,255,0.05); padding: 3px 8px; border-radius: 2px; }
.saved-ok { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(118,185,0,0.8); }

/* Key input */
.flabel { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.25); margin-bottom: 6px; display: block; }
.key-row { display: flex; gap: 6px; align-items: center; }
.sinp { flex: 1; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.09); border-radius: 2px; color: #fff; font-family: 'Courier New', monospace; font-size: 11px; padding: 8px 12px; outline: none; transition: border-color 0.2s; }
.sinp:focus { border-color: rgba(255,255,255,0.28); }
.sinp.sm { flex: 0 0 62px; text-align: center; }
.field-hint { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.2); }
.field-hint a { color: rgba(255,255,255,0.5); }

/* Buttons */
.btn-xs { padding: 7px 12px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 2px; color: rgba(255,255,255,0.6); font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; white-space: nowrap; transition: all 0.2s; }
.btn-xs:hover { border-color: rgba(255,255,255,0.3); color: #fff; }
.btn-xs.primary { background: #fff; color: #000; border-color: #fff; }
.btn-xs.primary:hover { background: rgba(255,255,255,0.88); }
.btn-xs:disabled { opacity: 0.35; cursor: not-allowed; }

/* Messages */
.msg-ok  { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(118,185,0,0.85); letter-spacing: 0.06em; }
.msg-err { font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,100,100,0.85); letter-spacing: 0.06em; }

/* Model assignment */
.model-assignment { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 2px; padding: 14px; }
.ma-title { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.25); margin-bottom: 12px; }
.ma-grid { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.ma-row { display: grid; grid-template-columns: 1fr auto; gap: 12px; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.ma-row:last-child { border-bottom: none; }
.ma-role-name { font-size: 12px; font-weight: 700; color: #fff; }
.ma-role-desc { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.2); margin-top: 2px; }
.fsel-sm { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 2px; color: #fff; font-family: 'Courier New', monospace; font-size: 10px; padding: 6px 10px; outline: none; min-width: 220px; appearance: none; cursor: pointer; }
.fsel-sm option { background: #111; }
.fsel-sm optgroup { background: #000; color: rgba(255,255,255,0.4); font-size: 9px; }
.ma-tip { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.25); line-height: 1.6; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; }
.ma-tip strong { color: rgba(255,255,255,0.5); font-weight: 400; }

/* Priority */
.priority-list {}
.priority-row { display: flex; align-items: center; gap: 14px; padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.priority-row:last-of-type { border-bottom: none; }
.p-num { font-family: 'Courier New', monospace; font-size: 13px; font-weight: 900; color: rgba(255,255,255,0.15); width: 20px; flex-shrink: 0; }
.p-active .p-num { color: rgba(255,255,255,0.7); }
.p-name { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.4); flex: 1; }
.p-active .p-name { color: #fff; }
.p-status { font-family: 'Courier New', monospace; font-size: 9px; }
.p-on  { color: rgba(118,185,0,0.8); }
.p-off { color: rgba(255,255,255,0.2); }
.priority-note { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.15); line-height: 1.7; margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.04); padding-top: 10px; }

/* Sim defaults */
.srow { display: flex; align-items: center; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }
.srow:last-child { border-bottom: none; padding-bottom: 0; }
.sname { font-size: 12px; font-weight: 700; color: #fff; }
.sdesc { font-family: 'Courier New', monospace; font-size: 9px; color: rgba(255,255,255,0.2); margin-top: 1px; }
</style>