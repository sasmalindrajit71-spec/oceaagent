import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './assets/global.css'
import { API_BASE } from './api.js'

import Dashboard        from './views/Dashboard.vue'
import NewSimulation    from './views/NewSimulation.vue'
import SimulationDetail from './views/SimulationDetail.vue'
import Settings         from './views/Settings.vue'
import Admin            from './views/Admin.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/',               component: Dashboard },
    { path: '/new',            component: NewSimulation },
    { path: '/simulate',       component: NewSimulation },
    { path: '/simulation/:id', component: SimulationDetail },
    { path: '/console',        redirect: '/' },
    { path: '/settings',       component: Settings },
    { path: '/admin',          component: Admin },
  ]
})

// Track page views on every route change
router.afterEach((to) => {
  fetch(`${API_BASE}/analytics/pageview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: to.fullPath }),
  }).catch(() => {})
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')