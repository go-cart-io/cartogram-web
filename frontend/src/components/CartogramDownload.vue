<script setup lang="ts">
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

  $('#download-modal').modal()
}

defineExpose({
  generateSVGDownloadLinks
})
</script>

<template>
  <div class="modal fade" id="download-modal" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header" style="border-bottom: none">
          <img src="/static/img/gocart_final.svg" width="150" alt="go-cart.io logo" />
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <p class="lead mb-5 text-center">Your map is ready!</p>
          <p class="text-center mb-5">
            <a
              href=""
              download=""
              id="download-modal-svg-link"
              class="btn btn-lg btn-primary"
              style="border-radius: 1.2em"
              >Download SVG</a
            >
            <a
              href=""
              download=""
              id="download-modal-geojson-link"
              class="btn btn-lg btn-primary ml-5"
              style="border-radius: 1.2em"
              >Download GeoJSON</a
            >
          </p>
          <p class="lead text-center">
            Liked our work? Make sure to credit us using the citation below:
          </p>
          <div class="form-group">
            <a
              id="citation-text2"
              class="text-primary"
              href="https://www.pnas.org/content/115/10/E2156"
              target="_blank"
              rel="noopener noreferrer"
              >Gastner MT, Seguy V, More P. Fast low-based algorithm for creating density-equalizing
              map projections. Proc Natl Acad Sci USA 115(10):E2156–E2164 (2018).</a
            >

            <button
              style="margin-top: 25px"
              class="clipboard-copy"
              id="clipboard-citation2"
              data-animation="false"
              title="Copy"
              v-on:click="
                util.addClipboard(
                  'clipboard-citation2',
                  document.getElementById('citation-text2').innerText
                )
              "
            >
              <img
                id="clipboard-citation2-icon"
                src="/static/img/clipboard.svg"
                alt="Copy button"
                title="Copy"
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style></style>
