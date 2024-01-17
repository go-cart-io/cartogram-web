<script setup lang="ts">
import { ref, reactive } from 'vue'
import CTextCitation from './CTextCitation.vue'

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

  let mapAreaSVG = document.getElementById(area + '-svg')!.cloneNode(true) as SVGSVGElement

  // Add SVG xml namespace to SVG element, so that the file can be opened with any web browser.
  mapAreaSVG.setAttribute('xmlns', 'http://www.w3.org/2000/svg')

  let legendSVG = document.getElementById(area + '-legend')!.cloneNode(true) as HTMLElement
  mapAreaSVG.appendChild(legendSVG)

  let legendNumber = document.getElementById(area + '-legend-num')!.textContent || ''
  let legendNumberSVG = document.createElement('text')
  let legendNumberX = 2 + parseFloat(legendSVG.getAttribute('width')!)
  legendNumberSVG.innerHTML = legendNumber
  legendNumberSVG.setAttribute('font-family', 'sans-serif')
  legendNumberSVG.setAttribute('font-size', '12px')
  legendNumberSVG.setAttribute('x', legendNumberX.toString())
  legendNumberSVG.setAttribute('y', '20')
  mapAreaSVG.appendChild(legendNumberSVG)

  mapAreaSVG.appendChild(document.getElementById(area + '-grid-area')!.cloneNode(true))

  // document.getElementById('download-modal-svg-link').href = "data:image/svg+xml;base64," + window.btoa(svg_header + document.getElementById('map-area').innerHTML);
  let svgLinkEl = document.getElementById('download-modal-svg-link')! as HTMLAnchorElement
  svgLinkEl.href =
    'data:image/svg+xml;base64,' +
    window.btoa(svg_header + mapAreaSVG.outerHTML.replace(/×/g, '&#xD7;'))
  svgLinkEl.download = 'map.svg'

  let geoJsonLinkEl = document.getElementById('download-modal-geojson-link')! as HTMLAnchorElement
  geoJsonLinkEl.href = 'data:application/json;base64,' + window.btoa(geojson)
  geoJsonLinkEl.download = 'map.geojson'

  state.show = true
}

defineExpose({
  generateSVGDownloadLinks
})
</script>

<template>
  <div
    class="modal fade text-wrap"
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
            <a id="download-modal-svg-link" class="btn btn-lg btn-primary mx-3">SVG</a>
            <a id="download-modal-geojson-link" class="btn btn-lg btn-primary">GeoJSON</a>
          </p>
          <c-text-citation />
        </div>
      </div>
    </div>
  </div>
</template>

<style></style>
