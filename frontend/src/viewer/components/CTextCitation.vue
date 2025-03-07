<script setup lang="ts">
import * as util from '../lib/util'
const citation =
  'Gastner MT, Seguy V, More P. Fast low-based algorithm for creating density-equalizing map projections. Proc Natl Acad Sci USA 115(10):E2156–E2164 (2018).'
</script>

<template>
  <div>
    <p class="lead text-center">Liked our work? Make sure to credit us using the citation below:</p>
    <div class="form-group">
      <a
        id="citation-text"
        class="text-primary"
        href="https://www.pnas.org/content/115/10/E2156"
        target="_blank"
        rel="noopener noreferrer"
        >{{ citation }}</a
      >

      <button
        style="margin-top: 25px"
        class="clipboard-copy"
        id="clipboard-citation"
        data-animation="false"
        title="Copy"
        v-on:click="util.addClipboard('clipboard-citation', citation)"
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
</template>
