#!/usr/bin/env python3
"""
duelo_oc.py — Duelo de modelos por OPENCODE, 5 retos CABRONES + autocalificacion dura.
Corre:  opencode run -m <modelo> "<prompt>"   por cada modelo.
Chequeos: substr / palabras / cadena / autoconteo / sin-letra. Exporta a .md.
"""
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- CONFIG -----------------------------------------------------------
MODELOS = {
    "DeepSeek-V4": "opencode/deepseek-v4-flash-free",
    "Big-Pickle": "opencode/big-pickle",
    "Mimo-v2.5": "opencode/mimo-v2.5-free",
    "North-Mini": "opencode/north-mini-code-free",
    "GLM-4.5-Flash": "zai/glm-4.5-flash",
    "GLM-4.7-Flash": "zai/GLM-4.7-Flash",
    "Nemotron-3": "opencode/nemotron-3-ultra-free",
}
FLAGS_EXTRA = []
STAGGER = 3.0     # anti-baneo
TIMEOUT = 240

PRUEBAS = [
    {   # 1. RAZONAMIENTO TEMPORAL encadenado (antier lunes -> pasado man~ana = viernes)
        "prompt": ("Si antier fue lunes, que dia sera pasado man~ana? "
                   "Responde con el dia y explica el encadenado paso a paso."),
        "substr": "viernes",
    },
    {   # 2. AUTORREFERENCIA: el numero que diga debe igualar las palabras de su respuesta
        "prompt": ("Cuantas palabras tiene tu respuesta a esta pregunta? "
                   "Responde SOLO con el numero, y tiene que ser exacto."),
        "autoconteo": True,
    },
    {   # 3. CADENA: cada palabra empieza con la ultima letra de la anterior; 12 palabras; desierto
        "prompt": ("Escribe una frase de EXACTAMENTE 12 palabras sobre el desierto "
                   "donde cada palabra empiece con la ultima letra de la palabra "
                   "anterior (cadena). Devuelve SOLO la frase."),
        "cadena": True,
        "palabras_exactas": 12,
    },
    {   # 4. CODIGO: mutable default arg (el bug famoso). f(1)->[1], f(2)->[1, 2]
        "prompt": ("Que imprime EXACTAMENTE este codigo Python? Responde SOLO "
                   "con las dos lineas de salida:\n"
                   "def f(x, l=[]):\n    l.append(x)\n    return l\n"
                   "print(f(1))\nprint(f(2))"),
        "substr": "[1, 2]",
    },
    {   # 5. TRAMPA LOGICA: 3 hermanas, cada una tiene 'un hermano' (compartido) -> 4 hijos
        "prompt": ("En una familia hay 3 hermanas. Cada una de las hermanas tiene "
                   "un hermano. Cuantos hijos hay en total en la familia? "
                   "Responde con el numero y el por que."),
        "substr": "4",
    },
]
# ----------------------------------------------------------------------


def construir_cmd(model_id, prompt):
    return ["opencode", "run", "-m", model_id, *FLAGS_EXTRA, prompt]


def preguntar(nombre, model_id, prompt, retraso):
    if model_id == "MODELO_AQUI":
        return (nombre, "ERROR: falta el modelo (usa `opencode models`)", 0.0)
    time.sleep(retraso)
    cmd = construir_cmd(model_id, prompt)
    print(f"  -> {nombre}: {' '.join(cmd[:-1])} \"...\"")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        if r.returncode != 0:
            err = (r.stderr or r.stdout).strip()[:400]
            return (nombre, f"ERROR (exit {r.returncode}): {err}", time.time() - t0)
        salida = r.stdout.strip()
        if not salida:
            return (nombre, "ERROR: salida vacia", time.time() - t0)
        return (nombre, salida, time.time() - t0)
    except subprocess.TimeoutExpired:
        return (nombre, f"ERROR: timeout >{TIMEOUT}s", time.time() - t0)
    except FileNotFoundError:
        return (nombre, "ERROR: 'opencode' no esta en el PATH", 0.0)
    except Exception as e:
        return (nombre, f"ERROR: {type(e).__name__}: {e}", time.time() - t0)


def _cadena_ok(texto):
    pal = re.findall(r"[a-záéíóúñü]+", texto.lower())
    if len(pal) < 2:
        return False
    return all(pal[i][0] == pal[i - 1][-1] for i in range(1, len(pal)))


def _autoconteo_ok(texto):
    nums = re.findall(r"\d+", texto)
    if not nums:
        return False
    return int(nums[0]) == len(texto.split())


def calificar(texto, prueba):
    n = len(texto.split())
    if texto.startswith("ERROR"):
        return ("ERROR", n)
    notas = []
    if "substr" in prueba:
        ok = prueba["substr"].lower() in texto.lower()
        notas.append("OK substr" if ok else "FALLA substr")
    if "palabras_exactas" in prueba:
        obj = prueba["palabras_exactas"]
        notas.append("OK pal" if n == obj else f"FALLA pal ({n}!={obj})")
    if "cadena" in prueba:
        notas.append("OK cadena" if _cadena_ok(texto) else "FALLA cadena")
    if "autoconteo" in prueba:
        notas.append("OK autoconteo" if _autoconteo_ok(texto) else "FALLA autoconteo")
    if "sin_letra" in prueba:
        c = prueba["sin_letra"].lower()
        notas.append(f"FALLA tiene-{c}" if c in texto.lower() else f"OK sin-{c}")
    return (" ".join(notas) if notas else "-", n)


def correr():
    lineas = [f"# Duelo CABRON por OpenCode - {datetime.now():%Y-%m-%d %H:%M}", ""]
    for prueba in PRUEBAS:
        print("\n" + "=" * 72)
        print("PROMPT:", prueba["prompt"][:80], "...")
        print("=" * 72)
        lineas += ["", "## Prompt", "", f"> {prueba['prompt']}", "",
                   "| Modelo | Tiempo | Palabras | Marca |", "|---|---|---|---|"]
        with ThreadPoolExecutor(max_workers=len(MODELOS)) as ex:
            futuros = [ex.submit(preguntar, n, m, prueba["prompt"], i * STAGGER)
                       for i, (n, m) in enumerate(MODELOS.items())]
            resultados = [f.result() for f in futuros]
        resultados.sort(key=lambda r: r[2])
        for nombre, texto, segs in resultados:
            marca, n = calificar(texto, prueba)
            print(f"\n--- {nombre}  ({segs:.1f}s - {n} pal - {marca}) ---")
            print(texto)
            lineas.append(f"| {nombre} | {segs:.1f}s | {n} | {marca} |")
            lineas += ["", f"<details><summary>{nombre}</summary>", "",
                       texto, "", "</details>", ""]
    archivo = f"duelo_oc_{datetime.now():%Y%m%d_%H%M%S}.md"
    with open(archivo, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print(f"\nGuardado en: {archivo}")

    ruta_descargas = os.path.expanduser("~/Downloads")
    shutil.copy(archivo, ruta_descargas)
    print(f"Copiado a: {ruta_descargas}/{archivo}")


if __name__ == "__main__":
    correr()