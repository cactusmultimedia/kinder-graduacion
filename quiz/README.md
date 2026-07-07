# Evaluación «¿Cómo aprendo?» · Trimestre 2

Quiz interactivo para GitHub Pages que envía respuestas a Google Sheets vía Apps Script.

## Archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Quiz autónomo (vanilla JS, sin dependencias) |
| `apps-script.gs` | Código para Google Apps Script (web app) |

---

## 1. Desplegar el quiz en GitHub Pages

1. Sube `index.html` a un repo de GitHub (puede estar en la raíz o en una subcarpeta).
2. Ve a **Settings > Pages** y elige **Deploy from a branch** → `main` / `docs` o la carpeta que uses.
3. El quiz quedará disponible en `https://<usuario>.github.io/<repo>/` (o la ruta que corresponda).

Alternativa: usa `npx gh-pages -d .` si prefieres deploy desde CLI.

---

## 2. Conectar Google Apps Script (la base de datos)

### Crear el script

1. Ve a [script.google.com](https://script.google.com) y crea un proyecto nuevo.
2. Copia el contenido de `apps-script.gs` en el editor `Code.gs`.
3. Crea o abre el Google Sheet donde quieres las respuestas. Copia su URL.
4. En Apps Script, ve a **Configuración del proyecto** y marca **Mostrar "archivo de manifiesto" en el editor**.
5. Abre `appsscript.json` y agrega el scope de Sheets:
   ```json
   {
     "timeZone": "America/Mexico_City",
     "dependencies": {},
     "exceptionLogging": "STACKDRIVER",
     "oauthScopes": [
       "https://www.googleapis.com/auth/spreadsheets",
       "https://www.googleapis.com/auth/script.external_request"
     ]
   }
   ```
6. En el editor, llama a `SpreadsheetApp.openByUrl("URL_DE_TU_SHEET")` en lugar de usar la hoja activa, **o** simplemente crea el script *desde* la hoja (Extensions > Apps Script) — así se vinculan automáticamente.

### Publicar como web app

1. **Implementar > Nueva implementación > App web**
2. Configura:
   - **Ejecutar como**: Yo (tu cuenta)
   - **Acceso**: Cualquier usuario (incluso anónimo)
3. Implementa y **copia la URL** (termina en `/exec`).
4. Pega esa URL en `index.html` dentro de la variable `SCRIPT_URL` (línea ~310):
   ```js
   var SCRIPT_URL = "https://script.google.com/macros/s/.../exec";
   ```
5. Vuelve a subir `index.html` al repo. GitHub Pages la actualiza automáticamente.

> **Nota:** La primera vez que se ejecute, Google pedirá autorización. Como el acceso es "Cualquier usuario", los alumnos no necesitan cuenta de Google para enviar.

---

## 3. Analizar respuestas con pandas

```python
import pandas as pd
import matplotlib.pyplot as plt

# Leer hoja
SHEET_ID = "1ABC123..."  # ID de tu Google Sheet
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Respuestas"
df = pd.read_csv(url)

# Limpieza
df.columns = df.columns.str.strip()
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Vista rápida
print(df.shape)
print(df['grupo'].value_counts())

# Ejemplo: estilos de aprendizaje
estilos = df['estilos'].str.get_dummies(sep=' | ')
top_estilos = estilos.sum().sort_values(ascending=False)

top_estilos.plot(kind='barh', title='Actividades preferidas para aprender')
plt.tight_layout()
plt.show()

# Guardar resumen
df.describe(include='object').to_csv('resumen_evaluacion.csv')
```

### Notebook sugerido

```python
# Análisis por grupo
for grupo in df['grupo'].unique():
    sub = df[df['grupo'] == grupo]
    print(f"\n=== {grupo} (n={len(sub)}) ===")
    print(sub[['p1','p2','p3_modo']].apply(pd.Series.value_counts))
```

---

## 4. Fallback sin conexión

Si el servidor de Apps Script no responde (red del lab lenta, restricciones), el quiz descarga automáticamente un respaldo `.json` y le pide al alumno que se lo entregue al profe. Esa colección de `.json` se puede juntar después con:

```python
import json, glob

rows = []
for f in glob.glob('respuesta_*.json'):
    with open(f) as fh:
        rows.append(json.load(fh))
df = pd.DataFrame(rows)
```
