import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import NewSimulation from './views/NewSimulation.vue'
import SimulationDetail from './views/SimulationDetail.vue'
import Settings from './views/Settings.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/new', component: NewSimulation },
    { path: '/simulation/:id', component: SimulationDetail },
    { path: '/settings', component: Settings },
  ]
})
