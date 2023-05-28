import * as XLSX from 'xlsx'

export function clearFileInput(ctrl: HTMLInputElement): void {
  try {
    ctrl.value = null
  } catch (ex) {}
  if (ctrl.value) {
    ctrl.parentNode.replaceChild(ctrl.cloneNode(true), ctrl)
  }
}

export function convertExcelToCSV(excel_file: File) {
  return new Promise((resolve, reject) => {
    let reader = new FileReader()
    try {
      reader.onloadend = function (e) {
        var data = e.target.result
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
  document.getElementById(button_id).onclick = function () {
    var icon_id = button_id + '-icon'
    navigator.clipboard.writeText(message)
    document.getElementById(icon_id).setAttribute('src', 'static/img/clipboard-check.svg')

    setTimeout(function () {
      document.getElementById(icon_id).setAttribute('src', 'static/img/clipboard.svg')
    }, 2000)
  }
}
