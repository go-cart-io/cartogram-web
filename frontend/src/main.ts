// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './viewer/components/CartogramViewer.vue'
import CartogramMaker from './maker/components/CartogramMaker.vue'
import './assets/styles.scss'

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG
if (document.getElementById('cartogram-app')) {
  const app = createApp(App, {
    maps: CARTOGRAM_CONFIG.maps,
    mapName: CARTOGRAM_CONFIG.mapName,
    mapTitle: CARTOGRAM_CONFIG.mapTitle,
    mapDBKey: CARTOGRAM_CONFIG.mapDBKey,
    mode: CARTOGRAM_CONFIG.mode
  })
  app.use(createPinia())

  // app.config.compilerOptions.delimiters = ['[[', ']]']
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
