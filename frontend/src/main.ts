// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import BootstrapVue3 from 'bootstrap-vue-3'
import App from './components/Cartogram.vue'
import './assets/styles.scss'

if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    defaultHandler,
    cartogram_handlers,
    cartogram_data,
    cartogramui_data,
    mode,
    scale
  })
  app.use(BootstrapVue3) // Make BootstrapVue available throughout your project
  // app.config.compilerOptions.delimiters = ['[[', ']]']
  // app.provide('defaultHandler', defaultHandler)
  app.mount('#cartogram-app')
}
