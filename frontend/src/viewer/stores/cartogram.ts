import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useCartogramStore = defineStore('cartogram', () => {  
  const loadingProgress = ref(0)
  const currentMapName = ref("")
  const currentVersionName = ref("")
  const stringKey = ref("")
  const versions = ref({} as { [key: string]: any })
  const options = ref({
    showGrid: true,
    showBase: window.innerWidth > 768
  })

  const isLoading = computed(() => {
    return loadingProgress.value < 100
  })
  
  return { loadingProgress, currentMapName, currentVersionName, stringKey, versions, options, isLoading }
})
