import * as d3 from 'd3'
import type { KeyValueArray, DataTable } from './interface'
import type { FeatureCollection, Feature } from 'geojson'

export async function readFile(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsBinaryString(file)
    reader.onload = () => resolve(<string>reader.result)
    reader.onerror = (error) => reject(error)
  })
}

export function generateShareKey(length: number): string {
  let result = Date.now().toString()
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const charactersLength = characters.length
  let counter = result.length
  while (counter < length) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength))
    counter += 1
  }
  return result
}

export function renameKeyInArray(
  data: KeyValueArray,
  oldKeyname: string,
  newKeyName: string
): KeyValueArray {
  return data.map((item) => {
    return Object.keys(item).reduce((accumulator: { [key: string]: any }, key: string) => {
      accumulator[key === oldKeyname ? newKeyName : key] = item[key]
      return accumulator
    }, {})
  })
}

export function addKeyInArray(data: KeyValueArray, keyName: string, defaultValue: any) {
  return data.map((item) => {
    if (!item.hasOwnProperty(keyName)) {
      return {
        ...item,
        [keyName]: defaultValue
      }
    }
    return item
  })
}

export function filterKeyValueInArray(
  data: KeyValueArray,
  except: Array<string>,
  allow: string | null = 'number'
): KeyValueArray {
  return data.map((item) => {
    return Object.keys(item).reduce((accumulator: { [key: string]: any }, key: string) => {
      if (except.includes(key)) accumulator[key] = item[key]
      else if (
        allow === 'number' &&
        (typeof item[key] === 'number' || !isNaN(parseFloat(item[key])))
      )
        accumulator[key] = parseFloat(item[key])
      return accumulator
    }, {})
  })
}

export function arrangeKeysInArray(
  data: KeyValueArray,
  templateKeys: Array<string>
): KeyValueArray {
  return data.map((item) => {
    const orderedKeys = [
      ...templateKeys,
      ...Object.keys(item).filter((key) => !templateKeys.includes(key))
    ]

    // Rebuild object with ordered keys
    return orderedKeys.reduce((orderedItem: { [key: string]: any }, key: string) => {
      if (key in item) orderedItem[key] = item[key]
      else orderedItem[key] = null
      return orderedItem
    }, {})
  })
}

export function mergeObjInArray(baseData: KeyValueArray, newData: KeyValueArray, mergeKey: string) {
  return baseData.map((item) => {
    const csvItems = newData.find((c) => c[mergeKey] === item[mergeKey])
    return csvItems ? { ...item, ...csvItems } : item
  })
}

export function tableToArray(dataTable: DataTable): KeyValueArray {
  var data = [] as KeyValueArray
  for (var i = 0; i < dataTable.items.length; i++) {
    data[i] = {}
    for (var j = 0; j < dataTable.fields.length; j++) {
      if (dataTable.fields[j].show || dataTable.fields[j].name === 'ColorGroup') {
        let newLabel = dataTable.fields[j].unit
          ? dataTable.fields[j].name + ' (' + dataTable.fields[j].unit + ')'
          : dataTable.fields[j].name
        data[i][newLabel] = dataTable.items[i][dataTable.fields[j].label]
      }
    }
  }
  return data
}

export function propertiesToArray(geojsonData: FeatureCollection): KeyValueArray {
  if (!geojsonData.features) return []

  return geojsonData.features.map((item: Feature) => {
    const { properties, ...rest } = item
    return properties ? properties : []
  }) as KeyValueArray
}

export function getNameUnit(label: string): [string, string] {
  let unitMatch = label.match(/\(([^)]+)\)$/)
  let unit = unitMatch ? unitMatch[1].trim() : ''
  let name = label.replace('(' + unit + ')', '').trim()
  return [name, unit]
}

export function filterGeoJSONProperties(
  geojson: FeatureCollection,
  fromProperties: Array<string>,
  toProperties: Array<string>
) {
  return {
    ...geojson,
    features: geojson.features.map((feature) => {
      let filteredProperties = {} as any
      for (let i = 0; i <= fromProperties.length; i++) {
        if (feature.properties?.hasOwnProperty(fromProperties[i])) {
          filteredProperties[toProperties[i]] = feature.properties[fromProperties[i]]
        }
      }
      return {
        ...feature,
        properties: filteredProperties
      }
    })
  }
}

export async function getGeneratedCSV(dataTable: DataTable, isGetFile = false) {
  var data = tableToArray(dataTable)
  var csv = d3.csvFormat(data)
  if (!isGetFile) return csv

  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'data.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
