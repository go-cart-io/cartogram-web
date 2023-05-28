// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import App from './components/Cartogram.vue'

if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    defaultHandler,
    cartogram_handlers,
    cartogram_data,
    cartogramui_data,
    mode,
    scale
  })
  // app.config.compilerOptions.delimiters = ['[[', ']]']
  // app.provide('defaultHandler', defaultHandler)
  app.mount('#cartogram-app')
}
