<template>
  <div class="page-bg">
    <div class="layout">

      <div class="left-col">
        <div class="stepper">
          <div v-for="(s,i) in steps" :key="i" class="step" :class="{on: activeStep===i}" @click="activeStep=i">
            <span class="sn">{{ String(i+1).padStart(2,'0') }}</span>{{ s }}
          </div>
        </div>

        <label class="flabel">Simulation Title</label>
        <input class="finp" type="text" v-model="form.title" placeholder="e.g. India Election Sentiment 2026" />

        <label class="flabel">Event Context</label>
        <textarea class="ftxa" v-model="form.seed_text" placeholder="Paste article text, URL, or describe the event in detail..."></textarea>

        <label class="flabel">Deep Agents (LLM-powered)</label>
        <select class="fsel" v-model="form.deep_agent_count">
          <option value="5">5 agents — Quick test</option>
          <option value="10">10 agents — Micro</option>
          <option value="20">20 agents — Standard</option>
          <option value="50">50 agents — Dense</option>
        </select>

        <label class="flabel">Shallow Agents (statistical)</label>
        <select class="fsel" v-model="form.shallow_agent_count">
          <option value="50">50 agents</option>
          <option value="100">100 agents</option>
          <option value="200">200 agents</option>
          <option value="500">500 agents</option>
        </select>

        <label class="flabel">Total Ticks</label>
        <select class="fsel" v-model="form.total_ticks">
          <option value="10">10 ticks — Fast</option>
          <option value="20">20 ticks — Standard</option>
          <option value="30">30 ticks — Full</option>
          <option value="50">50 ticks — Deep</option>
        </select>

        <div v-if="error" class="err-box">{{ error }}</div>

        <button class="btn-launch" :disabled="submitting || !form.title.trim() || !form.seed_text.trim()" @click="handleSubmit">
          <span v-if="submitting" class="pulse">Extracting knowledge graph...</span>
          <span v-else>Launch Simulation →</span>
        </button>
      </div>

      <div class="right-col">
        <div class="rlabel">Preview</div>
        <div class="preview-box">
          <div class="prev-title">{{ form.title || '— Awaiting input —' }}</div>
          <div class="bub-grid">
            <div v-for="(init,i) in previewList" :key="i" class="bub" :style="{animationDelay: i*0.035+'s'}">{{ init }}</div>
            <div v-if="overflow > 0" class="bub overflow">+{{ overflow }}</div>
          </div>
          <div class="meta-list">
            <div class="meta-row"><span>Deep agents</span><span class="mv">{{ form.deep_agent_count }}</span></div>
            <div class="meta-row"><span>Shallow agents</span><span class="mv">{{ form.shallow_agent_count }}</span></div>
            <div class="meta-row"><span>Ticks</span><span class="mv">{{ form.total_ticks }}</span></div>
            <div class="meta-row"><span>Network</span><span class="mv">Watts-Strogatz</span></div>
            <div class="meta-row"><span>Memory decay</span><span class="mv">Exponential</span></div>
            <div class="meta-row"><span>Report engine</span><span class="mv">3-pass synthesis</span></div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSimulationStore } from '../stores'

const router = useRouter()
const store = useSimulationStore()

const activeStep = ref(0)
const steps = ['Ingest','Validate','Generate','Run']
const submitting = ref(false)
const error = ref('')

const INITS = ['PK','SR','ZA','DM','AO','LF','KS','RP','NB','TV','JC','MW','HG','IL','YD','BS','CQ','FE']

const form = reactive({
  title: '',
  seed_text: '',
  deep_agent_count: '20',
  shallow_agent_count: '200',
  total_ticks: '30',
})

const previewList = computed(() => INITS.slice(0, Math.min(parseInt(form.deep_agent_count), 18)))
const overflow    = computed(() => Math.max(0, parseInt(form.deep_agent_count) - 18))

async function handleSubmit() {
  if (!form.title.trim() || !form.seed_text.trim()) return
  submitting.value = true
  error.value = ''
  try {
    const result = await store.createSimulation({
      title: form.title,
      seed_text: form.seed_text,
      deep_agent_count: parseInt(form.deep_agent_count),
      shallow_agent_count: parseInt(form.shallow_agent_count),
      total_ticks: parseInt(form.total_ticks),
    })
    router.push(`/simulation/${result.id}`)
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to create simulation'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-bg { min-height: calc(100vh - 54px); background: rgba(0,0,0,0.82); }
.layout { display: grid; grid-template-columns: 1fr 1fr; min-height: calc(100vh - 54px); }
.left-col { padding: 3rem; border-right: 1px solid rgba(255,255,255,0.07); display: flex; flex-direction: column; gap: 0; }
.stepper { display: flex; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 2rem; }
.step { flex: 1; padding: 9px 4px; text-align: center; font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(255,255,255,0.22); border-right: 1px solid rgba(255,255,255,0.08); cursor: pointer; transition: all 0.2s; }
.step:last-child { border-right: none; }
.step.on { color: #000; background: #fff; }
.sn { font-size: 14px; font-weight: 900; display: block; margin-bottom: 1px; }
.flabel { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: rgba(255,255,255,0.25); margin-bottom: 7px; margin-top: 1rem; display: block; }
.finp, .ftxa, .fsel { width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 2px; color: #fff; font-family: 'Courier New', monospace; font-size: 12px; padding: 10px 14px; outline: none; transition: border-color 0.2s; margin-bottom: 0; }
.finp:focus, .ftxa:focus, .fsel:focus { border-color: rgba(255,255,255,0.32); }
.ftxa { min-height: 100px; resize: vertical; }
.fsel { appearance: none; cursor: pointer; }
.fsel option { background: #111; }
.err-box { margin-top: 1rem; padding: 10px 14px; border: 1px solid rgba(255,100,100,0.3); background: rgba(255,100,100,0.05); border-radius: 2px; font-family: 'Courier New', monospace; font-size: 11px; color: rgba(255,150,150,0.8); }
.btn-launch { margin-top: auto; padding: 13px; width: 100%; background: #fff; color: #000; border: none; border-radius: 2px; font-family: 'Courier New', monospace; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 700; cursor: pointer; transition: background 0.2s; margin-top: 1.5rem; }
.btn-launch:hover:not(:disabled) { background: rgba(255,255,255,0.86); }
.btn-launch:disabled { opacity: 0.4; cursor: not-allowed; }
.right-col { padding: 3rem; background: rgba(255,255,255,0.01); display: flex; flex-direction: column; }
.rlabel { font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.25em; text-transform: uppercase; color: rgba(255,255,255,0.22); margin-bottom: 1.4rem; }
.preview-box { border: 1px solid rgba(255,255,255,0.08); border-radius: 2px; padding: 1.4rem; background: rgba(255,255,255,0.02); flex: 1; display: flex; flex-direction: column; gap: 1rem; }
.prev-title { font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; color: rgba(255,255,255,0.22); padding-bottom: 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.06); min-height: 2.2rem; }
.bub-grid { display: grid; grid-template-columns: repeat(6,1fr); gap: 5px; }
.bub { aspect-ratio: 1; border-radius: 50%; border: 1px solid rgba(255,255,255,0.15); display: flex; align-items: center; justify-content: center; font-family: 'Courier New', monospace; font-size: 8px; font-weight: 700; color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.03); animation: bi .3s both; transition: all 0.2s; cursor: default; }
.bub:hover { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.4); transform: scale(1.1); }
.bub.overflow { color: rgba(255,255,255,0.3); font-size: 9px; }
@keyframes bi { from{opacity:0;transform:scale(.3)} to{opacity:1;transform:scale(1)} }
.meta-list { margin-top: auto; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 1rem; display: flex; flex-direction: column; gap: 5px; }
.meta-row { display: flex; justify-content: space-between; font-family: 'Courier New', monospace; font-size: 10px; color: rgba(255,255,255,0.22); }
.mv { color: rgba(255,255,255,0.52); }
.pulse { animation: pl 1s ease-in-out infinite; }
@keyframes pl { 0%,100%{opacity:1}50%{opacity:.4} }
</style>