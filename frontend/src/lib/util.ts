import * as XLSX from 'xlsx'

export function convertExcelToCSV(excel_file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    let reader = new FileReader()
    try {
      reader.onloadend = function (e) {
        var data = e.target?.result
        var wb = XLSX.read(data, { type: 'binary' })
        var ws = wb.Sheets[wb.SheetNames[0]]
        var csv = XLSX.utils.sheet_to_csv(ws)
        var result = new Blob([csv], { type: 'text/csv;charset=utf-8' })
        resolve(result)
      }
    } catch (e) {
      console.log(e)
      reject(Error('Given Excel file is corrupted.'))
    }
    reader.readAsBinaryString(excel_file)
  })
}

export function addClipboard(button_id: string, message: string) {
  var icon_id = button_id + '-icon'
  navigator.clipboard.writeText(message)
  document.getElementById(icon_id)?.setAttribute('src', 'static/img/clipboard-check.svg')

  setTimeout(function () {
    document.getElementById(icon_id)?.setAttribute('src', 'static/img/clipboard.svg')
  }, 2000)
}

export function findNearestNiceNumber(value: number): [number, number] {
  let scaleNiceNumber = 99
  let scalePowerOf10 = Math.floor(Math.log10(value))

  // We find the "nice number" that is closest to valuePerSquare's
  const valueFirstNumber = value / Math.pow(10, scalePowerOf10)
  let valueDiff = Math.abs(valueFirstNumber - scaleNiceNumber)
  const niceNumbers = [1, 2, 5, 10]
  niceNumbers.forEach(function (n) {
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
