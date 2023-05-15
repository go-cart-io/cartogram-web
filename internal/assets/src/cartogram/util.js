import * as XLSX from 'xlsx/xlsx.mjs';

export function clearFileInput(ctrl) {
    try {
      ctrl.value = null;
    } catch(ex) { }
    if (ctrl.value) {
      ctrl.parentNode.replaceChild(ctrl.cloneNode(true), ctrl);
    }
 }

export function convertExcelToCSV(excel_file) {
  return new Promise((resolve, reject) => {
      let reader = new FileReader();
      try {
          reader.onloadend = function(e) {
              var data = e.target.result;
              var wb = XLSX.read(data, {type: 'binary'});
              var ws = wb.Sheets[wb.SheetNames[0]];
              var csv = XLSX.utils.sheet_to_csv(ws);
              csv = new Blob([csv], {type: "text/csv;charset=utf-8"});
              resolve(csv);
          }
      }
      catch(e) {
          console.log(e);
          reject(Error('Given Excel file is corrupted.'));
      }
      reader.readAsBinaryString(excel_file);
  })
}

export function addClipboard (button_id, message) {

  $("#" + button_id).tooltip({
      trigger : 'hover',
    })
    
  document.getElementById(button_id).onclick = function() {
      var icon_id = button_id + "-icon";
      navigator.clipboard.writeText(message);
      document.getElementById(icon_id).src = 'static/clipboard-check.svg';
      $("#" + button_id)
      .attr('data-original-title', "Copied!")
      .tooltip('show');
      
      setTimeout(function() {
          document.getElementById(icon_id).src = 'static/clipboard.svg';
          $("#" + button_id)
          .attr('data-original-title', "Copy")
      }
      , 2000);
  };
}