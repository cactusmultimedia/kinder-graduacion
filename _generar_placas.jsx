function sanitizeFilename(name) {
    var result = "";
    for (var i = 0; i < name.length; i++) {
        var c = name.charAt(i);
        if (c == " " || c == "/" || c == "\\" || c == ":") {
            result += "_";
        } else {
            result += c;
        }
    }
    return result;
}

var doc = app.activeDocument;
var outputFolder = Folder("/Users/navirami/Desktop/pedidos/placas");

var nameLayer = null;
for (var i = 0; i < doc.layers.length; i++) {
    if (doc.layers[i].kind == LayerKind.TEXT) {
        var txt = doc.layers[i].textItem.contents;
        if (txt.indexOf("MANUEL") >= 0 && txt.indexOf("RAMÓN") >= 0) {
            nameLayer = doc.layers[i];
            break;
        }
    }
}

if (!nameLayer) {
    alert("No se encontró la capa del nombre");
} else {
    var nombres = [
        "MANUEL RAMÓN BASCOS LÓPEZ",
        "MÁXIMO DIONEY CAMACHO CRUZ",
        "MATÍAS FARID DOMÍNGUEZ HERNÁNDEZ",
        "JUAN PABLO GÓMEZ TAHUAS",
        "MAXIMILIANO GUTIÉRREZ HERNÁNDEZ",
        "MARÍA VALENTINA MORALES HERNÁNDEZ",
        "VALLOLET VICTORIA MORALES LÓPEZ",
        "JUAN DIEGO QUIROZ SUÁREZ",
        "IKER ALEXANDER RABASA CERVANTES",
        "ISRAEL AGUSTÍN RAMÓN MEZA",
        "ÁNGEL CAMILO ZENTENO SANTIAGO"
    ];

    for (var n = 0; n < nombres.length; n++) {
        var nombre = nombres[n];
        nameLayer.textItem.contents = nombre;
        nameLayer.name = nombre;
        
        var pngFile = new File(outputFolder + "/" + sanitizeFilename(nombre) + ".png");
        var pngOpt = new PNGSaveOptions();
        pngOpt.compression = 6;
        pngOpt.interlaced = false;
        doc.saveAs(pngFile, pngOpt, true);
        
        // Write progress marker
        var marker = new File(outputFolder + "/_progreso.txt");
        marker.encoding = "UTF-8";
        marker.open("w");
        marker.write("Generados: " + (n+1) + " de " + nombres.length);
        marker.close();
    }
    
    nameLayer.textItem.contents = nombres[0];
    nameLayer.name = nombres[0];
    
    alert("Listo! Se generaron " + nombres.length + " placas en: " + outputFolder.fsName);
}