export interface MapHandlers {
  [key: string]: { name: string; region_identifier: string }
}

export interface Entry {
  name: string
  value: number
  unit: string
}
