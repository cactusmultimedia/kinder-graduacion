---
tipo: procedimiento
proyecto: Graduaciones
fecha: 2026-06-30
---

# Exportar agradecimientos desde PSD (por capas de alumno)

## Contexto
PSD: `agradecieminto 2026` (el typo está en el nombre original)
Capas: Capa 1 (overlay) + capas de alumnos (2-25) + Fondo

## Procedimiento (AppleScript → ExtendScript)

```applescript
tell application "Adobe Photoshop 2024"
    do javascript "
var doc = app.activeDocument;
var outFolder = \"/Users/navirami/Desktop/pedidos/secundaria/agradecimientos/\";
var so = new JPEGSaveOptions();
so.quality = 12;

// layers[0]=Capa1, layers[1]-[24]=students, layers[25]=Fondo
for (var i = 1; i <= 24; i++) {
    for (var j = 1; j <= 24; j++) {
        doc.layers[j].visible = false;
    }
    doc.layers[i].visible = true;
    doc.layers[0].visible = true;

    var f = new File(outFolder + doc.layers[i].name + \".jpg\");
    doc.saveAs(f, so, true, Extension.LOWERCASE);
}
"
end tell
```

## Notas importantes
- Crear carpeta de salida antes (`mkdir -p`)
- ExtendScript `layers[]` es 0-indexed (layers[0] = capa más arriba en el panel)
- `saveAs` con `JPEGSaveOptions` funciona bien; NO usar `make new JPEG save options` (falla)
- Calidad 12, progressive, con perfil de color

## Destino
`~/Desktop/pedidos/secundaria/agradecimientos/` — 24 archivos JPG
