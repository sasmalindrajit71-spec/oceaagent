<template>
  <div class="dashboard">

    <!-- HERO -->
    <section class="hero">
      <div class="hero-eyebrow">
        <span class="eyebrow-line"></span>
        <span class="eyebrow-text">Open-Source · Multi-Agent · Phase 1</span>
      </div>

      <h1 class="hero-headline">
        Simulate the world<br>
        <em>before it happens.</em>
      </h1>

      <p class="hero-sub">Feed any event into OCEAN. Watch psychologically-grounded AI agents interact, debate, and reshape their beliefs across a living social network.</p>

      <div class="hero-cta">
        <router-link to="/new" class="cta-primary">
          <span class="cta-text">New Simulation</span>
          <span class="cta-arrow">↗</span>
        </router-link>
        <div class="hero-metrics">
          <div class="metric">
            <span class="metric-n">{{ totalSimulations }}</span>
            <span class="metric-l">Simulations</span>
          </div>
          <div class="metric-sep"></div>
          <div class="metric">
            <span class="metric-n">{{ totalAgents.toLocaleString() }}</span>
            <span class="metric-l">Agents run</span>
          </div>
          <div class="metric-sep"></div>
          <div class="metric">
            <span class="metric-n">{{ totalTicks.toLocaleString() }}</span>
            <span class="metric-l">Ticks total</span>
          </div>
        </div>
      </div>
    </section>

    <!-- DIVIDER -->
    <div class="section-divider">
      <span class="divider-label">Library</span>
      <span class="divider-count">{{ simulations.length }}</span>
    </div>

    <!-- LOADING -->
    <div v-if="loading" class="skeleton-grid">
      <div v-for="i in 3" :key="i" class="skeleton"></div>
    </div>

    <!-- EMPTY -->
    <div v-else-if="simulations.length === 0" class="empty">
      <div class="empty-mark">
        <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
          <circle cx="24" cy="24" r="23" stroke="white" stroke-width="0.5" opacity="0.2"/>
          <circle cx="24" cy="24" r="10" stroke="white" stroke-width="0.5" opacity="0.4"/>
          <line x1="24" y1="1" x2="24" y2="47" stroke="white" stroke-width="0.3" opacity="0.15"/>
          <line x1="1" y1="24" x2="47" y2="24" stroke="white" stroke-width="0.3" opacity="0.15"/>
        </svg>
      </div>
      <p class="empty-title">No simulations yet</p>
      <p class="empty-sub">Create your first simulation and watch AI agents evolve.</p>
      <router-link to="/new" class="cta-primary" style="margin-top:28px">
        <span class="cta-text">Launch simulation</span>
        <span class="cta-arrow">↗</span>
      </router-link>

      <!-- Features -->
      <div class="features">
        <div class="feature" v-for="f in FEATURES" :key="f.title">
          <div class="feature-num">{{ f.num }}</div>
          <div class="feature-body">
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- SIMULATION GRID -->
    <div v-else class="sim-section">
      <!-- Filter -->
      <div class="filter-bar">
        <button
          v-for="f in FILTERS"
          :key="f.id"
          :class="['filter-btn', { 'filter-active': activeFilter === f.id }]"
          @click="activeFilter = f.id"
        >{{ f.label }}</button>
      </div>

      <div class="sim-grid">
        <router-link
          v-for="(sim, idx) in filteredSims"
          :key="sim.id"
          :to="`/simulation/${sim.id}`"
          class="sim-card"
          :style="{ animationDelay: `${idx * 40}ms` }"
        >
          <!-- Card inner -->
          <div class="card-inner">
            <div class="card-top">
              <span class="card-status" :class="`cs-${sim.status}`">
                <span class="cs-pip"></span>
                {{ sim.status }}
              </span>
              <span class="card-date">{{ formatDate(sim.created_at) }}</span>
            </div>

            <h3 class="card-title">{{ sim.title }}</h3>

            <!-- Agent split bar -->
            <div class="agent-split">
              <div class="split-bar">
                <div
                  class="split-deep"
                  :style="{ width: `${(sim.deep_agent_count / Math.max(sim.deep_agent_count + sim.shallow_agent_count, 1)) * 100}%` }"
                ></div>
              </div>
              <div class="split-labels">
                <span class="split-d">{{ sim.deep_agent_count }} deep</span>
                <span class="split-s">{{ sim.shallow_agent_count }} shallow</span>
              </div>
            </div>

            <!-- Progress -->
            <div class="card-progress">
              <div class="progress-track">
                <div
                  class="progress-bar"
                  :style="{ width: `${Math.min((sim.current_tick / Math.max(sim.total_ticks, 1)) * 100, 100)}%` }"
                  :class="{ 'pb-running': sim.status === 'running', 'pb-done': sim.status === 'completed' }"
                ></div>
                <div class="progress-marker" v-for="m in [25,50,75]" :key="m" :style="{ left: m + '%' }"></div>
              </div>
              <div class="progress-labels">
                <span class="progress-pct">{{ Math.round((sim.current_tick / Math.max(sim.total_ticks, 1)) * 100) }}%</span>
                <span class="progress-ticks">{{ sim.current_tick }} / {{ sim.total_ticks }}</span>
              </div>
            </div>

            <!-- Footer -->
            <div class="card-footer">
              <span class="card-report" v-if="sim.has_report">Report ready</span>
              <span class="card-failed" v-else-if="sim.status === 'failed'">Failed</span>
              <span class="card-status-text" v-else>{{ sim.status }}</span>
              <span class="card-arr">→</span>
            </div>
          </div>

          <!-- Hover reveal line -->
          <div class="card-reveal-line"></div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed, ref } from 'vue'
import { useSimulationStore } from '../stores'

const store = useSimulationStore()
const simulations = computed(() => store.simulations)
const loading = computed(() => store.loading)
const activeFilter = ref('all')

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'running', label: 'Running' },
  { id: 'completed', label: 'Completed' },
  { id: 'failed', label: 'Failed' },
]

const FEATURES = [
  { num: '01', title: 'Graph RAG extraction', desc: 'Multi-pass knowledge graph built from any text, URL, or PDF — validated before agents spawn.' },
  { num: '02', title: 'Tiered agent architecture', desc: 'Deep agents with memory decay and emotional salience. Shallow agents for crowd dynamics.' },
  { num: '03', title: 'Live intervention', desc: 'Pause. Inject events. Watch the cascade. Compare diverging timelines from the same seed.' },
  { num: '04', title: 'Intelligence reports', desc: 'Three-pass analysis: pattern detection → causal attribution → plain-English briefing.' },
]

const filteredSims = computed(() => {
  if (activeFilter.value === 'all') return simulations.value
  return simulations.value.filter(s => s.status === activeFilter.value)
})

const totalSimulations = computed(() => simulations.value.length)
const totalAgents = computed(() => simulations.value.reduce((s, sim) => s + (sim.deep_agent_count || 0) + (sim.shallow_agent_count || 0), 0))
const totalTicks = computed(() => simulations.value.reduce((s, sim) => s + (sim.current_tick || 0), 0))

onMounted(() => store.fetchSimulations())

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso), now = new Date(), diff = now - d
  if (diff < 60000) return 'just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.dashboard { padding: 0; min-height: 100vh; }

/* ── HERO ── */
.hero {
  padding: 72px 56px 64px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  position: relative;
}

.hero-eyebrow {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.eyebrow-line {
  display: block;
  width: 32px;
  height: 1px;
  background: rgba(255,255,255,0.3);
}

.eyebrow-text {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--ink-300);
}

.hero-headline {
  font-family: var(--font-display);
  font-size: clamp(42px, 6vw, 72px);
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: var(--white);
  margin-bottom: 24px;
}

.hero-headline em {
  font-style: italic;
  color: rgba(255,255,255,0.55);
}

.hero-sub {
  font-size: 15px;
  line-height: 1.75;
  color: var(--ink-300);
  max-width: 480px;
  margin-bottom: 48px;
  font-weight: 300;
}

.hero-cta {
  display: flex;
  align-items: center;
  gap: 48px;
  flex-wrap: wrap;
}

/* CTA button */
.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 28px;
  background: var(--white);
  color: var(--black);
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.cta-primary::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 50%);
}

.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(255,255,255,0.12);
}

.cta-text {}
.cta-arrow { font-size: 14px; }

/* Hero metrics */
.hero-metrics {
  display: flex;
  align-items: center;
  gap: 24px;
}

.metric { display: flex; flex-direction: column; gap: 3px; }
.metric-n { font-family: var(--font-display); font-size: 24px; color: var(--white); }
.metric-l { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-400); }
.metric-sep { width: 1px; height: 32px; background: rgba(255,255,255,0.08); }

/* ── DIVIDER ── */
.section-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 56px;
  height: 48px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.divider-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--ink-400);
}

.divider-count {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--ink-600);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 2px;
  padding: 1px 7px;
}

/* ── EMPTY ── */
.empty {
  padding: 80px 56px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.empty-mark { margin-bottom: 28px; }
.empty-title { font-family: var(--font-display); font-size: 28px; color: var(--white); margin-bottom: 10px; }
.empty-sub { font-size: 14px; color: var(--ink-300); font-weight: 300; }

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  margin-top: 64px;
  width: 100%;
  max-width: 680px;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.feature {
  display: flex;
  gap: 20px;
  padding: 28px;
  background: rgba(255,255,255,0.015);
  border-right: 1px solid rgba(255,255,255,0.04);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.feature:nth-child(even) { border-right: none; }
.feature:nth-last-child(-n+2) { border-bottom: none; }

.feature-num {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--ink-500);
  letter-spacing: 0.1em;
  flex-shrink: 0;
  margin-top: 2px;
}

.feature-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--white);
  margin-bottom: 6px;
  font-family: var(--font-body);
}

.feature-desc {
  font-size: 12px;
  color: var(--ink-300);
  line-height: 1.6;
  font-weight: 300;
}

/* ── SIMULATION GRID ── */
.sim-section { padding: 32px 56px 56px; }

.filter-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 28px;
}

.filter-btn {
  padding: 6px 16px;
  background: transparent;
  color: var(--ink-400);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 2px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  transition: all 0.15s ease;
}

.filter-btn:hover { color: var(--ink-100); border-color: rgba(255,255,255,0.12); }
.filter-active { color: var(--white) !important; border-color: rgba(255,255,255,0.3) !important; background: rgba(255,255,255,0.04) !important; }

.sim-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1px;
  background: rgba(255,255,255,0.04);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.sim-card {
  display: block;
  background: var(--black);
  text-decoration: none;
  color: var(--text);
  position: relative;
  overflow: hidden;
  animation: fadeUp 0.4s ease both;
  transition: background 0.2s ease;
}

.sim-card:hover { background: rgba(255,255,255,0.02); }
.sim-card:hover .card-arr { transform: translate(3px, -3px); }
.sim-card:hover .card-reveal-line { transform: scaleX(1); }
.sim-card:hover .card-title { color: var(--white); }

.card-reveal-line {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: rgba(255,255,255,0.15);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.card-inner { padding: 28px; display: flex; flex-direction: column; gap: 18px; }

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--ink-300);
}

.cs-pip {
  width: 5px; height: 5px;
  border-radius: 50%;
  background: currentColor;
}

.cs-running { color: var(--white); }
.cs-running .cs-pip { animation: pip-pulse 1.5s ease-in-out infinite; }
@keyframes pip-pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(255,255,255,0.4); }
  50% { box-shadow: 0 0 0 4px rgba(255,255,255,0); }
}
.cs-completed { color: var(--ink-200); }
.cs-failed { color: var(--ink-500); }

.card-date { font-family: var(--font-mono); font-size: 10px; color: var(--ink-500); }

.card-title {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 400;
  line-height: 1.25;
  color: rgba(255,255,255,0.8);
  letter-spacing: -0.01em;
  transition: color 0.2s ease;
}

/* Agent split */
.agent-split { display: flex; flex-direction: column; gap: 8px; }
.split-bar { height: 2px; background: rgba(255,255,255,0.06); border-radius: 1px; overflow: hidden; }
.split-deep { height: 100%; background: rgba(255,255,255,0.5); transition: width 0.5s ease; }
.split-labels { display: flex; justify-content: space-between; }
.split-d { font-family: var(--font-mono); font-size: 10px; color: var(--ink-200); letter-spacing: 0.06em; }
.split-s { font-family: var(--font-mono); font-size: 10px; color: var(--ink-500); letter-spacing: 0.06em; }

/* Progress */
.card-progress { display: flex; flex-direction: column; gap: 8px; }
.progress-track { height: 1px; background: rgba(255,255,255,0.06); position: relative; }
.progress-bar { position: absolute; left: 0; top: 0; bottom: 0; background: rgba(255,255,255,0.4); transition: width 0.8s ease; }
.pb-running { background: var(--white); animation: pulse-white 2s ease-in-out infinite; }
.pb-done { background: rgba(255,255,255,0.6); }
.progress-marker { position: absolute; top: -3px; width: 1px; height: 7px; background: rgba(255,255,255,0.06); }
.progress-labels { display: flex; justify-content: space-between; }
.progress-pct { font-family: var(--font-mono); font-size: 11px; color: var(--white); font-weight: 500; }
.progress-ticks { font-family: var(--font-mono); font-size: 10px; color: var(--ink-500); }

/* Card footer */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.04);
}

.card-report { font-family: var(--font-mono); font-size: 10px; color: var(--ink-200); letter-spacing: 0.08em; text-transform: uppercase; }
.card-failed { font-family: var(--font-mono); font-size: 10px; color: var(--ink-500); letter-spacing: 0.08em; text-transform: uppercase; }
.card-status-text { font-family: var(--font-mono); font-size: 10px; color: var(--ink-500); letter-spacing: 0.08em; text-transform: uppercase; }
.card-arr { font-size: 14px; color: var(--ink-400); transition: transform 0.2s ease; }

/* Skeleton */
.skeleton-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; padding: 32px 56px; background: rgba(255,255,255,0.04); margin: 32px 56px; border-radius: var(--radius-lg); overflow: hidden; }
.skeleton { height: 240px; background: rgba(255,255,255,0.015); animation: pulse-white 1.5s ease-in-out infinite; }
</style>