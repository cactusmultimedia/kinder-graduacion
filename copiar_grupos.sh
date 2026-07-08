#!/bin/bash
SRC="/Users/navirami/Library/Mobile Documents/com~apple~CloudDocs/graduaciones 2026 /250D7100"
DST="/Users/navirami/Documents/archivado/galeria-secundaria"

# Map student names to folder numbers
declare -A MAP
MAP["ximena"]="21"
MAP["solai"]="22"        # Ximena Solail
MAP["cesar"]="6"
MAP["mariajose"]="17"
MAP["gustabo"]="15"      # Luis Gustavo
MAP["delmar"]="7"
MAP["maite"]="16"
MAP["yatziri"]="23"
MAP["eliu"]="4"          # Axel Eliu
MAP["jorge"]="9"
MAP["aracely"]="11"      # Karla Aracely
MAP["camila"]="5"
MAP["nahomi"]="18"
MAP["diana"]="8"
MAP["karlavaleria"]="12"

# "luis" alone -> ambiguous, need context
# "adrian" -> Luis Adrian (13)

for f in "$SRC"/*.JPG; do
    bname=$(basename "$f")
    # Remove extension
    name="${bname%.JPG}"
    
    # The pattern is: namesDSC_number or names.JPG
    # Extract the part before DSC_
    if [[ "$name" =~ DSC_ ]]; then
        names_part="${name%%DSC_*}"
    else
        names_part="$name"
    fi
    
    # Clean up: trim spaces, commas
    # Split by comma
    IFS=',' read -ra NAMES <<< "$names_part"
    
    # Determine which folders to copy to
    folders=""
    has_adrian=false
    has_luis=false
    has_gustabo=false
    
    for n in "${NAMES[@]}"; do
        n=$(echo "$n" | xargs)  # trim
        n_lower=$(echo "$n" | tr '[:upper:]' '[:lower:]')
        
        if [ "$n_lower" == "luis" ]; then
            has_luis=true
        elif [ "$n_lower" == "adrian" ]; then
            has_adrian=true
        elif [ "$n_lower" == "gustabo" ]; then
            has_gustabo=true
        fi
    done
    
    # Now process each name to get folder numbers
    for n in "${NAMES[@]}"; do
        n=$(echo "$n" | xargs)
        n_lower=$(echo "$n" | tr '[:upper:]' '[:lower:]')
        
        if [ "$n_lower" == "luis" ]; then
            if $has_adrian; then
                # luis + adrian in same photo -> luis = Luis Artemio (14)
                folders="$folders 14"
            elif $has_gustabo; then
                # luis + gustabo -> luis = Luis Artemio (14)
                folders="$folders 14"
            else
                # luis alone -> both Luis Adrian (13) and Luis Artemio (14)
                folders="$folders 13 14"
            fi
        elif [ "$n_lower" == "adrian" ]; then
            folders="$folders 13"  # Luis Adrian
        else
            folder="${MAP[$n_lower]}"
            if [ -n "$folder" ]; then
                folders="$folders $folder"
            fi
        fi
    done
    
    # Remove duplicates
    folders=$(echo "$folders" | tr ' ' '\n' | sort -nu | tr '\n' ' ')
    
    echo "=== $bname ==="
    echo "  Nombres: ${NAMES[*]}"
    echo "  Carpetas: $folders"
    
    for fol in $folders; do
        outname=$(echo "$bname" | sed 's/\.JPG$//' | sed 's/[ ,]//g')
        outname="grupo_${outname: -10}.jpg"
        mkdir -p "$DST/$fol"
        sips --resampleWidth 1200 "$f" --out "$DST/$fol/$outname" > /dev/null 2>&1
        echo "  → carpeta $fol/$outname"
    done
done

echo ""
echo "Listo!"
