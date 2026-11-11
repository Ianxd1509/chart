"""SP (Star Power) y secciones automáticas por ENERGÍA (heurística honesta).

No “entiende” la canción: agrupa compases en RUNES de alta/baja energía y los
etiqueta alto=“Chorus”, bajo=“Verse”. En complejos/ambientales largos sale
imperfecto — es una aproximación documentada, nunca un error (si la selección
queda vacía, simplemente no se escriben frases/secciones).

S 2 va en CADA sección de dificultad (Single/DoubleBass/Drums) en el MISMO tick;
las secciones van como eventos globales en [Events] ("section <título>").
"""
from __future__ import annotations

import numpy as np

from chartforge import formatos

TICKS_COMPAS = formatos.RESOLUCION * 4  # TS 4/4
_SP_BARRAS = 4  # frase SP típica de 4 compases
_SP_MAX = 3
_SP_MIN_BARRAS_COBERTURA = 8  # separación minima entre frases
_SP_UMBRAL_PCT = 60  # percentil de energía para considerar "alto"
_SECCIONES_MAX = 14
_SECCIONES_MAX_SP = 6


def energias_por_compas(ruta_mix, bpm: float, sr: int = 11025) -> np.ndarray:
    """RMS del mix por compás (4/4). Se carga UNA vez, mono."""
    import librosa  # diferido

    y, _sr = librosa.load(str(ruta_mix), sr=sr, mono=True)
    segundos_compas = 4 * 60.0 / float(bpm)
    muestras_compas = max(1, int(segundos_compas * sr))
    if len(y) == 0:
        return np.array([], dtype=np.float64)
    n = int(np.ceil(len(y) / muestras_compas))
    rms = np.zeros(n, dtype=np.float64)
    for i in range(n):
        bloque = y[i * muestras_compas : (i + 1) * muestras_compas]
        rms[i] = float(np.sqrt(np.mean(bloque**2))) if bloque.size else 0.0
    return rms


def _runs(mascara: np.ndarray) -> list[tuple[int, int]]:
    """Runs (inicio, fin) inclusivos de True en la máscara booleana."""
    runs: list[tuple[int, int]] = []
    inicio = None
    for i, valor in enumerate(np.asarray(mascara, dtype=bool)):
        if valor and inicio is None:
            inicio = i
        elif not valor and inicio is not None:
            runs.append((inicio, i - 1))
            inicio = None
    if inicio is not None:
        runs.append((inicio, len(mascara) - 1))
    return runs


def proponer_frases_sp(
    rms: np.ndarray, bpm: float
) -> list[tuple[int, int]]:
    """Ticks (inicio, longitud) de hasta 3 frases SP en las cimas de energía."""
    n = len(rms)
    if n < _SP_BARRAS * 2:
        return []
    umbral = float(np.percentile(rms, _SP_UMBRAL_PCT))
    alta = rms >= umbral
    # funde runs separados por 1 compas (SP va como bloque continuo)
    alta_fundida = np.asarray(alta.copy())
    for i in range(n - 2):
        if alta[i] and alta[i + 2] and not alta[i + 1]:
            alta_fundida[i + 1] = True
    runs = _runs(alta_fundida)
    if not runs:
        return []
    mediados = [
        (float(np.mean(rms[a : b + 1])), a, b) for a, b in runs if b - a >= _SP_BARRAS - 1
    ]
    mediados.sort(key=lambda item: (item[0], item[2] - item[1]), reverse=True)
    escogidos: list[tuple[int, int, int]] = []  # (pico, a, b)
    for pico, a, b in mediados:
        if all(abs(a - otra_a) >= _SP_MIN_BARRAS_COBERTURA for _p, otra_a, _ob in escogidos):
            escogidos.append((pico, a, b))
        if len(escogidos) >= _SP_MAX:
            break
    if not escogidos:
        return []
    escogidos.sort(key=lambda item: item[1])
    frases: list[tuple[int, int]] = []
    for _p, a, _b in escogidos:
        start_bar = a
        longitud = _SP_BARRAS * TICKS_COMPAS
        frases.append((start_bar * TICKS_COMPAS, longitud))
    return frases[:_SP_MAX]


def proponer_secciones(rms: np.ndarray) -> list[tuple[int, str]]:
    """Lista (tick, nombre) para eventos globales: Intro, Verse/Chorus N, Outro."""
    n = len(rms)
    if n == 0:
        return []
    secciones: list[tuple[int, str]] = [(0, "Intro")]
    if n < 6:
        secciones.append((max(0, (n - 2)) * TICKS_COMPAS, "Outro"))
        return secciones
    umbral = float(np.percentile(rms, 60))
    alto = rms >= umbral
    runs = _runs(alto)
    if runs and runs[0][0] == 0:
        # la cancion arranca directa en energia alta: no habria un "Intro" real
        secciones = secciones[1:]
    coros = 0
    versos = 0
    cursor = 0
    for a, b in runs:
        if a > cursor + 2:
            versos += 1
            secciones.append((cursor * TICKS_COMPAS, f"Verse {versos}"))
        coros += 1
        secciones.append((a * TICKS_COMPAS, f"Chorus {coros}"))
        cursor = b + 1
        if coros >= _SECCIONES_MAX_SP:
            break
    if cursor < n - 2:
        versos += 1
        secciones.append((cursor * TICKS_COMPAS, f"Verse {versos}"))
    secciones.append((max(0, n - 2) * TICKS_COMPAS, "Outro"))
    # ordena y limita; deduplica ticks consecutivos
    vistas: set[int] = set()
    salida: list[tuple[int, str]] = []
    for tick, nombre in sorted(secciones, key=lambda par: par[0]):
        if tick in vistas:
            continue
        vistas.add(tick)
        salida.append((int(tick), nombre))
        if len(salida) >= _SECCIONES_MAX:
            break
    return salida
