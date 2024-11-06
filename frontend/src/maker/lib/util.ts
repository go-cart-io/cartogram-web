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

export function filterNumberInArray(data: KeyValueArray, except: Array<string>): KeyValueArray {
  return data.map((item) => {
    return Object.keys(item).reduce((accumulator: { [key: string]: any }, key: string) => {
      if (except.includes(key)) accumulator[key] = item[key]
      else if (typeof item[key] === 'number' || !isNaN(parseFloat(item[key])))
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

export function tableToArray(dataTable: DataTable): KeyValueArray {
  var data = [] as KeyValueArray
  for (var i = 0; i < dataTable.items.length; i++) {
    data[i] = {}
    for (var j = 0; j < dataTable.fields.length; j++) {
      if (dataTable.fields[j].show) {
        data[i][dataTable.fields[j].label] = dataTable.items[i][dataTable.fields[j].label]
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
