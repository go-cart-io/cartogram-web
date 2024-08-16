export function getTotalAreas(features: any): number {
  var area = 0
  features.forEach((feature: any) => {
    area += feature['Area']
  })

  return area
}

// TODO: Check NA strategy
export function getTotalAreasAndValuesForVersion(
  versionName: string,
  features: any,
  data: any
): [number, number] {
  var area = 0
  var sum = 0
  var na_names: Array<string> = []
  var na_areas: Array<number> = []

  data.forEach((row: any) => {
    if (
      row[versionName] &&
      row[versionName].toString() !== '' &&
      row[versionName].toString() !== 'NA'
    ) {
      let value = typeof row[versionName] === 'string' ? Number(row[versionName]) : row[versionName]
      sum += value
    } else {
      na_names.push(row['Region'])
    }
  })

  na_areas = Array(na_names.length)
  features.forEach((feature: any) => {
    let na_index = na_names.indexOf(feature['Region'])
    if (na_index > -1) na_areas[na_index] = feature['Area']
    else area += feature['Area']
  })

  const avg_density = sum / area

  na_areas.forEach(function (na_area) {
    sum += avg_density * na_area
    area += na_area
  })

  return [area, sum]
}

export const NICE_NUMBERS = [1, 2, 5, 10, 20, 50]
export function findNearestNiceNumber(value: number): [number, number] {
  let scaleNiceNumber = 99
  let scalePowerOf10 = Math.floor(Math.log10(value))

  // We find the "nice number" that is closest to valuePerSquare's
  const valueFirstNumber = value / Math.pow(10, scalePowerOf10)
  let valueDiff = Math.abs(valueFirstNumber - scaleNiceNumber)
  NICE_NUMBERS.forEach(function (n) {
    if (Math.abs(valueFirstNumber - n) < valueDiff) {
      valueDiff = Math.abs(valueFirstNumber - n)
      scaleNiceNumber = n
    }
  })

  return [scaleNiceNumber, scalePowerOf10]
}

export function getOriginalMatrix(): Array<Array<number>> {
  return [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1]
  ]
}

export function getScaleMatrix(x: number, y: number): Array<Array<number>> {
  return [
    [x, 0, 0],
    [0, y, 0],
    [0, 0, 1]
  ]
}

export function getRotateMatrix(degree: number): Array<Array<number>> {
  return [
    [Math.cos(degree), -Math.sin(degree), 0],
    [Math.sin(degree), Math.cos(degree), 0],
    [0, 0, 1]
  ]
}

export function getTranslateMatrix(x: number, y: number): Array<Array<number>> {
  return [
    [1, 0, x],
    [0, 1, y],
    [0, 0, 1]
  ]
}

export function multiplyMatrix(
  matrix1: Array<Array<number>>,
  matrix2: Array<Array<number>>
): Array<Array<number>> {
  if (matrix1.length !== 3 || matrix2.length !== 3) {
    throw new Error('Both matrices should be 3x3.')
  }

  const result = [
    [0, 0, 0],
    [0, 0, 0],
    [0, 0, 0]
  ]

  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      for (let k = 0; k < 3; k++) {
        result[i][j] += matrix1[i][k] * matrix2[k][j]
      }
    }
  }

  return result
}

export function addClipboard(button_id: string, message: string) {
  var icon_id = button_id + '-icon'
  navigator.clipboard.writeText(message)
  document.getElementById(icon_id)?.setAttribute('src', '/static/img/clipboard-check.svg')

  setTimeout(function () {
    document.getElementById(icon_id)?.setAttribute('src', '/static/img/clipboard.svg')
  }, 2000)
}

export function getGeojsonURL(currentMapName: string, stringKey: string, dataKey: string) {
  let baseURL =
    stringKey && stringKey !== ''
      ? '/static/userdata/' + stringKey + '/'
      : '/static/cartdata/' + currentMapName + '/'

  if (dataKey === 'Land Area.json')
    return '/static/cartdata/' + currentMapName + '/' + 'Original.json'
  else return baseURL + dataKey
}
