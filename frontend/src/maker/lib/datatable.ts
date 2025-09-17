import type { FeatureCollection } from 'geojson'
import * as d3 from 'd3'
import { toRaw } from 'vue'

import * as config from '@/common/lib/config'
import * as util from '../lib/util'

import { useProjectStore } from '../stores/project'
import type { KeyValueArray, DataTable } from './interface'

export function reset() {
  const store = useProjectStore()
  store.useInset = false
  if (store.cartoColorScheme === 'custom') store.cartoColorScheme = 'pastel1'
  store.dataTable.items = []
  store.dataTable.fields = [
    {
      label: 'Region',
      name: 'Region',
      type: 'text',
      editable: false,
      show: true
    },
    { label: 'RegionMap', name: 'RegionMap', type: 'text', editable: false, show: false },
    { label: 'RegionLabel', name: 'RegionLabel', type: 'text', editable: true, show: true },
    { label: 'Color', name: 'Color', type: 'color', editable: true, show: false },
    { label: 'ColorGroup', name: 'ColorGroup', type: 'number', editable: false, show: false },
    {
      label: 'Inset',
      name: 'Inset',
      type: 'select',
      options: config.OPTIONS_INSET,
      editable: true,
      show: false
    },
    {
      label: 'Geographic Area',
      name: 'Geographic Area',
      unit: 'sq. km',
      type: 'text',
      editable: true,
      editableHead: true,
      show: false
    }
  ]
  store.regionData = []
  store.regionWarnings.clear()
}

export async function initDataTableWGeojson(
  geojsonData: FeatureCollection,
  geojsonRegionCol: string,
  csvFile = ''
) {
  reset()

  // Transform geojson to data fields
  let geoProperties = util.propertiesToArray(geojsonData)
  if (geoProperties.length === 0) return

  geoProperties = util.deleteKeysInArray(geoProperties, 'cartogram_id')

  const areaKey = Object.keys(geoProperties[0]).find((key) => key.startsWith('Geographic Area'))
  if (areaKey) geoProperties = util.renameKeyInArray(geoProperties, areaKey, 'Geographic Area')
  geoProperties = util.renameKeyInArray(geoProperties, geojsonRegionCol, 'Region')
  geoProperties = util.copyKeyInArray(geoProperties, 'Region', 'RegionMap')
  geoProperties = util.arrangeKeysInArray(geoProperties, [...config.RESERVE_FIELDS])
  geoProperties.sort((a, b) => a.Region.localeCompare(b.Region))

  initDataTableWArray(geoProperties)

  // Immediately populate data if a CSV file is supplied
  if (csvFile) {
    await d3
      .csv(csvFile)
      .then((csvData) => {
        if (!csvData || !Array.isArray(csvData)) {
          console.error('Invalid CSV data')
          return
        }
        updateDataTable(csvData)
      })
      .catch((error) => {
        console.error('Error loading CSV:', error)
      })
  }
}

export function initDataTableWArray(data: KeyValueArray, isReplace = true) {
  const store = useProjectStore()
  data = util.filterKeyValueInArray(data, config.RESERVE_FIELDS)

  // Update data
  let keys = [] as Array<string>
  if (isReplace) {
    store.dataTable.items = data
    keys = Object.keys(store.dataTable.items[0])
  } else {
    const result = util.updateObjInArray(store.dataTable.items, data, 'Region')
    keys = result.fields
    store.dataTable.items = result.updated
    store.regionData = result.unmatched
    if (result.unupdatedIndex.length > 0) store.regionWarnings = new Set(result.unupdatedIndex)
    else store.regionWarnings = new Set()
  }

  // Re-populate headers
  for (let i = 0; i < keys.length; i++) {
    if (!config.RESERVE_FIELDS.includes(keys[i])) {
      let [fieldname, unit] = util.getNameUnit(keys[i])
      fieldname = util.sanitizeFilename(fieldname)
      const label = unit ? fieldname + ' (' + unit + ')' : fieldname
      if (label !== keys[i]) {
        store.dataTable.items = util.renameKeyInArray(toRaw(store.dataTable.items), keys[i], label)
        store.regionData = util.renameKeyInArray(toRaw(store.regionData), keys[i], label)
      }

      store.dataTable.fields.push({
        label: label,
        name: fieldname,
        unit: unit,
        type: 'number',
        vis: '',
        editable: true,
        editableHead: true,
        show: true
      })
    }
  }
}

export function updateDataTable(csvData: KeyValueArray) {
  if (csvData.length === 0) {
    reset()
    return
  }
  const store = useProjectStore()

  // Save visType of each column
  const visTypes = getVisTypes(store.dataTable)

  const areaKey = Object.keys(csvData[0]).find((key) => key.startsWith('Geographic Area'))
  if (areaKey) {
    const [, unit] = util.getNameUnit(areaKey)
    store.dataTable.fields[config.COL_AREA].unit = unit
    csvData = util.renameKeyInArray(csvData, areaKey, 'Geographic Area')
  }

  // Remove other columns excepts the reserved fields
  store.dataTable.items = util.filterKeyValueInArray(
    store.dataTable.items,
    config.RESERVE_FIELDS,
    null
  )
  store.dataTable.fields.splice(config.NUM_RESERVED_FILEDS)

  store.dataTable.fields[config.COL_COLOR].show = csvData[0].hasOwnProperty('Color')
  store.dataTable.fields[config.COL_INSET].show = csvData[0].hasOwnProperty('Inset')
  initDataTableWArray(csvData, false)

  // Restore visType of each column
  store.dataTable.fields = assignVisTypes(store.dataTable, visTypes)

  store.cartoColorScheme = store.dataTable.fields[config.COL_COLOR].show
    ? 'custom'
    : store.cartoColorScheme
  store.useInset = store.dataTable.fields[config.COL_INSET].show
}

export function assignVisTypes(dataTable: DataTable, types: Record<string, string>) {
  return dataTable.fields.map((item) => ({
    ...item,
    vis: types[item.label] ?? item.vis // keep old vis if not in map
  }))
}

// Get the mapping of column name and visualization type {'column_name': 'visualization_type'}
export function getVisTypes(dataTable: DataTable): Record<string, string> {
  return dataTable.fields.reduce<Record<string, string>>((acc, item) => {
    if (item.vis && item.vis !== 'none') {
      acc[item.label] = item.vis
    }
    return acc
  }, {})
}

// Get the column names with specified visualization type
export function getColsByVisType(dataTable: DataTable, type: string): string[] {
  return dataTable.fields.filter((item) => item.vis === type).map((item) => item.label)
}

export function updateChoroSpec(): void {
  const store = useProjectStore()

  // Do not override spec if the user is in advance mode
  if (store.choroSettings.isAdvanceMode) return

  let cols = getColsByVisType(store.dataTable, 'choropleth')
  let jsonObj = { scales: [] as Array<any>, legend_titles: {} as { [key: string]: string } }
  for (let i = 0; i < cols.length; i++) {
    jsonObj.scales.push({
      name: cols[i],
      type: store.choroSettings.type,
      domain: { data: 'source_csv', field: cols[i] },
      range: { scheme: store.choroSettings.scheme, count: store.choroSettings.step }
    })

    jsonObj.legend_titles[cols[i]] = util.getNameUnitScale(
      cols[i],
      store.choroSettings.type,
      store.choroSettings.step
    )
  }
  store.choroSettings.spec = JSON.stringify(jsonObj, null, 2)
}
