import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const RAW_API_BASE = import.meta.env.VITE_API_BASE_URL?.trim()
const RAW_WS_BASE = import.meta.env.VITE_WS_BASE_URL?.trim()
const VERCEL_FALLBACK_API = 'https://oceaagent-production.up.railway.app/api'
// Use absolute URL for non-dev environments to avoid relying on Vercel rewrites
const API = (RAW_API_BASE || (!location.hostname.includes('localhost') && !location.hostname.includes('127.0.0.1') ? VERCEL_FALLBACK_API : '/api')).replace(/\/+$/, '')
const WS_BASE = (RAW_WS_BASE || (API.startsWith('http') ? API.replace(/^http/, 'ws').replace(/\/api$/, '') : '')).replace(/\/+$/, '')

export const useSimulationStore = defineStore('simulation', () => {
  const simulations = ref([])
  const current = ref(null)
  const agents = ref([])
  const interactions = ref([])
  const loading = ref(false)
  const error = ref(null)
  let ws = null

  async function fetchSimulations() {
    loading.value = true
    try {
      const { data } = await axios.get(`${API}/simulations`)
      simulations.value = data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchSimulation(id) {
    loading.value = true
    try {
      const { data } = await axios.get(`${API}/simulations/${id}`)
      current.value = data
      return data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchAgents(simId, tier = null) {
    const params = tier ? { tier } : {}
    const { data } = await axios.get(`${API}/simulations/${simId}/agents`, { params })
    agents.value = data
    return data
  }

  async function fetchInteractions(simId, limit = 50) {
    const { data } = await axios.get(`${API}/simulations/${simId}/interactions`, { params: { limit } })
    interactions.value = data
    return data
  }

  async function createSimulation(payload) {
    loading.value = true
    try {
      const { data } = await axios.post(`${API}/simulations`, payload)
      await fetchSimulations()
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateGraph(simId, graph) {
    await axios.patch(`${API}/simulations/${simId}/graph`, graph)
  }

  async function generateAgents(simId) {
    await axios.post(`${API}/simulations/${simId}/generate-agents`)
  }

  async function startSimulation(simId) {
    await axios.post(`${API}/simulations/${simId}/start`)
    await fetchSimulation(simId)
  }

  async function pauseSimulation(simId) {
    await axios.post(`${API}/simulations/${simId}/pause`)
    await fetchSimulation(simId)
  }

  async function injectEvent(simId, content) {
    await axios.post(`${API}/simulations/${simId}/inject-event`, { content })
  }

  async function generateReport(simId) {
    const { data } = await axios.post(`${API}/simulations/${simId}/report`)
    return data
  }

  function connectWebSocket(simId, onMessage) {
    if (ws) ws.close()
    if (WS_BASE) {
      ws = new WebSocket(`${WS_BASE}/ws/${simId}`)
    } else {
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
      ws = new WebSocket(`${protocol}://${location.host}/ws/${simId}`)
    }

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      onMessage(msg)
    }

    ws.onopen = () => {
      const ping = setInterval(() => {
        if (ws?.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }))
        } else {
          clearInterval(ping)
        }
      }, 30000)
    }
  }

  function disconnectWebSocket() {
    if (ws) { ws.close(); ws = null }
  }

  const runningSimulations = computed(() =>
    simulations.value.filter(s => s.status === 'running')
  )

  return {
    simulations, current, agents, interactions, loading, error,
    fetchSimulations, fetchSimulation, fetchAgents, fetchInteractions,
    createSimulation, updateGraph, generateAgents,
    startSimulation, pauseSimulation, injectEvent, generateReport,
    connectWebSocket, disconnectWebSocket,
    runningSimulations,
  }
})

export const useSettingsStore = defineStore('settings', () => {
  // Store raw provider data per provider name — completely isolated
  const providerData = ref({
    openrouter: { api_key: '', enabled: false, models: {}, base_url: '' },
    groq: { api_key: '', enabled: false, models: {}, base_url: '' },
    together: { api_key: '', enabled: false, models: {}, base_url: '' },
    mistral: { api_key: '', enabled: false, models: {}, base_url: '' },
    custom: { api_key: '', enabled: false, models: {}, base_url: '' },
  })
  const activeProviders = ref([])
  const loading = ref(false)

  // Fetch providers from backend and populate isolated per-provider state
  async function fetchProviders() {
    loading.value = true
    try {
      const { data } = await axios.get(`${API}/settings/providers`)
      // Populate each provider independently — no cross-contamination
      for (const name of Object.keys(providerData.value)) {
        if (data[name]) {
          providerData.value[name] = {
            api_key: data[name].api_key || '',
            enabled: data[name].enabled || false,
            base_url: data[name].base_url || '',
            models: { ...(data[name].models || {}) },
          }
        }
      }
      const { data: active } = await axios.get(`${API}/settings/active-providers`)
      activeProviders.value = active.providers
    } finally {
      loading.value = false
    }
  }

  // Save a single provider — only touches that one provider
  async function saveProvider(name, payload) {
    await axios.patch(`${API}/settings/providers/${name}`, payload)
    // Re-fetch only active providers list after save
    const { data: active } = await axios.get(`${API}/settings/active-providers`)
    activeProviders.value = active.providers
  }

  async function testProvider(name) {
    const { data } = await axios.post(`${API}/settings/providers/${name}/test`)
    return data.valid
  }

  return {
    providerData,
    activeProviders,
    loading,
    fetchProviders,
    saveProvider,
    testProvider,
  }
})