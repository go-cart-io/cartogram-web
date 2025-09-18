// @ts-nocheck
import 'vite/modulepreload-polyfill'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import './styles'
import CartogramViewer from './viewer/components/CartogramViewer.vue'

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG
if (document.getElementById('cartogram-viewer')) {
  const viewer = createApp(CartogramViewer)
  viewer.use(createPinia())
  viewer.mount('#cartogram-viewer')
}
