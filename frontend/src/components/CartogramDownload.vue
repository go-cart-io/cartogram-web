<script setup lang="ts">
import { ref, reactive } from 'vue'
import Citation from './Citation.vue'

const state = reactive({
  show: false
})

/**
 * generateSVGDownloadLinks generates download links for the map(s) and/or cartogram(s) displayed on the left and
 * right. We do this by taking advantage of the fact that D3 generates SVG markup. We convert the SVG markup into a
 * blob URL.
 */
function generateSVGDownloadLinks(area: string, geojson: any) {
  var svg_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>'

  let mapArea = document.getElementById(area).cloneNode(true)
  let mapAreaSVG = mapArea.getElementsByTagName('svg')[0]

  // Add SVG xml namespace to SVG element, so that the file can be opened with any web browser.
  mapAreaSVG.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  // Increase height of SVG to accommodate legend and total.
  const mapHeight = parseFloat(mapAreaSVG.getAttribute('height'))
  mapAreaSVG.setAttribute('height', mapHeight + 100)

  let legendSVG = document.getElementById(area + '-legend').cloneNode(true)

  // Iterate legend SVG's text elements and add font attribute.
  for (let i = 0; i < legendSVG.getElementsByTagName('text').length; i++) {
    legendSVG.getElementsByTagName('text')[i].setAttribute('font-family', 'sans-serif')
  }

  // Iterate legend SVG's elements and append them to map SVG.
  for (let i = 0; i < legendSVG.children.length; i++) {
    let newY = parseFloat(legendSVG.children[i].getAttribute('y')) + mapHeight
    legendSVG.children[i].setAttribute('y', newY)
    let newX = parseFloat(legendSVG.children[i].getAttribute('x')) + 20
    legendSVG.children[i].setAttribute('x', newX)
    mapAreaSVG.appendChild(legendSVG.children[i].cloneNode(true))
  }

  // document.getElementById('download-modal-svg-link').href = "data:image/svg+xml;base64," + window.btoa(svg_header + document.getElementById('map-area').innerHTML);
  document.getElementById('download-modal-svg-link').href =
    'data:image/svg+xml;base64,' +
    window.btoa(svg_header + mapArea.innerHTML.replace(/×/g, '&#xD7;'))
  document.getElementById('download-modal-svg-link').download = 'map.svg'

  document.getElementById('download-modal-geojson-link').href =
    'data:application/json;base64,' + window.btoa(geojson)
  document.getElementById('download-modal-geojson-link').download = 'map.geojson'

  state.show = true
}

defineExpose({
  generateSVGDownloadLinks
})
</script>

<template>
  <div
    class="modal fade"
    id="downloadModal"
    tabindex="-1"
    aria-labelledby="downloadModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="downloadModalLabel">Your map is ready!</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <p class="lead text-center">Download</p>
          <p class="text-center mb-5">
            <button id="download-modal-svg-link" class="btn btn-lg btn-primary mx-3">SVG</button>
            <button id="download-modal-geojson-link" class="btn btn-lg btn-primary">GeoJSON</button>
          </p>
          <Citation />
        </div>
      </div>
    </div>
  </div>
</template>

<style></style>
