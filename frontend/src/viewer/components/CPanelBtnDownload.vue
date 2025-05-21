<script setup lang="ts">
import { computed } from 'vue'
import * as util from '../lib/util'
import CTextCitation from './CTextCitation.vue'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const props = defineProps<{
  mapDBKey: string
  versionKey: string
  panelID: string
}>()

const version = computed(() => {
  return store.versions[props.versionKey]
})

const geolink = computed(() => {
  const ext =
    store.versions[props.versionKey].name === 'Geographic Area' ? '.json' : '_simplified.json'
  return util.getGeojsonURL(
    store.currentMapName,
    props.mapDBKey,
    store.versions[props.versionKey].name + ext
  )
})

const csvlink = computed(() => {
  return util.getCsvURL(store.currentMapName, props.mapDBKey)
})
/**
 * Generates download links for the map(s) and/or cartogram(s) displayed on the left and
 * right. We do this by taking advantage of the fact that D3 generates SVG markup. We convert the SVG markup into a
 * blob URL.
 */
function downloadSVG() {
  const svg_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'

  const mapAreaSVG = document
    .getElementById(props.panelID + '-vis')!
    .querySelector('svg')!
    .cloneNode(true) as SVGSVGElement

  // Add SVG xml namespace to SVG element, so that the file can be opened with any web browser.
  mapAreaSVG.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  const legendSVG = document
    .getElementById(props.panelID + '-legend')!
    .cloneNode(true) as HTMLElement
  mapAreaSVG.appendChild(legendSVG)

  const legendNumber = document.getElementById(props.panelID + '-legend-num')!.textContent || ''
  const legendNumberSVG = document.createElement('text')
  const legendNumberX = 2 + parseFloat(legendSVG.getAttribute('width')!)
  legendNumberSVG.textContent = legendNumber.replace('Total:', ' / Total:')
  legendNumberSVG.setAttribute('font-family', 'sans-serif')
  legendNumberSVG.setAttribute('font-size', '12px')
  legendNumberSVG.setAttribute('x', legendNumberX.toString())
  legendNumberSVG.setAttribute('y', '20')
  mapAreaSVG.appendChild(legendNumberSVG)
  mapAreaSVG.appendChild(document.getElementById(props.panelID + '-grid-area')!.cloneNode(true))

  // https://stackoverflow.com/questions/68122097/how-can-i-ensure-text-is-valid-for-an-svg
  const dummy = document.createElement('div')
  const svgData = mapAreaSVG.outerHTML.replace(/(&(?!(amp|gt|lt|quot|apos))[^;]+;)/g, (t) => {
    dummy.innerHTML = t
    return dummy.textContent || ''
  })

  const a = document.createElement('a')
  const svgBlob = new Blob([svg_header + svgData.replace(/×/g, '&#xD7;')], {
    type: 'image/svg+xml;charset=utf-8'
  })
  const url = URL.createObjectURL(svgBlob)
  a.href = url

  a.download = store.versions[props.versionKey].name + '.svg'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)

  if (typeof window.gtag !== 'undefined') {
    window.gtag('event', 'file_download', {
      file_name: geolink.value.replace('json', 'svg').replace('_simplified', ''),
      file_extension: 'svg'
    })
  }
}

function downloadJson() {
  if (typeof window.gtag !== 'undefined') {
    window.gtag('event', 'file_download', {
      file_name: geolink.value,
      file_extension: 'json'
    })
  }
}
</script>

<template>
  <button
    class="btn btn-primary"
    data-bs-toggle="modal"
    v-bind:data-bs-target="'#downloadModal' + version.key"
    v-bind:title="'Download ' + version.name"
  >
    <i class="fas fa-download"></i>
  </button>

  <div
    class="modal fade text-wrap"
    v-bind:id="'downloadModal' + version.key"
    tabindex="-1"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5">Your map is ready!</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <p class="lead text-center">Download</p>
          <p class="text-center">
            <a v-on:click="downloadSVG" class="btn btn-lg btn-primary mx-3">SVG</a>
            <a
              v-bind:href="geolink"
              v-on:click="downloadJson"
              download
              class="btn btn-lg btn-primary"
              >GeoJSON</a
            >
            <a v-bind:href="csvlink" download class="btn btn-lg btn-primary mx-3">CSV</a>
          </p>
          <c-text-citation />
        </div>
      </div>
    </div>
  </div>
</template>

<style></style>
