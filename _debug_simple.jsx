var doc = app.activeDocument;
var f = File("/Users/navirami/Desktop/pedido kinder/6x8/samantha-paquete2.jpg");
var txt = "File exists: " + f.exists + "\n";
txt += "File path: " + f.fsName + "\n";

// Test: open, copy, close
var tempDoc = open(f);
txt += "Temp doc opened: " + tempDoc.name + "\n";
tempDoc.selection.selectAll();
tempDoc.selection.copy();
tempDoc.close(SaveOptions.DONOTSAVECHANGES);
txt += "Temp doc closed\n";

// Paste
app.activeDocument = doc;
doc.paste();
txt += "Pasted: " + doc.activeLayer.name + "\n";

// Save
var jpgFile = new File("/Users/navirami/Desktop/pedidos/reconocimientos/_DEBUG_TEST.jpg");
var jpgOpt = new JPEGSaveOptions();
jpgOpt.quality = 12;
doc.saveAs(jpgFile, jpgOpt, true);
txt += "Saved to: " + jpgFile.fsName + "\n";

var outFile = new File("/Users/navirami/Documents/archivado/_debug_test.txt");
outFile.encoding = "UTF-8";
outFile.open("w");
outFile.write(txt);
outFile.close();
alert(txt);