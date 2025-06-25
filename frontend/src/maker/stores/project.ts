import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { DataTable } from '../lib/interface'

export const useProjectStore = defineStore('project', () => {
  const title = ref('')
  const useInset = ref(false)
  const colorRegionScheme = ref('pastel1')
  const dataTable = ref<DataTable>({ fields: [], items: [] })

  return {
    title,
    useInset,
    colorRegionScheme,
    dataTable
  }
})
