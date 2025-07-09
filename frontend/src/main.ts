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
  const app = createApp(App)
  app.use(createPinia())
  app.mount('#cartogram-app')
}

if (document.getElementById('cartogram-maker')) {
  const maker = createApp(CartogramMaker, {
    maps,
    mapName,
    mapTitle,
    geoUrl,
    csvUrl,
    mapTypes,
    cartoColorScheme,
    choroSettings
  })
  maker.use(createPinia())
  maker.mount('#cartogram-maker')
}
