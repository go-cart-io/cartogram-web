export type KeyValueArray = Array<{ [key: string]: any }>

export type DataTable = {
  fields: Array<{
    label: string
    type: string
    show: boolean
    editable: boolean
    required?: boolean
  }>
  items: Array<{ [key: string]: any }>
}
