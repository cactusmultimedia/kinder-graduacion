#!/usr/bin/env python3
"""
duelo_velocidad.py — Solo los 3 ganadores. Razonamiento RAPIDO + latencia.
Mide quien tiene mejor conexion a servidores: repite cada reto N rondas
y saca latencia promedio, minima, maxima y consistencia (spread).
"""
import os
import re
import statistics
import shutil
import subprocess
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- CONFIG -----------------------------------------------------------
MODELOS = {
    "Big-Pickle":  "opencode/big-pickle",
    "DeepSeek-V4": "opencode/deepseek-v4-flash-free",
    "Nemotron-3":  "opencode/nemotron-3-ultra-free",
}
FLAGS_EXTRA = []
RONDAS = 3          # cuantas veces se repite cada reto (para medir consistencia)
STAGGER = 2.0       # anti-baneo (NO cuenta en la latencia medida)
TIMEOUT = 120

# Retos cortos: respuesta de 1 dato, para que el tiempo sea de conexion, no de texto
PRUEBAS = [
    {"prompt": ("Si 5 maquinas tardan 5 minutos en hacer 5 aparatos, cuanto "
                "tardan 100 maquinas en hacer 100 aparatos? Responde SOLO con "
                "el numero de minutos."),
     "substr": "5"},
    {"prompt": ("Una pluma y un cuaderno cuestan $1.10 en total. El cuaderno "
                "cuesta $1.00 mas que la pluma. Cuanto cuesta la pluma? "
                "Responde SOLO con la cantidad."),
     "substr": "0.05"},
    {"prompt": ("Que numero continua la serie 2, 6, 12, 20, 30? Responde SOLO "
                "con el numero."),
     "substr": "42"},
]
# ----------------------------------------------------------------------


def construir_cmd(model_id, prompt):
    return ["opencode", "run", "-m", model_id, *FLAGS_EXTRA, prompt]


def preguntar(nombre, model_id, prompt, retraso):
    if model_id == "MODELO_AQUI":
        return (nombre, "ERROR: falta el modelo", 0.0)
    time.sleep(retraso)           # stagger FUERA del cronometro
    cmd = construir_cmd(model_id, prompt)
    t0 = time.time()              # <-- aqui empieza la medicion real
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        dt = time.time() - t0
        if r.returncode != 0 or not r.stdout.strip():
            return (nombre, "ERROR", dt)
        return (nombre, r.stdout.strip(), dt)
    except subprocess.TimeoutExpired:
        return (nombre, "ERROR: timeout", time.time() - t0)
    except FileNotFoundError:
        return (nombre, "ERROR: no 'opencode' en PATH", 0.0)
    except Exception as e:
        return (nombre, f"ERROR: {e}", time.time() - t0)


def correr():
    # acumula por modelo: lista de latencias y de aciertos
    stats = {n: {"lat": [], "ok": 0, "tot": 0} for n in MODELOS}

    for ronda in range(1, RONDAS + 1):
        print(f"\n===== RONDA {ronda}/{RONDAS} =====")
        for prueba in PRUEBAS:
            with ThreadPoolExecutor(max_workers=len(MODELOS)) as ex:
                futuros = [ex.submit(preguntar, n, m, prueba["prompt"], i * STAGGER)
                           for i, (n, m) in enumerate(MODELOS.items())]
                resultados = [f.result() for f in futuros]
            for nombre, texto, dt in resultados:
                acierto = (not texto.startswith("ERROR")
                           and prueba["substr"].lower() in texto.lower())
                stats[nombre]["lat"].append(dt)
                stats[nombre]["tot"] += 1
                stats[nombre]["ok"] += int(acierto)
                print(f"  {nombre:12s} {dt:6.1f}s  {'OK' if acierto else 'X'}")

    # tabla final ordenada por latencia promedio (mas rapido = mejor conexion)
    filas = []
    for n, s in stats.items():
        lat = s["lat"] or [0]
        prom = statistics.mean(lat)
        spread = max(lat) - min(lat)
        filas.append((n, s["ok"], s["tot"], prom, min(lat), max(lat), spread))
    filas.sort(key=lambda f: f[3])  # por promedio

    lineas = [f"# Duelo VELOCIDAD (3 ganadores) - {datetime.now():%Y-%m-%d %H:%M}",
              f"_{RONDAS} rondas x {len(PRUEBAS)} retos = {RONDAS*len(PRUEBAS)} llamadas por modelo_", "",
              "| # | Modelo | Aciertos | Lat. prom | Min | Max | Spread (consistencia) |",
              "|---|---|---|---|---|---|---|"]
    print("\n===== RESULTADO FINAL (ordenado por rapidez) =====")
    for pos, (n, ok, tot, prom, mn, mx, sp) in enumerate(filas, 1):
        fila = f"| {pos} | {n} | {ok}/{tot} | {prom:.1f}s | {mn:.1f}s | {mx:.1f}s | {sp:.1f}s |"
        lineas.append(fila)
        print(f"  {pos}. {n:12s} prom={prom:5.1f}s  spread={sp:5.1f}s  aciertos={ok}/{tot}")

    lineas += ["", "_Menor latencia promedio = servidor mas rapido._",
               "_Menor spread = conexion mas estable (responde parejo)._"]
    archivo = f"velocidad_{datetime.now():%Y%m%d_%H%M%S}.md"
    with open(archivo, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))

    ruta_descargas = os.path.expanduser("~/Downloads")
    shutil.copy(archivo, ruta_descargas)
    print(f"\nGuardado en: {archivo}")
    print(f"Copiado a: {ruta_descargas}/{archivo}")


if __name__ == "__main__":
    correr()