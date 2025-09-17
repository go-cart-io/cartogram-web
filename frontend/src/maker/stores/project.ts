import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { DataTable } from '../lib/interface'

export const useProjectStore = defineStore('project', () => {
  const title = ref('')
  const useInset = ref(false)
  const currentColorCol = ref('Region')
  const cartoColorScheme = ref('pastel1')
  const choroSettings = ref({
    isAdvanceMode: false,
    scheme: 'blues',
    type: 'quantile',
    step: 5,
    spec: '{}'
  })
  const dataTable = ref<DataTable>({ fields: [], items: [] })
  const regionWarnings = ref(new Set() as Set<number>)
  const regionData = ref([] as Array<{ [key: string]: any }>)

  return {
    title,
    useInset,
    currentColorCol,
    cartoColorScheme,
    choroSettings,
    dataTable,
    regionWarnings,
    regionData
  }
})
