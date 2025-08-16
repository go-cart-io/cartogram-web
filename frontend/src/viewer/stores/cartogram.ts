import { ref } from 'vue'
import { defineStore } from 'pinia'

// Should contain only reactive variables that are passed more than one level
export const useCartogramStore = defineStore('cartogram', () => {
  const currentMapName = ref('')
  const currentColorCol = ref('Region')
  const highlightedRegionID = ref('')
  const options = ref({
    gridOpacity: 0.3,
    numberOfPanels: window.innerWidth > 768 ? 2 : 1
  })

  // const isLoading = computed(() => {
  //   return loadingProgress.value < 100
  // })

  return {
    currentMapName,
    currentColorCol,
    highlightedRegionID,
    options
  }
})
