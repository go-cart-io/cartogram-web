// @ts-nocheck
import 'vite/modulepreload-polyfill'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import './styles'
import CartogramMaker from './maker/components/CartogramMaker.vue'

if (document.getElementById('cartogram-maker')) {
  const maker = createApp(CartogramMaker, {
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
