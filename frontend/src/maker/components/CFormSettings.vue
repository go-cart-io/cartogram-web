<script setup lang="ts">
import * as config from '../../common/config'

import { useProjectStore } from '../stores/project'
const store = useProjectStore()

const props = defineProps<{
  disabled: boolean
}>()
</script>

<template>
  <div class="p-2">
    Project Title
    <input type="text" class="form-control" v-model="store.title" maxlength="100" />
  </div>

  <div class="p-2">
    <div class="form-check">
      <input
        id="chk-inset"
        class="form-check-input"
        type="checkbox"
        v-model="store.useInset"
        v-bind:disabled="props.disabled"
        v-on:change="store.dataTable.fields[config.COL_INSET].show = store.useInset"
      />
      <label class="form-check-label" for="chk-inset"> Define inset of specific regions </label>
    </div>
  </div>

  <div class="p-2">
    Review data and select a visualization method for each column in the input overview panel.
  </div>
</template>
