var secundariaPath = "/Users/navirami/Desktop/pedido secundaria/";
var outputPath = "/Users/navirami/Desktop/pedidos/reconocimientos_secundaria/";

// All unique student photos (from all folders)
var students = [
    "4x6/aldo-paquete1.jpg",
    "6x12/angel-paquete2.jpg",
    "4x6/arisbeth-paquete1.jpg",
    "6x12/axel-paquete2.jpg",
    "6x12/camila-paquete2.jpg",
    "6x12/cesar-paquete2.jpg",
    "6x12/delmar-paquete2.jpg",
    "4x6/diana-paquete1.jpg",
    "4x6/jorge-paquete1.jpg",
    "6x12/karen-paquete2.jpg",
    "4x6/karlaaracely-paquete1.jpg",
    "4x6/karlavaleria-paquete1.jpg",
    "6x12/luisadrian-paquete2.jpg",
    "4x6/luisartemio-paquete1.jpg",
    "6x12/luisgustavo-paquete2.jpg",
    "6x12/maite-paquete2.jpg",
    "6x12/mariajose-paquete2.jpg",
    "6x12/nahomi-paquete2.jpg",
    "6x12/valeria-paquete2.jpg",
    "4x6/veronica-paquete1.jpg",
    "4x6/ximena-paquete1.jpg",
    "6x12/ximenasolail-paquete2.jpg",
    "4x6/yatziri-paquete1.jpg"
];

var refLeft = 0.6265;
var refTop = 1.2785;
var errors = "";

// Create output folder if needed
var outFolder = Folder(outputPath);
if (!outFolder.exists) outFolder.create();

// Get current open PSD path (to reopen after each save)
var templateFile = app.activeDocument.fullName;

for (var s = 0; s < students.length; s++) {
    var relPath = students[s];
    var shortName = relPath.substring(relPath.lastIndexOf("/") + 1).replace(".jpg", "");

    var mainDoc = app.activeDocument;

    // Clean: keep only "platilla" and "Fondo"
    for (var i = mainDoc.layers.length - 1; i >= 0; i--) {
        var ln = mainDoc.layers[i].name;
        if (ln != "platilla" && ln != "Fondo") {
            mainDoc.layers[i].remove();
        }
    }

    // Open student photo
    var photoFile = File(secundariaPath + relPath);
    if (!photoFile.exists) {
        // Try other folders
        var found = false;
        var folders = ["4x6", "6x8", "6x12", "4x6 textura piel", "6x8 textura piel", "23 6x12 textura piel"];
        var fileName = relPath.substring(relPath.lastIndexOf("/") + 1);
        for (var f = 0; f < folders.length; f++) {
            var testFile = File(secundariaPath + folders[f] + "/" + fileName);
            if (testFile.exists) {
                photoFile = testFile;
                found = true;
                break;
            }
        }
        if (!found) {
            errors += shortName + ": no photo found\n";
            continue;
        }
    }

    var tempDoc = open(photoFile);
    tempDoc.selection.selectAll();
    tempDoc.selection.copy();
    tempDoc.close(SaveOptions.DONOTSAVECHANGES);

    // Paste into main doc
    app.activeDocument = mainDoc;
    mainDoc.paste();
    var newLayer = mainDoc.activeLayer;
    newLayer.name = "foto";

    // Move below "platilla"
    for (var i = 0; i < mainDoc.layers.length; i++) {
        if (mainDoc.layers[i].name == "platilla") {
            newLayer.move(mainDoc.layers[i], ElementPlacement.PLACEAFTER);
            break;
        }
    }

    // Re-find and position
    for (var i = 0; i < mainDoc.layers.length; i++) {
        if (mainDoc.layers[i].name == "foto") {
            newLayer = mainDoc.layers[i];
            break;
        }
    }
    var b = newLayer.bounds;
    var dx = refLeft - b[0].value;
    var dy = refTop - b[1].value;
    if (Math.abs(dx) > 0.001 || Math.abs(dy) > 0.001) {
        newLayer.translate(UnitValue(dx, "cm"), UnitValue(dy, "cm"));
    }

    // Save as JPG
    var jpgFile = File(outputPath + shortName + ".jpg");
    var jpgOpt = new JPEGSaveOptions();
    jpgOpt.quality = 12;
    mainDoc.saveAs(jpgFile, jpgOpt, false);

    // Close JPG and reopen PSD template
    mainDoc.close(SaveOptions.DONOTSAVECHANGES);
    open(templateFile);
}

if (errors.length > 0) {
    alert("Listo con errores:\n" + errors);
} else {
    alert("Listo! " + students.length + " reconocimientos de secundaria");
}
