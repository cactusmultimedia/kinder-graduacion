/**
 * Recibe las respuestas de la evaluación y las guarda en la hoja "Respuestas".
 * Implementar como: Implementar > Nueva implementación > App web
 *   - Ejecutar como: Yo (tu cuenta)
 *   - Acceso: Cualquier usuario
 * Copia la URL que termina en /exec y pégala en index.html (SCRIPT_URL).
 */

var CAMPOS = ["timestamp","nombre","grupo","p1","p2","p3_modo","p3_porque","p4","p5","p6","p7",
  "q8","q9","q10","q11","q12","q13","q14","estilos","t1","t2","t3","t4","t5","t6","t7",
  "ref_sano","ref_familia","ref_cambio","actitudes"];

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName('Respuestas') || ss.insertSheet('Respuestas');

    if (sheet.getLastRow() === 0) {
      sheet.appendRow(CAMPOS);
    }

    var data = JSON.parse(e.postData.contents);
    var row = CAMPOS.map(function(k){ return data[k] !== undefined ? data[k] : ''; });
    row[0] = new Date(); // timestamp real del servidor
    sheet.appendRow(row);

    return ContentService
      .createTextOutput(JSON.stringify({ok:true}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ok:false, error:String(err)}))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

// Prueba opcional: abre la URL /exec en el navegador para confirmar que vive.
function doGet() {
  return ContentService.createTextOutput('Evaluación activa. Usa POST.');
}
