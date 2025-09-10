<script setup lang="ts">
import { computed } from 'vue'
import * as util from '../lib/util'

import { useCartogramStore } from '../stores/cartogram'
const store = useCartogramStore()

const CARTOGRAM_CONFIG = window.CARTOGRAM_CONFIG

const queryString = computed(() => {
  const params = new URLSearchParams()
  if (store.currentColorCol !== 'Region') params.append('by', store.currentColorCol)
  const queryString = params.toString()
  return queryString ? `?${queryString}` : ''
})

const baseURL = computed(() => {
  if (CARTOGRAM_CONFIG.mapDBKey && CARTOGRAM_CONFIG.mapDBKey !== '')
    return location.protocol + '//' + location.host + '/view/key/' + CARTOGRAM_CONFIG.mapDBKey

  return location.protocol + '//' + location.host + '/view/map/' + store.currentMapName
})

const socialURL = computed(() => {
  return baseURL.value + queryString.value
})

const socialURLEncoded = computed(() => {
  return window.encodeURIComponent(baseURL.value)
})

const embedHTML = computed(() => {
  const embedURL = baseURL.value + '/embed' + queryString.value

  return (
    '<iframe src="' +
    embedURL +
    '" width="800" height="550" style="border: 1px solid black;"></iframe>'
  )
})

function access() {
  const http = new XMLHttpRequest()
  http.open('GET', baseURL.value)
}
</script>

<template>
  <!-- Button trigger modal -->
  <button
    id="shareBtn"
    class="btn btn-primary d-flex align-items-center"
    data-bs-toggle="modal"
    data-bs-target="#shareModal"
    title="Save and share cartogram"
    v-on:click="access()"
  >
    <span class="d-none d-lg-block me-2">Share</span>
    <i class="fas fa-share-alt"></i>
  </button>

  <!-- Modal -->
  <div
    class="modal fade text-wrap"
    id="shareModal"
    tabindex="-1"
    aria-labelledby="shareModalLabel"
    aria-hidden="true"
  >
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="shareModalLabel">Share cartogram</h1>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <div>
            <div>
              <p class="bg-warning-subtle p-1 rounded">
                <span class="badge text-bg-warning">Important</span> The share link/embed will be
                pruned from our server if there is no access for one year. We strongly advise you to
                back up your original data in a safe place so you can regenerate the cartogram if
                needed.
              </p>
            </div>
            <h3 class="text-center">Share now</h3>
            <div class="text-center">
              <a
                v-bind:href="'https://www.facebook.com/sharer/sharer.php?u=' + socialURLEncoded"
                onclick="javascript:window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=300,width=600');return false;"
                target="_blank"
                title="Share on Facebook"
                class="social-link"
                id="facebook-share"
                ><i class="fab fa-facebook-square"></i
              ></a>

              <a
                v-bind:href="
                  'https://www.linkedin.com/shareArticle?url=' +
                  socialURLEncoded +
                  '&mini=true&title=Cartogram&summary=Create%20cartograms%20with%20go-cart.io&source=go-cart.io'
                "
                onclick="javascript:window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=520,width=570');return false;"
                target="_blank"
                title="Share on LinkedIn"
                class="social-link"
                id="linkedin-share"
                ><i class="fab fa-linkedin"></i
              ></a>

              <a
                v-bind:href="'https://twitter.com/share?url=' + socialURLEncoded"
                onclick="javascript:window.open(this.href, '', 'menubar=no,toolbar=no,resizable=yes,scrollbars=yes,height=300,width=600');return false;"
                target="_blank"
                title="Share on Twitter"
                class="social-link"
                id="twitter-share"
                ><i class="fab fa-twitter-square"></i
              ></a>

              <a
                v-bind:href="'mailto:?body=' + socialURLEncoded"
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
                v-bind:value="socialURL"
              />
              <button
                style="margin-top: 4.6px"
                data-animation="false"
                class="clipboard-copy"
                id="clipboard-link"
                title="Copy"
                v-on:click="util.addClipboard('clipboard-link', socialURL)"
              >
                <img id="clipboard-link-icon" src="/static/img/clipboard.svg" alt="Copy button" />
              </button>
            </div>
          </div>

          <div id="share-embed" class="mb-5">
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
                v-model="embedHTML"
              ></textarea>
              <button
                class="clipboard-copy"
                id="clipboard-embed"
                data-animation="false"
                title="Copy"
                v-on:click="util.addClipboard('clipboard-embed', embedHTML)"
              >
                <img id="clipboard-embed-icon" src="/static/img/clipboard.svg" alt="Copy button" />
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
  padding: 5px;
}

.social-link:hover {
  color: #d76127;
}
</style>
