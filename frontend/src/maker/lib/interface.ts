import type { StringObject } from '@/common/interface'

export type VisualizationTypes = { [key: string]: Array<string> }

export type KeyValueArray = Array<{ [key: string]: any }>

export type DataTable = {
  fields: Array<{
    label: string
    name: string
    unit?: string
    type: string
    vis?: string
    options?: Array<{ text: string; value: string }>
    show: boolean
    editable: boolean
    editableHead?: boolean
  }>
  items: StringObject[]
}
