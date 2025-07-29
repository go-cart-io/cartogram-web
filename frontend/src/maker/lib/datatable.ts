import type { FeatureCollection } from 'geojson'
import * as d3 from 'd3'
import { toRaw } from 'vue'

import type { KeyValueArray } from './interface'
import * as config from '../../common/config'
import * as util from '../lib/util'
import { useProjectStore } from '../stores/project'

export function reset() {
  const store = useProjectStore()
  store.useInset = false
  store.dataTable.items = []
  store.dataTable.fields = [
    {
      label: 'Region',
      name: 'Region',
      type: 'text',
      editable: false,
      show: true
    },
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
  geoProperties = util.arrangeKeysInArray(geoProperties, [...config.RESERVE_FIELDS])
  geoProperties = util.addKeyInArray(geoProperties, '', 0)
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

function _getVisTypeForColumn(
  visTypes: { [key: string]: Array<string> },
  columnName: string
): string {
  for (const visType in visTypes) {
    if (Object.prototype.hasOwnProperty.call(visTypes, visType)) {
      const columns = visTypes[visType]
      if (columns.includes(columnName)) {
        return visType
      }
    }
  }
  return ''
}

export function initDataTableWArray(data: KeyValueArray, isReplace = true) {
  const store = useProjectStore()
  data = util.filterKeyValueInArray(data, config.RESERVE_FIELDS)

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
        vis: _getVisTypeForColumn(store.visTypes, keys[i]),
        editable: true,
        editableHead: true,
        show: true
      })
    }
  }
}

export function updateDataTable(csvData: KeyValueArray) {
  if (csvData.length === 0) return
  const store = useProjectStore()

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

  store.cartoColorScheme = store.dataTable.fields[config.COL_COLOR].show
    ? 'custom'
    : store.cartoColorScheme
  store.useInset = store.dataTable.fields[config.COL_INSET].show
}
