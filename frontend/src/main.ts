// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './components/Cartogram.vue'
import './assets/styles.scss'

if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    defaultHandler,
    cartogram_handlers,
    cartogram_data,
    cartogramui_data,
    mode
  })
  app.use(createPinia())
  // app.config.compilerOptions.delimiters = ['[[', ']]']
  // app.provide('defaultHandler', defaultHandler)
  app.mount('#cartogram-app')
}
