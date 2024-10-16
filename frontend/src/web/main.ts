// @ts-nocheck
import 'vite/modulepreload-polyfill'
import '../assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './components/Cartogram.vue'
import CartogramEditor from './components/CartogramEditor.vue'
import '../assets/styles.scss'

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

if (document.getElementById('cartogram-editor')) {
  const editor = createApp(CartogramEditor, { maps })
  editor.use(createPinia())
  editor.mount('#cartogram-editor')
}
