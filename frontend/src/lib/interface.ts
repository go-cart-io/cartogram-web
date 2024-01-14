export interface Mappack {
  abbreviations: { [key: string]: string } // e.g. Alabama: 'AL'
  colors: { [key: string]: string } // e.g. id_1: '#7570b3'
  config: MapConfig
  griddocument: any
  labels: Labels
  [key: string]: any // map
}

/**
 * Configuration for a map. Some maps do not display properly without modification. This configuration information
 * allows us to draw maps properly by hiding certain polygons, and changing the order in which they are drawn.
 * @typedef {Object} MapConfig
 * @property {Array} dont_draw A list of polygon IDs not to draw
 * @property {Array} elevate A list of polygon IDs to draw after all others
 */
export interface MapConfig {
  dont_draw: Array<any>
  elevate: Array<any>
  data_names?: Array<string>
  label_size?: string
}

export interface PolygonToDraw {
  region_id: string
  polygon_id: string
  path: string
  color: string
  elevated: boolean
  value: string
}

/**
 * Extrema for a map
 */
export interface Extrema {
  min_x: number
  max_x: number
  min_y: number
  max_y: number
}

/**
 * Labels for a map version
 * @typedef {Object} Labels
 * @property {number} scale_x Horizontal scaling factor for all label coordinates
 * @property {number} scale_y Vertical scaling factor for all label coordinates
 * @property {Array<{x: number, y: number, text: string}>} labels Text labels
 * @property {Array<{x1: number, y1: number, x2: number, y2: number}>} lines Line labels
 */
export interface Labels {
  scale_x: number
  scale_y: number
  skipSVG: boolean | null
  labels: Array<{ x: number; y: number; text: string }>
  lines: Array<{ x1: number; y1: number; x2: number; y2: number }>
}

export interface Entry {
  name: string
  value: number
  unit: string
}

export interface DataTable {
  fields: Array<{
    key: string, label: string, editable: boolean, type?: string, headerEditable?: boolean
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
