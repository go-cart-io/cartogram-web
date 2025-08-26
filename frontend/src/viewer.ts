// @ts-nocheck
import 'vite/modulepreload-polyfill'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import './common'
import App from './viewer/components/CartogramViewer.vue'

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG
if (document.getElementById('cartogram-app')) {
  const app = createApp(App)
  app.use(createPinia())
  app.mount('#cartogram-app')
}
