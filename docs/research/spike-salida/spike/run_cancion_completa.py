"""Corrida completa de una canciones del corpus con demucs (medicion manual Task 4)."""
import sys
import threading
import time
from pathlib import Path

import psutil
import soundfile as sf

sys.path.insert(0, r"D:\charf1")
import chartforge.config as config
from chartforge.etapas import stems

AUDIO = Path(r"C:\Users\art64\Downloads\musica de prueba\1_spotdown.org.mp3")
DESTINO = config.RUTA_PROYECTO / "tmp" / "spike" / "cancion-completa"
LOG = config.RUTA_PROYECTO / "docs" / "research" / "spike-cancion-completa.txt"


def medir(fn):
    proc = psutil.Process()
    pico = [proc.memory_info().rss]
    parado = threading.Event()

    def muestrear():
        while not parado.is_set():
            pico.append(proc.memory_info().rss)
            time.sleep(0.5)

    hilo = threading.Thread(target=muestrear, daemon=True)
    hilo.start()
    t0 = time.perf_counter()
    resultado = fn()
    dt = time.perf_counter() - t0
    parado.set()
    hilo.join()
    return resultado, dt, max(pico) / 1024**2


def main():
    cfg = config.cargar_config("")
    info = sf.info(str(AUDIO))
    duracion = info.duration
    print(f"cancion: {AUDIO.name}; duracion {duracion:.1f} s = {duracion/60:.2f} min", flush=True)
    inicio = time.perf_counter()
    (rutas, dt, ram) = medir(lambda: stems.extraer_stems(AUDIO, DESTINO, cfg))
    total = time.perf_counter() - inicio
    lineas = [
        f"cancion = {AUDIO.name}",
        f"duracion = {duracion:.1f} s ({duracion/60:.2f} min)",
        f"demucs tiempo = {dt:.1f} s (total proceso {total:.1f} s)",
        f"factor = {dt/duracion:.2f}x tiempo real",
        f"RAM pico = {ram:.0f} MB",
        f"stems en: {DESTINO}",
    ]
    LOG.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
