<script setup lang="ts">
const props = defineProps<{
  colorFields: Array<string>
  active?: string
}>()

const emit = defineEmits(['change'])
</script>

<template>
  <div class="d-flex">
    <!-- Legend -->
    <div id="legend" class="flex-grow-1"></div>

    <!-- Color column selector -->
    <div class="dropdown">
      <button
        class="btn btn-primary dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        title="Select map/cartogram color strategy"
      >
        <span class="d-none d-lg-inline me-2">Color</span>
        <i class="fas fa-palette"></i>
      </button>
      <ul class="dropdown-menu dropdown-menu-end">
        <li>
          <button
            class="dropdown-item"
            v-bind:class="{ active: props.active === 'Region' }"
            v-on:click="emit('change', 'Region')"
          >
            Region
          </button>
        </li>
        <li><button class="dropdown-item disabled">Data:</button></li>
        <li v-if="!props.colorFields.length">
          <button class="dropdown-item disabled">&nbsp;&nbsp;No color column</button>
        </li>
        <li
          v-for="(versionItem, versionKey) in props.colorFields"
          v-bind:value="versionItem"
          v-bind:key="versionKey"
        >
          <button
            class="dropdown-item"
            v-bind:class="{ active: props.active === versionItem }"
            v-on:click="emit('change', versionItem)"
          >
            &nbsp;&nbsp;{{ versionItem }}
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
