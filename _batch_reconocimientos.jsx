function sanitizeFilename(name) {
    var result = "";
    for (var i = 0; i < name.length; i++) {
        var c = name.charAt(i);
        if (c == " " || c == "/" || c == "\\" || c == ":") result += "_";
        else result += c;
    }
    return result;
}

var kinderPath = "/Users/navirami/Desktop/pedido kinder/";
var outputPath = "/Users/navirami/Desktop/pedidos/reconocimientos/";

var students = [
    ["SAMANTHA BELÉN CONDE LÓPEZ", "6x8/samantha-paquete2.jpg"],
    ["MADAY DANAE COUTIÑO MONTERO", "6x8/maday-paquete2.jpg"],
    ["EMMANUEL MARTÍNEZ DÍAZ", "6x8/emmanuel-paquete2.jpg"],
    ["LUIS GERARDO NARVÁEZ ESPINOSA", "6x8/luisgerardo-paquete2.jpg"],
    ["IAN GADDIEL RUIZ RAMÍREZ", "6x8/ian-paquete2.jpg"],
    ["HORACIO SOLÍS SERRANO", "6x8/horacio-paquete2.jpg"],
    ["MANUEL RAMÓN BASCOS LÓPEZ", "4x6/manuelramon-paquete1.jpg"],
    ["MÁXIMO DIONEY CAMACHO CRUZ", "4x6/maximo-paquete1.jpg"],
    ["MATÍAS FARID DOMÍNGUEZ HERNÁNDEZ", "4x6/farid-paquete1.jpg"],
    ["JUAN PABLO GÓMEZ TAHUAS", "4x6/juanpablo-paquete1.jpg"],
    ["MAXIMILIANO GUTIÉRREZ HERNÁNDEZ", "4x6/maximiliano-paquete1.jpg"],
    ["MARÍA VALENTINA MORALES HERNÁNDEZ", "4x6/mariavalentina-paquete1.jpg"],
    ["VALLOLET VICTORIA MORALES LÓPEZ", "4x6/vallolet-paquete1.jpg"],
    ["JUAN DIEGO QUIROZ SUÁREZ", "4x6/juandiego-paquete1.jpg"],
    ["IKER ALEXANDER RABASA CERVANTES", "4x6/iker-paquete1.jpg"],
    ["ISRAEL AGUSTÍN RAMÓN MEZA", "4x6/israelagustin-paquete1.jpg"],
    ["ÁNGEL CAMILO ZENTENO SANTIAGO", "4x6/angelcamilo-paquete1.jpg"]
];

var refLeft = 0.6265;
var refTop = 1.2785;
var errors = "";

for (var s = 0; s < students.length; s++) {
    var name = students[s][0];
    var relPath = students[s][1];
    
    // Make sure main doc is active and clean
    var mainDoc = app.activeDocument;
    
    // Ensure clean state: remove any extra layers from main doc
    var needsCleanup = false;
    for (var i = mainDoc.layers.length - 1; i >= 0; i--) {
        var ln = mainDoc.layers[i].name;
        if (ln != "platilla" && ln != "Fondo") {
            mainDoc.layers[i].remove();
            needsCleanup = true;
        }
    }
    
    // Open student photo
    var photoFile = File(kinderPath + relPath);
    if (!photoFile.exists) {
        var altPath = relPath.substring(0, relPath.lastIndexOf(".")) + "_copia2.jpg";
        photoFile = File(kinderPath + altPath);
        if (!photoFile.exists) {
            errors += name + ": no photo\n";
            continue;
        }
    }
    
    // Open photo and copy
    var tempDoc = open(photoFile);
    tempDoc.selection.selectAll();
    tempDoc.selection.copy();
    tempDoc.close(SaveOptions.DONOTSAVECHANGES);
    
    // Paste into main doc
    app.activeDocument = mainDoc;
    mainDoc.paste();
    var newLayer = mainDoc.activeLayer;
    newLayer.name = "foto";
    
    // Move below platilla
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
    
    // Save as JPG WITHOUT asCopy - this will save AND rename the doc
    var jpgFile = File(outputPath + sanitizeFilename(name) + ".jpg");
    var jpgOpt = new JPEGSaveOptions();
    jpgOpt.quality = 12;
    mainDoc.saveAs(jpgFile, jpgOpt, false);
    // Now mainDoc is a JPG file
    
    // Close the JPG to get back to the PSD template
    // The template should already be saved
    mainDoc.close(SaveOptions.DONOTSAVECHANGES);
    
    // Reopen the PSD template for next iteration
    var templateFile = File("/Users/navirami/Downloads/agradecieminto 2026.psd");
    if (templateFile.exists) {
        open(templateFile);
    } else {
        errors += name + ": template not found!\n";
        break;
    }
}

if (errors.length > 0) {
    alert("Con errores:\n" + errors);
} else {
    alert("Listo! " + students.length + " reconocimientos");
}