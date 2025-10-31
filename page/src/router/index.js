import { createRouter, createWebHashHistory } from 'vue-router'
import Transcribe from '../views/Transcribe.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Transcribe
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
