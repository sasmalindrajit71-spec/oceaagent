<template>
  <div class="admin-wrap">

    <!-- LOGIN SCREEN -->
    <div v-if="!authed" class="login-screen">
      <div class="login-box">
        <div class="login-logo">◈ OCEAAGENT ADMIN</div>
        <div class="login-sub">Restricted access — administrators only</div>
        <div class="login-form">
          <div class="field-group">
            <label class="flabel">Username</label>
            <input v-model="loginUser" type="text" class="linp" placeholder="admin" @keydown.enter="doLogin" />
          </div>
          <div class="field-group">
            <label class="flabel">Password</label>
            <input v-model="loginPass" type="password" class="linp" placeholder="••••••••" @keydown.enter="doLogin" />
          </div>
          <div v-if="loginError" class="login-err">{{ loginError }}</div>
          <button class="login-btn" @click="doLogin" :disabled="logging">
            {{ logging ? 'Verifying...' : 'Access Admin Panel →' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ADMIN DASHBOARD -->
    <div v-else class="admin-dash">

      <!-- TOP BAR -->
      <div class="admin-nav">
        <div class="admin-logo">◈ OCEAAGENT ADMIN</div>
        <div class="admin-tabs">
          <button v-for="t in adminTabs" :key="t.id"
            :class="['atab', { 'atab-on': activeTab === t.id }]"
            @click="activeTab = t.id">
            {{ t.label }}
          </button>
        </div>
        <div class="admin-nav-right">
          <span class="live-dot"></span>
          <span class="live-label">{{ overview.active_now || 0 }} live</span>
          <button class="logout-btn" @click="logout">Logout</button>
        </div>
      </div>

      <!-- OVERVIEW TAB -->
      <div v-if="activeTab === 'overview'" class="tab-content">

        <!-- Stat cards -->
        <div class="stat-grid">
          <div class="stat-card" v-for="s in statCards" :key="s.label">
            <div class="sc-val">{{ s.val }}</div>
            <div class="sc-label">{{ s.label }}</div>
            <div class="sc-sub">{{ s.sub }}</div>
          </div>
        </div>

        <!-- Daily chart -->
        <div class="chart-section">
          <div class="section-title">Daily Traffic — Last 30 Days</div>
          <div class="chart-wrap">
            <svg class="line-chart" :viewBox="`0 0 ${chartW} ${chartH}`" preserveAspectRatio="none">
              <!-- Grid lines -->
              <line v-for="i in 5" :key="i"
                x1="0" :y1="(chartH / 5) * i" :x2="chartW" :y2="(chartH / 5) * i"
                stroke="rgba(255,255,255,0.04)" stroke-width="1"/>
              <!-- Views line -->
              <polyline v-if="chartPoints.views.length"
                :points="chartPoints.views.join(' ')"
                fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
              <!-- Visitors line -->
              <polyline v-if="chartPoints.visitors.length"
                :points="chartPoints.visitors.join(' ')"
                fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1"/>
              <!-- Fill area -->
              <polygon v-if="chartPoints.viewsFill"
                :points="chartPoints.viewsFill"
                fill="rgba(255,255,255,0.04)"/>
            </svg>
            <div class="chart-legend">
              <span class="legend-item"><span class="legend-dot bright"></span>Page Views</span>
              <span class="legend-item"><span class="legend-dot dim"></span>Unique Visitors</span>
            </div>
          </div>
        </div>

        <!-- Two column: devices + browsers -->
        <div class="two-col">
          <div class="breakdown-card">
            <div class="section-title">Devices</div>
            <div v-for="(val, key) in stats.devices" :key="key" class="bar-row">
              <span class="bar-label">{{ key }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barPct(val, stats.devices) + '%' }"></div>
              </div>
              <span class="bar-val">{{ val }}</span>
            </div>
          </div>
          <div class="breakdown-card">
            <div class="section-title">Browsers</div>
            <div v-for="(val, key) in stats.browsers" :key="key" class="bar-row">
              <span class="bar-label">{{ key }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barPct(val, stats.browsers) + '%' }"></div>
              </div>
              <span class="bar-val">{{ val }}</span>
            </div>
          </div>
          <div class="breakdown-card">
            <div class="section-title">Operating Systems</div>
            <div v-for="(val, key) in stats.os_stats" :key="key" class="bar-row">
              <span class="bar-label">{{ key }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barPct(val, stats.os_stats) + '%' }"></div>
              </div>
              <span class="bar-val">{{ val }}</span>
            </div>
          </div>
          <div class="breakdown-card">
            <div class="section-title">Top Pages</div>
            <div v-for="page in stats.top_pages" :key="page.path" class="bar-row">
              <span class="bar-label">{{ page.path }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barPctArr(page.views, stats.top_pages, 'views') + '%' }"></div>
              </div>
              <span class="bar-val">{{ page.views }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- LIVE FEED TAB -->
      <div v-if="activeTab === 'live'" class="tab-content">
        <div class="section-title" style="margin-bottom:1rem">
          Recent Visitors
          <span class="refresh-btn" @click="loadStats">↻ Refresh</span>
        </div>
        <div class="activity-table">
          <div class="at-header">
            <span>Time</span><span>Path</span><span>Browser</span><span>OS</span><span>Device</span>
          </div>
          <div v-for="(ev, i) in stats.recent_activity" :key="i" class="at-row">
            <span class="at-time">{{ formatTime(ev.time) }}</span>
            <span class="at-path">{{ ev.path }}</span>
            <span class="at-browser">{{ ev.browser }}</span>
            <span class="at-os">{{ ev.os }}</span>
            <span class="at-device">{{ ev.device }}</span>
          </div>
          <div v-if="!stats.recent_activity?.length" class="at-empty">No visitors recorded yet.</div>
        </div>
      </div>

      <!-- SIMULATIONS TAB -->
      <div v-if="activeTab === 'sims'" class="tab-content">
        <div class="section-title" style="margin-bottom:1rem">All Simulations</div>
        <div class="sim-table">
          <div class="st-header">
            <span>Title</span><span>Status</span><span>Ticks</span><span>Agents</span><span>Report</span><span>Created</span>
          </div>
          <div v-for="sim in simulations" :key="sim.id" class="st-row">
            <span class="st-title">{{ sim.title }}</span>
            <span class="st-status" :class="`sts-${sim.status}`">{{ sim.status }}</span>
            <span>{{ sim.current_tick }}/{{ sim.total_ticks }}</span>
            <span>{{ (sim.deep_agents || 0) + (sim.shallow_agents || 0) }}</span>
            <span>{{ sim.has_report ? '✓' : '—' }}</span>
            <span class="st-date">{{ formatDate(sim.created_at) }}</span>
          </div>
          <div v-if="!simulations.length" class="at-empty">No simulations yet.</div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE } from '../api.js'

const API = `${API_BASE}/admin`

// Auth
const authed    = ref(false)
const loginUser = ref('admin')
const loginPass = ref('')
const loginError= ref('')
const logging   = ref(false)
let authHeader  = ''

const activeTab = ref('overview')
const adminTabs = [
  { id: 'overview', label: '📊 Overview' },
  { id: 'live',     label: '🔴 Live Feed' },
  { id: 'sims',     label: '🧪 Simulations' },
]

const stats       = ref({ devices:{}, browsers:{}, os_stats:{}, top_pages:[], daily:[], recent_activity:[], overview:{} })
const overview    = ref({})
const simulations = ref([])
const chartW = 800
const chartH = 160

async function doLogin() {
  if (!loginPass.value.trim()) return
  logging.value = true
  loginError.value = ''
  const creds = btoa(`${loginUser.value}:${loginPass.value}`)
  authHeader = `Basic ${creds}`
  try {
    const { data } = await axios.get(`${API}/overview`, {
      headers: { Authorization: authHeader }
    })
    overview.value = data
    authed.value = true
    await loadStats()
    await loadSims()
  } catch (e) {
    loginError.value = e.response?.status === 401
      ? 'Invalid username or password'
      : 'Connection failed — is the backend running?'
    authHeader = ''
  } finally { logging.value = false }
}

function logout() {
  authed.value = false
  authHeader = ''
  loginPass.value = ''
}

async function loadStats() {
  try {
    const { data } = await axios.get(`${API}/stats?days=30`, {
      headers: { Authorization: authHeader }
    })
    stats.value = data
    overview.value = data.overview
  } catch (e) { console.error(e) }
}

async function loadSims() {
  try {
    const { data } = await axios.get(`${API}/simulations`, {
      headers: { Authorization: authHeader }
    })
    simulations.value = data
  } catch (e) { console.error(e) }
}

const statCards = computed(() => [
  { val: overview.value.active_now ?? 0,      label: 'Live Right Now',     sub: 'Active in last 5 min' },
  { val: overview.value.today_views ?? 0,     label: 'Views Today',        sub: 'Page loads today' },
  { val: overview.value.total_views ?? 0,     label: 'Total Views',        sub: 'All time' },
  { val: overview.value.recent_unique ?? (stats.value.overview?.recent_unique ?? 0), label: 'Unique Visitors', sub: 'Last 30 days' },
  { val: overview.value.total_sims ?? 0,      label: 'Total Simulations',  sub: `${overview.value.running_sims ?? 0} running` },
  { val: overview.value.total_agents ?? 0,    label: 'Agents Spawned',     sub: 'All time' },
  { val: overview.value.total_interactions ?? 0, label: 'Interactions',    sub: 'All time' },
  { val: overview.value.total_views ?? 0 > 0 ? Math.round((overview.value.total_interactions ?? 0) / (overview.value.total_sims ?? 1)) : 0, label: 'Avg per Sim', sub: 'Interactions/sim' },
])

const chartPoints = computed(() => {
  const daily = stats.value.daily || []
  if (!daily.length) return { views: [], visitors: [], viewsFill: '' }

  const maxViews = Math.max(...daily.map(d => d.views), 1)
  const n = daily.length

  const views = daily.map((d, i) => {
    const x = (i / Math.max(n - 1, 1)) * chartW
    const y = chartH - (d.views / maxViews) * (chartH - 20)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const visitors = daily.map((d, i) => {
    const x = (i / Math.max(n - 1, 1)) * chartW
    const y = chartH - (d.visitors / maxViews) * (chartH - 20)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })

  const fill = [
    ...views,
    `${chartW},${chartH}`, `0,${chartH}`
  ].join(' ')

  return { views, visitors, viewsFill: fill }
})

function barPct(val, obj) {
  const max = Math.max(...Object.values(obj), 1)
  return Math.round((val / max) * 100)
}

function barPctArr(val, arr, key) {
  const max = Math.max(...arr.map(x => x[key]), 1)
  return Math.round((val / max) * 100)
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {})
</script>

<style scoped>
.admin-wrap { min-height: 100vh; background: #000; color: #e8e8e6; font-family: 'Courier New', monospace; }

/* LOGIN */
.login-screen { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #000; }
.login-box { border: 1px solid rgba(255,255,255,0.12); padding: 2.5rem; width: 380px; background: rgba(255,255,255,0.02); }
.login-logo { font-size: 16px; font-weight: 700; letter-spacing: 0.25em; color: #fff; margin-bottom: 6px; }
.login-sub  { font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(255,255,255,0.22); margin-bottom: 2rem; }
.login-form { display: flex; flex-direction: column; gap: 1rem; }
.field-group { display: flex; flex-direction: column; gap: 6px; }
.flabel { font-size: 9px; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(255,255,255,0.3); }
.linp { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 2px; color: #fff; font-family: 'Courier New', monospace; font-size: 12px; padding: 10px 12px; outline: none; }
.linp:focus { border-color: rgba(255,255,255,0.3); }
.login-err { font-size: 10px; color: rgba(255,100,100,0.8); padding: 8px; background: rgba(255,100,100,0.06); border: 1px solid rgba(255,100,100,0.15); }
.login-btn { padding: 12px; background: #fff; color: #000; border: none; font-family: 'Courier New', monospace; font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; font-weight: 700; cursor: pointer; transition: background 0.2s; }
.login-btn:hover { background: rgba(255,255,255,0.88); }
.login-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ADMIN DASH */
.admin-nav { position: sticky; top: 0; z-index: 100; height: 52px; display: flex; align-items: center; gap: 2rem; padding: 0 2rem; background: rgba(0,0,0,0.92); border-bottom: 1px solid rgba(255,255,255,0.07); backdrop-filter: blur(20px); }
.admin-logo { font-size: 12px; font-weight: 700; letter-spacing: 0.22em; color: #fff; flex-shrink: 0; }
.admin-tabs { display: flex; gap: 2px; }
.atab { padding: 5px 14px; background: transparent; color: rgba(255,255,255,0.32); border: 1px solid transparent; border-radius: 2px; font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; transition: all 0.15s; }
.atab:hover { color: rgba(255,255,255,0.6); }
.atab-on { color: #000 !important; background: #fff; border-color: #fff; }
.admin-nav-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; animation: livepulse 1.5s ease-in-out infinite; }
@keyframes livepulse { 0%,100%{box-shadow:0 0 0 0 rgba(74,222,128,0.5)} 50%{box-shadow:0 0 0 5px rgba(74,222,128,0)} }
.live-label { font-size: 10px; color: rgba(255,255,255,0.5); }
.logout-btn { padding: 5px 12px; background: transparent; border: 1px solid rgba(255,255,255,0.12); color: rgba(255,255,255,0.4); font-family: 'Courier New', monospace; font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; cursor: pointer; transition: all 0.15s; }
.logout-btn:hover { border-color: rgba(255,255,255,0.3); color: #fff; }

.tab-content { padding: 2rem; }

/* STAT GRID */
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.06); margin-bottom: 2rem; }
.stat-card { background: #000; padding: 1.4rem; display: flex; flex-direction: column; gap: 4px; }
.sc-val   { font-size: 2rem; font-weight: 700; color: #fff; line-height: 1; }
.sc-label { font-size: 9px; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(255,255,255,0.4); }
.sc-sub   { font-size: 9px; color: rgba(255,255,255,0.18); margin-top: 2px; }

/* CHART */
.chart-section { margin-bottom: 2rem; }
.section-title { font-size: 9px; letter-spacing: 0.22em; text-transform: uppercase; color: rgba(255,255,255,0.3); margin-bottom: 1rem; }
.refresh-btn { margin-left: 12px; cursor: pointer; color: rgba(255,255,255,0.4); transition: color 0.15s; }
.refresh-btn:hover { color: #fff; }
.chart-wrap { border: 1px solid rgba(255,255,255,0.06); background: rgba(255,255,255,0.01); padding: 1rem; }
.line-chart { width: 100%; height: 160px; display: block; }
.chart-legend { display: flex; gap: 1.5rem; margin-top: 8px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 9px; color: rgba(255,255,255,0.3); }
.legend-dot { width: 20px; height: 1px; }
.legend-dot.bright { background: rgba(255,255,255,0.6); }
.legend-dot.dim    { background: rgba(255,255,255,0.25); }

/* BREAKDOWNS */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.06); }
.breakdown-card { background: #000; padding: 1.4rem; }
.bar-row   { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.bar-label { font-size: 10px; color: rgba(255,255,255,0.45); min-width: 70px; flex-shrink: 0; }
.bar-track { flex: 1; height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.bar-fill  { height: 100%; background: rgba(255,255,255,0.5); border-radius: 2px; transition: width 0.6s ease; }
.bar-val   { font-size: 10px; color: rgba(255,255,255,0.35); min-width: 28px; text-align: right; }

/* ACTIVITY TABLE */
.activity-table { border: 1px solid rgba(255,255,255,0.06); overflow: hidden; }
.at-header { display: grid; grid-template-columns: 100px 1fr 100px 100px 80px; gap: 0; padding: 8px 14px; background: rgba(255,255,255,0.04); font-size: 8px; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.25); }
.at-row    { display: grid; grid-template-columns: 100px 1fr 100px 100px 80px; gap: 0; padding: 8px 14px; border-top: 1px solid rgba(255,255,255,0.04); font-size: 10px; transition: background 0.15s; }
.at-row:hover { background: rgba(255,255,255,0.02); }
.at-time   { color: rgba(255,255,255,0.3); }
.at-path   { color: rgba(255,255,255,0.65); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.at-browser,.at-os,.at-device { color: rgba(255,255,255,0.35); }
.at-empty  { padding: 2rem; text-align: center; color: rgba(255,255,255,0.2); font-size: 11px; }

/* SIM TABLE */
.sim-table { border: 1px solid rgba(255,255,255,0.06); overflow: hidden; }
.st-header { display: grid; grid-template-columns: 1fr 90px 80px 80px 60px 140px; padding: 8px 14px; background: rgba(255,255,255,0.04); font-size: 8px; letter-spacing: 0.15em; text-transform: uppercase; color: rgba(255,255,255,0.25); }
.st-row    { display: grid; grid-template-columns: 1fr 90px 80px 80px 60px 140px; padding: 9px 14px; border-top: 1px solid rgba(255,255,255,0.04); font-size: 10px; }
.st-row:hover { background: rgba(255,255,255,0.02); }
.st-title  { color: rgba(255,255,255,0.8); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.st-status { font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; }
.sts-completed { color: rgba(255,255,255,0.6); }
.sts-running   { color: #4ade80; }
.sts-failed    { color: rgba(255,100,100,0.7); }
.st-date   { color: rgba(255,255,255,0.25); font-size: 9px; }
</style>