<script setup lang="ts">
import { computed } from 'vue'
import * as util from '../lib/util'
import CTextCitation from './CTextCitation.vue'

const props = defineProps<{
  currentMapName: string
  stringKey: string
  versions: { [key: string]: any }
  versionKey: string
  mapID: string
}>()

const version = computed(() => {
  return props.versions[props.versionKey]
})

const geolink = computed(() => {
  return util.getGeojsonURL(
    props.currentMapName,
    props.stringKey,
    props.versions[props.versionKey].name + '.json'
  )
})

/**
 * Generates download links for the map(s) and/or cartogram(s) displayed on the left and
 * right. We do this by taking advantage of the fact that D3 generates SVG markup. We convert the SVG markup into a
 * blob URL.
 */
function downloadSVG() {
  var svg_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'

  let mapAreaSVG = document
    .getElementById(props.mapID + '-vis')!
    .querySelector('svg')!
    .cloneNode(true) as SVGSVGElement

  // Add SVG xml namespace to SVG element, so that the file can be opened with any web browser.
  mapAreaSVG.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  let legendSVG = document.getElementById(props.mapID + '-legend')!.cloneNode(true) as HTMLElement
  mapAreaSVG.appendChild(legendSVG)

  let legendNumber = document.getElementById(props.mapID + '-legend-num')!.textContent || ''
  let legendNumberSVG = document.createElement('text')
  let legendNumberX = 2 + parseFloat(legendSVG.getAttribute('width')!)
  legendNumberSVG.innerHTML = legendNumber
  legendNumberSVG.setAttribute('font-family', 'sans-serif')
  legendNumberSVG.setAttribute('font-size', '12px')
  legendNumberSVG.setAttribute('x', legendNumberX.toString())
  legendNumberSVG.setAttribute('y', '20')
  mapAreaSVG.appendChild(legendNumberSVG)
  mapAreaSVG.appendChild(document.getElementById(props.mapID + '-grid-area')!.cloneNode(true))

  const a = document.createElement('a')
  a.href =
    'data:image/svg+xml;base64,' +
    window.btoa(svg_header + mapAreaSVG.outerHTML.replace(/×/g, '&#xD7;'))
  a.download = props.versions[props.versionKey].name + '.svg'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
</script>

<template>
  <button
    class="btn btn-primary me-2"
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
            <a v-on:click="downloadSVG()" class="btn btn-lg btn-primary mx-3">SVG</a>
            <a v-bind:href="geolink" download class="btn btn-lg btn-primary">GeoJSON</a>
          </p>
          <c-text-citation />
        </div>
      </div>
    </div>
  </div>
</template>

<style></style>
