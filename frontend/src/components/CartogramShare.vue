<script setup lang="ts">
import { computed, reactive } from 'vue'
import * as util from '../lib/util'
import Citation from './Citation.vue'

const props = defineProps<{
  key?: string | null
  sysname?: string | null
}>()

const state = reactive({
  show: false
})

const socialURL = computed(() => {
  if (props.key) return location.protocol + '//' + location.host + '/cart/' + props.key

  return location.protocol + '//' + location.host + '/cartogram/' + props.sysname
})

const socialURLEncoded = computed(() => {
  return window.encodeURIComponent(socialURL.value)
})

const embedHTML = computed(() => {
  let embedURL
  if (props.key) {
    embedURL = location.protocol + '//' + window.location.host + '/embed/cart/' + props.key
  } else {
    embedURL = location.protocol + '//' + window.location.host + '/embed/map/' + props.sysname
  }

  return (
    '<iframe src="' +
    embedURL +
    '" width="800" height="550" style="border: 1px solid black;"></iframe>'
  )
})

function show() {
  state.show = true
}

defineExpose({
  show
})
</script>

<template>
  <b-modal v-model="state.show" hide-footer>
    <h3 class="mb-1 text-center">Share Now!</h3>
    <div class="d-flex mb-3 justify-content-center">
      <div class="share-link">
        <a
          v-bind:href="'https://www.facebook.com/sharer/sharer.php?u=' + socialURLEncoded"
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
      </div>

      <div class="share-link">
        <a
          v-bind:href="'https://twitter.com/share?url=' + socialURLEncoded"
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
          >{{ embedHTML }}</textarea
        >
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

    <Citation />
  </b-modal>
</template>

<style scoped></style>
