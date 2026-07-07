#!/usr/bin/env python3
"""
duelo_opencode.py — Compara modelos via CLI de opencode en paralelo.
"""
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Modelos disponibles en tu config opencode
MODELOS = {
    "DeepSeek-V4-Flash-Free": "opencode/deepseek-v4-flash-free",
    "Nemotron-3-Ultra-Free": "opencode/nemotron-3-ultra-free",
    "GLM-4.7-Flash (Z.ai)": "zai/GLM-4.7-Flash",
    "Mimo-v2.5-Free": "opencode/mimo-v2.5-free",
    "Big-Pickle": "opencode/big-pickle",
    "North-Mini-Code-Free": "opencode/north-mini-code-free",
}

PROMPTS = [
    "En un torneo todos juegan contra todos una vez. Hubo 21 partidos en "
    "total. ¿Cuántos jugadores hubo? Explica el porqué.",

    "Escribe un microrelato de EXACTAMENTE 50 palabras sobre un cactus que "
    "florece en el desierto. Tono melancólico.",
]


def preguntar(nombre, model_id, prompt):
    """Llama a `opencode run -m <model> <prompt>`. Devuelve (nombre, texto, segs)."""
    # Z.ai necesita la API key en el entorno
    env = os.environ.copy()
    if model_id.startswith("zai/"):
        if not env.get("ZAI_API_KEY"):
            return (nombre, "ERROR: falta ZAI_API_KEY en el entorno", 0.0)

    cmd = ["opencode", "run", "-m", model_id, prompt]
    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
        elapsed = time.time() - t0
        if result.returncode != 0:
            return (nombre, f"ERROR (exit {result.returncode}): {result.stderr[:300]}", elapsed)
        return (nombre, result.stdout.strip(), elapsed)
    except subprocess.TimeoutExpired:
        return (nombre, "ERROR: timeout (180s)", time.time() - t0)
    except Exception as e:
        return (nombre, f"ERROR: {type(e).__name__}: {e}", time.time() - t0)


def duelo(prompt):
    print("\n" + "=" * 72)
    print("PROMPT:", prompt)
    print("=" * 72)

    with ThreadPoolExecutor(max_workers=len(MODELOS)) as ex:
        futuros = {
            ex.submit(preguntar, nombre, mid, prompt): nombre
            for nombre, mid in MODELOS.items()
        }
        for f in as_completed(futuros):
            nombre, texto, segs = f.result()
            guion = "-" * max(2, 52 - len(nombre))
            print(f"\n--- {nombre}  ({segs:.1f}s) {guion}")
            print(texto)


if __name__ == "__main__":
    # Verificar opencode CLI
    try:
        subprocess.run(["opencode", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ opencode CLI no encontrado. Instala: npm i -g @opencode/opencode")
        exit(1)

    # Avisar si falta ZAI_API_KEY
    if not os.environ.get("ZAI_API_KEY"):
        print("⚠️  ZAI_API_KEY no está seteado — GLM-4.7 fallará")
        print("   Exporta: export ZAI_API_KEY='tu-clave'")

    for p in PROMPTS:
        duelo(p)