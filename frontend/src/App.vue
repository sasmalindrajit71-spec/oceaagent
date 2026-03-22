<template>
  <div class="app-shell">
    <div class="cursor-dot" ref="cursorDot"></div>
    <div class="cursor-ring" ref="cursorRing"></div>

    <!-- 3D Ocean background fills entire app -->
    <div class="ambient-bg">
      <OceanScene />
    </div>

    <aside class="sidebar">
      <div class="sidebar-logo">
        <div class="logo-mark">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <circle cx="14" cy="14" r="13" stroke="white" stroke-width="0.75" opacity="0.6"/>
            <circle cx="14" cy="14" r="6" stroke="white" stroke-width="0.75" opacity="0.9"/>
            <line x1="14" y1="1" x2="14" y2="27" stroke="white" stroke-width="0.5" opacity="0.3"/>
            <line x1="1" y1="14" x2="27" y2="14" stroke="white" stroke-width="0.5" opacity="0.3"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-name">OCEAAGENT</span>
          <span class="logo-ver">v1.0</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" active-class="nav-active" exact>
          <span class="nav-label">Dashboard</span>
        </router-link>
        <router-link to="/new" class="nav-item" active-class="nav-active">
          <span class="nav-label">New Simulation</span>
        </router-link>
        <router-link to="/settings" class="nav-item" active-class="nav-active">
          <span class="nav-label">Settings</span>
        </router-link>
      </nav>

      <div class="sidebar-providers">
        <div class="providers-label">Providers</div>
        <div v-if="activeProviders.length === 0" class="provider-none">— none active</div>
        <div v-for="p in activeProviders" :key="p" class="provider-row">
          <span class="provider-pip"></span>
          <span class="provider-name">{{ p }}</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <span class="footer-text">Phase 1 · MIT</span>
      </div>
    </aside>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useSettingsStore } from './stores'
import OceanScene from './components/OceanScene.vue'

const settings = useSettingsStore()
const activeProviders = computed(() => settings.activeProviders)
const cursorDot = ref(null)
const cursorRing = ref(null)

onMounted(() => {
  settings.fetchProviders()
  initCursor()
})

function initCursor() {
  let mx = 0, my = 0, rx = 0, ry = 0
  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY
    if (cursorDot.value) {
      cursorDot.value.style.left = mx + 'px'
      cursorDot.value.style.top = my + 'px'
    }
  })
  function animRing() {
    rx += (mx - rx) * 0.12
    ry += (my - ry) * 0.12
    if (cursorRing.value) {
      cursorRing.value.style.left = rx + 'px'
      cursorRing.value.style.top = ry + 'px'
    }
    requestAnimationFrame(animRing)
  }
  animRing()
  document.addEventListener('mouseover', e => {
    if (e.target.closest('a,button,.sim-card,.agent-card,.nav-item') && cursorRing.value && cursorDot.value) {
      cursorRing.value.style.width = '48px'
      cursorRing.value.style.height = '48px'
      cursorDot.value.style.transform = 'translate(-50%,-50%) scale(1.5)'
    }
  })
  document.addEventListener('mouseout', () => {
    if (cursorRing.value && cursorDot.value) {
      cursorRing.value.style.width = '32px'
      cursorRing.value.style.height = '32px'
      cursorDot.value.style.transform = 'translate(-50%,-50%) scale(1)'
    }
  })
}
</script>

<style scoped>
.app-shell { display: flex; height: 100vh; overflow: hidden; position: relative; }

.ambient-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.sidebar {
  position: relative;
  z-index: 10;
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255,255,255,0.06);
  background: rgba(0,0,0,0.55);
  backdrop-filter: blur(24px);
}

.sidebar-logo { display: flex; align-items: center; gap: 12px; padding: 28px 24px 22px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.logo-mark { flex-shrink: 0; }
.logo-text { display: flex; flex-direction: column; gap: 1px; }
.logo-name { font-family: var(--font-mono); font-size: 13px; font-weight: 500; letter-spacing: 0.15em; color: var(--white); }
.logo-ver { font-family: var(--font-mono); font-size: 10px; color: var(--ink-400); letter-spacing: 0.1em; }

.sidebar-nav { padding: 20px 0; flex: 1; display: flex; flex-direction: column; gap: 2px; }

.nav-item {
  display: flex; align-items: center;
  padding: 10px 24px;
  color: var(--ink-400);
  font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
  text-decoration: none;
  transition: color 0.15s ease;
  position: relative;
}
.nav-item::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 2px;
  background: white; transform: scaleY(0); transition: transform 0.2s ease;
}
.nav-item:hover { color: var(--ink-100); }
.nav-item:hover::before { transform: scaleY(0.4); opacity: 0.4; }
.nav-active { color: var(--white) !important; }
.nav-active::before { transform: scaleY(1) !important; opacity: 1 !important; }

.sidebar-providers { padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.04); }
.providers-label { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.15em; text-transform: uppercase; color: var(--ink-500); margin-bottom: 10px; }
.provider-none { font-family: var(--font-mono); font-size: 11px; color: var(--ink-500); }
.provider-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.provider-pip { width: 4px; height: 4px; border-radius: 50%; background: white; opacity: 0.6; }
.provider-name { font-family: var(--font-mono); font-size: 11px; color: var(--ink-200); letter-spacing: 0.04em; }

.sidebar-footer { padding: 16px 24px; border-top: 1px solid rgba(255,255,255,0.04); }
.footer-text { font-family: var(--font-mono); font-size: 10px; color: var(--ink-600); letter-spacing: 0.08em; }

.main-content {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  position: relative; z-index: 1;
  background: rgba(0,0,0,0.45);
  backdrop-filter: blur(2px);
}

.page-enter-active { animation: pageIn 0.3s ease forwards; }
.page-leave-active { animation: pageOut 0.2s ease forwards; }
@keyframes pageIn { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
@keyframes pageOut { from{opacity:1} to{opacity:0} }
</style>