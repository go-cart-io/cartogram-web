// @ts-nocheck
import 'vite/modulepreload-polyfill'
import '../assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './components/Cartogram.vue'
import CartogramMaker from '../maker/components/CartogramMaker.vue'
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

if (document.getElementById('cartogram-maker')) {
  const maker = createApp(CartogramMaker, { maps })
  maker.use(createPinia())
  maker.mount('#cartogram-maker')
}
