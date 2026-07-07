#!/bin/bash
SRC="/Users/navirami/Desktop/familia primria secundaria y prepa /secundaria familias"
DST="/Users/navirami/Documents/archivado/galeria-secundaria"

copy_and_resize() {
    local file="$1"
    local folder="$2"
    mkdir -p "$DST/$folder"
    sips --resampleWidth 1200 "$file" --out "$DST/$folder/familia.jpg" > /dev/null 2>&1
    echo "✓ $(basename "$file") → carpeta $folder/"
}

# Individual
copy_and_resize "$SRC/aldo.JPG" 1
copy_and_resize "$SRC/angel blanco.JPG" 2
copy_and_resize "$SRC/camila.JPG" 5
copy_and_resize "$SRC/cesar.JPG" 6
copy_and_resize "$SRC/delmar.JPG" 7
copy_and_resize "$SRC/diana.JPG" 8
copy_and_resize "$SRC/jorge.JPG" 9
copy_and_resize "$SRC/karen.JPG" 10
copy_and_resize "$SRC/aracely.JPG" 11
copy_and_resize "$SRC/karla valeria .JPG" 12
copy_and_resize "$SRC/luis artemio.JPG" 14
copy_and_resize "$SRC/maite.JPG" 16
copy_and_resize "$SRC/nahomi trujillo.JPG" 18
copy_and_resize "$SRC/valeria.JPG" 19
copy_and_resize "$SRC/veronica.JPG" 20
copy_and_resize "$SRC/ximena.JPG" 21
copy_and_resize "$SRC/ximena solai.JPG" 22
copy_and_resize "$SRC/yatziri.JPG" 23

# Group: adrian y gustabo → Luis Adrian (13) + Luis Gustavo (15)
copy_and_resize "$SRC/adrian y gustabo.JPG" 13
copy_and_resize "$SRC/adrian y gustabo.JPG" 15

echo ""
echo "Fotos sin match: abdel.JPG, eliu.JPG, DSC_1956.JPG"
echo "Faltan carpetas: 3 (Arisbeth), 4 (Axel), 17 (Maria Jose)"
