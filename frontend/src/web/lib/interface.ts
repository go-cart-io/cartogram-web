export interface DataTable {
  fields: Array<{
    key: string
    label: string
    editable: boolean
    type?: string
    headerEditable?: boolean
  }>
  items: { [key: string]: any }
}

export interface ChartDataItem {
  label: string
  value: number
  color: string
  abbreviation: string
  name: string
}
