import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// Should contain only reactive variables that are passed more than one level
export const useCartogramStore = defineStore('cartogram', () => {
  const currentMapName = ref('')
  const versions = ref({} as { [key: string]: any })
  const highlightedRegionID = ref('')
  const options = ref({
    showGrid: true,
    numberOfPanels: window.innerWidth > 768 ? 2 : 1
  })

  // const isLoading = computed(() => {
  //   return loadingProgress.value < 100
  // })

  return {
    currentMapName,
    versions,
    highlightedRegionID,
    options
  }
})
