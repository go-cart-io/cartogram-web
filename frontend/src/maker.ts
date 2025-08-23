// @ts-nocheck
import 'vite/modulepreload-polyfill'
import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import CartogramMaker from './maker/components/CartogramMaker.vue'
import './assets/styles.scss'

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
