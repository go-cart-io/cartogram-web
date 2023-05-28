<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'

import * as util from '../lib/util'
import CartogramUI from './CartogramUI.vue'

const props = defineProps<{
  defaultHandler: string
  cartogram_handlers: Array<{ id: string; display_name: string }> | null
  cartogram_data: any
  cartogramui_data: any
  mode: string | null
  scale: number
}>()

// Form values
const selectedHandler = props.defaultHandler
const csvInput = ref()
// Elements
const cartogramUIEl = ref()

onMounted(() => {
  // console.log(cartogramUIEl.value)
})
</script>

<template>
  <div v-if="props.mode === 'embed'" class="container-fluid mt-3">
    <CartogramUI
      ref="cartogramUIEl"
      v-bind:handler="selectedHandler"
      v-bind:cartogram_data="props.cartogram_data"
      v-bind:cartogramui_data="props.cartogramui_data"
      v-bind:mode="props.mode"
      v-bind:scale="props.scale"
    />
  </div>
  <div v-else class="container-fluid mt-5 main-content">
    <div class="row">
      <div class="col-md-6">
        <div class="row">
          <div class="col-2">
            <p class="lead">Input:</p>
          </div>
          <div class="col-10">
            <div class="dropdown">
              <button class="btn btn btn-primary no-click">Download Template Data</button>
              <div class="dropdown-content">
                <a class="top-item" id="csv-template-link" href="#">CSV File</a>
                <a class="bottom-item" id="xlsx-template-link" href="#">Excel File</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-md-6">
        <div class="row">
          <div class="col-3">
            <p class="lead">Select Map:</p>
          </div>
          <div class="col-5">
            <select
              style="cursor: pointer"
              class="form-control border-primary bg-primary text-light"
              id="handler"
              v-model="selectedHandler"
              v-on:change="cartogramUIEl.switchMap(selectedHandler)"
            >
              <option v-for="handler in props.cartogram_handlers" v-bind:value="handler.id">
                <!-- TODO: {% if handler.id==default_cartogram_handler %}selected{% endif %} -->
                {{ handler.display_name }}
              </option>
            </select>
          </div>
          <div class="col-4">
            <input
              type="button"
              class="btn btn-primary mb-2 d-block w-100"
              value="Upload Data"
              onclick="util.clearFileInput(document.getElementById('csv'));document.getElementById('csv').click();"
              id="upload-button"
            />
            <input
              type="button"
              class="btn btn-primary mb-2 d-block w-100"
              value="Edit"
              id="edit-button"
              v-on:click="cartogramUIEl.launchGridEdit()"
            />
          </div>
        </div>
        <p id="non-fatal-error" class="text-danger font-weight-bold"></p>
      </div>
    </div>

    <input
      type="file"
      name="csv"
      id="csv"
      class="form-control-file"
      accept="text/csv,.csv,.xlsx,.xls"
      style="display: none"
      v-on:change="cartogramUIEl.requestAndDrawCartogram()"
    />

    <p class="lead">Output:</p>

    <CartogramUI
      ref="cartogramUIEl"
      v-bind:handler="selectedHandler"
      v-bind:cartogram_data="props.cartogram_data"
      v-bind:cartogramui_data="props.cartogramui_data"
      v-bind:mode="props.mode"
      v-bind:scale="props.scale"
    />
  </div>

  <div id="barchart-container" style="display: none">
    <p>
      Your cartogram was unable to be generated due to an error. You may make use of this barchart
      instead, or refresh the page and try again.
    </p>

    <div id="barchart" style="height: 600px"></div>
  </div>

  <div id="piechart" style="display: none">
    <div class="row">
      <div class="col-md-6">
        <h4>Confirm your data are appropriate for a cartogram</h4>
        <p>
          Your data sums to an approximate total of <b id="data-total"></b>. Is this a
          <a href="/faq#what-kind-of-data">meaningful quantity</a>? Additionally, you may consider
          the pie chart below. If it is an acceptable visualization for your dataset, then you can
          present your data as a cartogram. Otherwise, please choose a different dataset to
          continue.
        </p>
      </div>
    </div>
    <div id="piechart-area"></div>
    <div class="row" id="piechart-buttons">
      <button class="btn btn-primary mr-5" id="piechart-yes">Yes, I Confirm</button>
      <button class="btn btn-primary" id="piechart-no">Cancel</button>
    </div>
  </div>

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
              onclick="util.addClipboard('clipboard-citation2',document.getElementById('citation-text2').innerText);
              document.getElementById('clipboard-citation2').click()"
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

  <div class="modal fade" id="share-modal" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-lg modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header" style="border-bottom: none">
          <img src="/static/img/gocart_final.svg" width="150" alt="go-cart.io logo" />
          <button type="button" class="close" data-dismiss="modal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <div class="modal-body">
          <h3 class="mb-1 text-center">Share Now!</h3>
          <div class="d-flex mb-3 justify-content-center">
            <div class="share-link">
              <a
                href="https://www.facebook.com/sharer/sharer.php?u=https%3A%2F%2Fgo-cart.io"
                onclick="javascript:window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=300,width=600');return false;"
                target="_blank"
                title="Share on Facebook"
                class="social-link"
                id="facebook-share"
                ><i class="fab fa-facebook-square"></i
              ></a>
            </div>

            <div class="share-link">
              <a
                href="https://www.linkedin.com/shareArticle?url=https%3A%2F%2Fgo-cart.io&mini=true&title=Cartogram&summary=Create%20cartograms%20with%20go-cart.io&source=go-cart.io"
                onclick="javascript:window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=520,width=570');return false;"
                target="_blank"
                title="Share on LinkedIn"
                class="social-link"
                id="linkedin-share"
                ><i class="fab fa-linkedin"></i
              ></a>
            </div>

            <div class="share-link">
              <a
                href="https://twitter.com/share?url=https%3A%2F%2Fgo-cart.io"
                onclick="javascript:window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=300,width=600');return false;"
                target="_blank"
                title="Share on Twitter"
                class="social-link"
                id="twitter-share"
                ><i class="fab fa-twitter-square"></i
              ></a>
            </div>

            <div class="share-link">
              <a
                href="mailto:?body=https%3A%2F%2Fgo-cart.io"
                title="Share by Email"
                class="social-link"
                id="email-share"
                ><i class="fas fa-envelope-square"></i
              ></a>
            </div>
          </div>

          <div class="mb-3">
            <h3 class="text-center">Link</h3>
            <div class="form-group">
              <input
                type="text"
                id="share-link-href"
                class="form-control w-100"
                disabled
                style="font-family: monospace"
                value="https://go-cart.io"
              />
              <button
                style="margin-top: 4.6px"
                data-animation="false"
                class="clipboard-copy"
                id="clipboard-link"
                title="Copy"
              >
                <img id="clipboard-link-icon" src="/static/img/clipboard.svg" alt="Copy button" />
              </button>
            </div>
          </div>

          <div id="share-embed" class="mb-5" style="display: none">
            <h3 class="text-center">Embed</h3>
            <p class="text-center">
              To embed yor cartogram into any webpage, insert the HTML code below:
            </p>
            <div class="form-group">
              <textarea
                id="share-embed-code"
                class="form-control w-100"
                disabled
                rows="3"
                style="font-family: monospace; resize: none"
              ></textarea>
              <button
                class="clipboard-copy"
                id="clipboard-embed"
                data-animation="false"
                title="Copy"
              >
                <img id="clipboard-embed-icon" src="/static/img/clipboard.svg" alt="Copy button" />
              </button>
            </div>
          </div>

          <div>
            <p class="lead text-center">
              Liked our work? Make sure to credit us using the citation below:
            </p>
            <div class="form-group">
              <a
                id="citation-text"
                class="text-primary"
                href="https://www.pnas.org/content/115/10/E2156"
                target="_blank"
                rel="noopener noreferrer"
                >Gastner MT, Seguy V, More P. Fast low-based algorithm for creating
                density-equalizing map projections. Proc Natl Acad Sci USA 115(10):E2156–E2164
                (2018).</a
              >

              <button
                style="margin-top: 25px"
                class="clipboard-copy"
                id="clipboard-citation"
                data-animation="false"
                title="Copy"
                onclick="util.addClipboard('clipboard-citation',document.getElementById('citation-text').innerText);
              document.getElementById('clipboard-citation').click()"
              >
                <img
                  id="clipboard-citation-icon"
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
  </div>
</template>

<style scoped>
.social-link {
  font-size: 50px;
  color: #707070;
  text-decoration: none;
}

.social-link:hover {
  color: #d76127;
}

.share-link {
  margin-left: 10px;
  margin-right: 10px;
}

.no-click {
  pointer-events: none;
}

.dropdown {
  margin-right: 10px;
  position: relative;
  display: inline-block;
}

.dropdown-content {
  list-style: none;
  position: absolute;
  left: -9999px;
  /* Move it off-screen until hover */
  border-radius: 1.2rem;
  margin-top: 1px;
  width: 100px;
  background-color: #d76127;
  z-index: 1;
}

.dropdown-content a {
  color: white;
  padding: 6px 8px;
  text-decoration: none;
  display: block;
}

.dropdown-content a:hover {
  background-color: #b75222;
}

.dropdown-content .top-item:hover {
  border-radius: 1.2rem 1.2rem 0 0;
}

.dropdown-content .bottom-item:hover {
  border-radius: 0 0 1.2rem 1.2rem;
}

.dropdown:hover .dropdown-content {
  left: auto;
  /* Bring back on-screen when needed */
  right: 0;
}

.form-group {
  position: relative;
}

.clipboard-copy {
  position: absolute;
  top: 0;
  right: 0;
  margin-top: 8px;
  margin-right: 15px;
  cursor: pointer;
  border-radius: 3px;
  border: 1px solid #d7d3d3;
}

.clipboard-copy:hover {
  background-color: #dfdbdb;
}

#barchart svg {
  overflow: visible !important;
}

#barchart text.label {
  font-size: 0.8rem;
  letter-spacing: -0.01rem;
}

@media screen and (min-width: 1600px) {
  .main-content {
    padding-left: 250px;
    padding-right: 250px;
  }
}

#piechart-area svg {
  width: 960px;
  height: 450px;
}
</style>
