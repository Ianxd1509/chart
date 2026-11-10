"""Spike de medicion (Task 4): demucs sobre clip30 + whisper base/small.

Corre desde D:/charf1 con la venv:
    venv/Scripts/python.exe docs/research/spike_medicion.py
Mide tiempo y RAM pico (psutil) de cada etapa y escribe resultados en
docs/research/spike-resultados.txt.
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

import psutil

_RUTA_PROYECTO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_RUTA_PROYECTO))

import chartforge.config as config
from chartforge.etapas import letras, stems

CLIP = config.RUTA_PROYECTO / "tests" / "fixtures" / "clip30.mp3"
TMP = _RUTA_PROYECTO / "tmp" / "spike"


def medir(fn):
    proc = psutil.Process()
    pico = [proc.memory_info().rss]
    parado = threading.Event()

    def muestrear():
        while not parado.is_set():
            pico.append(proc.memory_info().rss)
            time.sleep(0.25)

    hilo = threading.Thread(target=muestrear, daemon=True)
    hilo.start()
    t0 = time.perf_counter()
    resultado = fn()
    dt = time.perf_counter() - t0
    parado.set()
    hilo.join()
    return resultado, dt, max(pico) / 1024**2


def main() -> int:
    salida = [ "== Spike demucs/whisper (clip30) ==", "" ]
    cfg = config.cargar_config("")

    salida.append("[demucs extraer_stems]")
    ruta_tmp = TMP / "stems"
    (rutas, dt, ram) = medir(lambda: stems.extraer_stems(CLIP, ruta_tmp, cfg))
    salida.append(f"tiempo = {dt:.1f} s; RAM pico = {ram:.0f} MB")
    for nombre, ruta in rutas.items():
        salida.append(f"  {nombre}.wav -> {ruta.name}")

    wav_vocals = rutas["vocals"]
    for modelo in ("base", "small"):
        salida.append(f"[whisper transcribir modelo={modelo}]")
        cfg_small = {**cfg, "letras": {**cfg["letras"], "modelo": modelo}}
        (palabras, dt, ram) = medir(lambda: letras.transcribir(wav_vocals, cfg_small))
        n_caracteres = sum(len(p) for _, p in palabras)
        salida.append(f"tiempo = {dt:.1f} s; RAM pico = {ram:.0f} MB; palabras = {len(palabras)}; chars = {n_caracteres}")
        if palabras:
            texto = " ".join(p for _, p in palabras)
            salida.append(f"  texto: {texto[:400]}")

    config.RUTA_PROYECTO.joinpath("docs", "research", "spike-resultados.txt").write_text(
        "\n".join(salida) + "\n", encoding="utf-8")
    print("\n".join(salida))
    return 0


if __name__ == "__main__":
    sys.exit(main())
