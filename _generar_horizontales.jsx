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
        if (txt.indexOf("CARLOS") >= 0) {
            nameLayer = doc.layers[i];
            break;
        }
    }
}

if (!nameLayer) {
    alert("No se encontró la capa del nombre");
} else {
    var nombres = [
        "CARLOS ARMANDO ACUÑA VÁZQUEZ",
        "NOÉ SEBASTIÁN AYALA CANCINO",
        "SAMANTHA BELÉN CONDE LÓPEZ",
        "MADAY DANAE COUTIÑO MONTERO",
        "AZUL CONSTANZA CUESTA NÚÑEZ",
        "EMMANUEL MARTÍNEZ DÍAZ",
        "LUIS GERARDO NARVÁEZ ESPINOSA",
        "IAN GADDIEL RUIZ RAMÍREZ",
        "HORACIO SOLÍS SERRANO"
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
    }
    
    nameLayer.textItem.contents = nombres[0];
    nameLayer.name = nombres[0];
    
    alert("Listo! Se generaron " + nombres.length + " placas horizontales");
}