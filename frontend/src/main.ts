// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './viewer/components/CartogramViewer.vue'
import CartogramMaker from './maker/components/CartogramMaker.vue'
import './assets/styles.scss'

if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    maps,
    mapName,
    mapTitle,
    mapDBKey,
    mode
  })
  app.provide('colorScheme', mapColorScheme)
  app.use(createPinia())
  // app.config.compilerOptions.delimiters = ['[[', ']]']
  // app.provide('defaultHandler', defaultHandler)
  app.mount('#cartogram-app')
}

if (document.getElementById('cartogram-maker')) {
  const maker = createApp(CartogramMaker, {
    maps,
    mapName,
    mapTitle,
    mapColorScheme,
    geoUrl,
    csvUrl
  })
  maker.use(createPinia())
  maker.mount('#cartogram-maker')
}
