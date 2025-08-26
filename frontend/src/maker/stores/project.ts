import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { DataTable } from '../lib/interface'

export const useProjectStore = defineStore('project', () => {
  const title = ref('')
  const useInset = ref(false)
  const cartoColorScheme = ref('pastel1')
  const choroSettings = ref({
    isAdvanceMode: false,
    scheme: 'blues',
    type: 'quantile',
    step: 5,
    spec: ''
  })
  const visTypes = ref({ cartogram: [], choropleth: [] } as { [key: string]: Array<string> })
  const dataTable = ref<DataTable>({ fields: [], items: [] })
  const regionWarnings = ref(new Set() as Set<number>)
  const regionData = ref([] as Array<{ [key: string]: any }>)

  function updateChoroSpec() {
    // Do not override spec if the user is in advance mode
    if (choroSettings.value.isAdvanceMode) return

    let jsonObj = { scales: [] as Array<any> }
    for (let i = 0; i < (visTypes.value['choropleth']?.length || 0); i++) {
      jsonObj.scales.push({
        name: visTypes.value['choropleth'][i],
        type: choroSettings.value.type,
        domain: { data: 'source_csv', field: visTypes.value['choropleth'][i] },
        range: { scheme: choroSettings.value.scheme, count: choroSettings.value.step }
      })
    }
    choroSettings.value.spec = JSON.stringify(jsonObj, null, 2)
  }

  return {
    title,
    useInset,
    cartoColorScheme,
    choroSettings,
    visTypes,
    dataTable,
    regionWarnings,
    regionData,
    updateChoroSpec
  }
})
