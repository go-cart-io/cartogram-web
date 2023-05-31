// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import App from './components/Cartogram.vue'

import BootstrapVue3 from 'bootstrap-vue-3'
// Import Bootstrap an BootstrapVue CSS files (order is important)
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue-3/dist/bootstrap-vue-3.css'
// Make BootstrapVue available throughout your project

if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    defaultHandler,
    cartogram_handlers,
    cartogram_data,
    cartogramui_data,
    mode,
    scale
  })
  app.use(BootstrapVue3)
  // app.config.compilerOptions.delimiters = ['[[', ']]']
  // app.provide('defaultHandler', defaultHandler)
  app.mount('#cartogram-app')
}
