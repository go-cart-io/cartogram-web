import type { StringObject } from '@/common/lib/interface'

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
