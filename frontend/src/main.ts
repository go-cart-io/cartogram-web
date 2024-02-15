// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './components/Cartogram.vue'
import './assets/styles.scss'

if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    mapName,
    maps,
    mapDataKey,
    mode
  })
  app.use(createPinia())
  // app.config.compilerOptions.delimiters = ['[[', ']]']
  // app.provide('defaultHandler', defaultHandler)
  app.mount('#cartogram-app')
}
