<script setup lang="ts">
import { ref } from 'vue'
import { Modal } from 'bootstrap'

const props = defineProps<{
  columns: Array<{
    label: string
    gamma_max: number | null
  }>
}>()

const emit = defineEmits<{
  proceed: []
  switch: []
}>()

let modalInstance: Modal | null = null
const modalEl = ref<HTMLElement | null>(null)

function open() {
  if (modalEl.value) {
    modalInstance = new Modal(modalEl.value, { backdrop: 'static', keyboard: false })
    modalInstance.show()
  }
}

function proceed() {
  modalInstance?.hide()
  emit('proceed')
}

function switchToChoropleth() {
  modalInstance?.hide()
  emit('switch')
}

defineExpose({ open })
</script>

<template>
  <div ref="modalEl" class="modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-warning-subtle border-warning">
          <h5 class="modal-title">
            <i class="fa-solid fa-triangle-exclamation text-warning me-2"></i>
            Extensivity warning
          </h5>
        </div>
        <div class="modal-body">
          <p>
            In a cartogram, each region's area represents its data value.
            When two regions merge, their areas add up — so the data must
            also add up for the map to remain meaningful.
          </p>
          <p>
            Our statistical model suggests the following
            {{ columns.length === 1 ? 'column' : 'columns' }}
            may <strong>not</strong> be additive:
          </p>
          <ul class="mb-3">
            <li v-for="col in columns" :key="col.label">
              <strong>{{ col.label }}</strong>
            </li>
          </ul>
          <p class="text-muted small mb-0">
            Variables like temperature, density, or percentages are typically
            not additive — a choropleth (color) map may be more appropriate.
          </p>
        </div>
        <div class="modal-footer d-flex gap-2 justify-content-end">
          <button class="btn btn-outline-secondary" @click="proceed">
            Create anyway
          </button>
          <button class="btn btn-primary" @click="switchToChoropleth">
            Try a choropleth instead
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
