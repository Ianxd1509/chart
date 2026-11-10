"""Densidad de dificultad (Task 7, spec F1): 4 niveles por densidad local.

Por instrumento: fusion de gemas con separacion < 1/16 (48 ticks) SOLO
a bpm > 160; densidad local = cantidad de gemas del instrumento a |Δt| <
0.25 s (incluida la propia); umbrales por INDICE (lower) del vector de
densidades ordenado: Easy = d <= u25, Medium suma d <= u50, Hard suma
d <= u75, el resto sale solo en Expert. Easy ⊆ Medium ⊆ Hard ⊆ Expert.
"""
from __future__ import annotations

import itertools

import numpy as np

from chartforge.chartgen.modelo import Gema, tiempo_de_ticks

GAP_FUSION_TICKS = 48          # RESOLUCION/4 = 1/16 nota
BPM_FUSION_MIN = 160.0
DENSIDAD_VENTANA_S = 0.25      # estricta: |Δt| < 0.25 s
DIFICULTADES = ("Easy", "Medium", "Hard", "Expert")

# Gemas simultaneas maximas por instrumento (diseño Task 7: acordes max 3 en
# cuerdas; CH bateria SI admite 4 = kick + 3 pads; voz una nota a la vez).
MAX_LANES = {"bateria": 4, "guitarra": 3, "bajo": 3, "voz": 1}


def _recortar_acordes(gemas: list[Gema], max_lanes: int) -> list[Gema]:
    """Recorta cada acorde (gemas de mismo tick) a `max_lanes` gemas."""
    salida: list[Gema] = []
    for _tick, grupo in itertools.groupby(gemas, key=lambda g: g.tick):
        cabezas = sorted(grupo, key=lambda g: g.lane)
        salida.extend(cabezas[:max_lanes])
    return salida


def _fusionar(gemas: list[Gema], max_lanes: int = 4) -> list[Gema]:
    """bpm > 160: el primer evento de un grupo <1/16 absorbe a los demas.

    Los gemas del mismo tick (acorde ya formado) no se tocan entre si; los
    seguidores a menos de 48 ticks del lider aportan su lane (cap = max_lanes
    por evento) y su longitud maxima. Devuelve ordenado por (tick, lane).
    """
    orden = sorted(gemas, key=lambda g: (g.tick, g.lane))
    salida: list[Gema] = []
    i, n = 0, len(orden)
    while i < n:
        lider = orden[i]
        absorbidas: dict[int, int] = {lider.lane: lider.longitud}
        j = i + 1
        while j < n and orden[j].tick == lider.tick:  # acorde ya formado
            absorbidas.setdefault(orden[j].lane, orden[j].longitud)
            j += 1
        while j < n and orden[j].tick - lider.tick < GAP_FUSION_TICKS:
            absorbidas.setdefault(orden[j].lane, orden[j].longitud)
            j += 1
        i = j
        for lane in sorted(absorbidas)[:max_lanes]:
            salida.append(Gema(lider.tick, lane, absorbidas[lane]))
    return salida


def _umbrales(densidades: np.ndarray) -> tuple[float, float, float]:
    """Indices 'lower' de la lista ordenada: u25, u50, u75."""
    ordenada = np.sort(densidades)
    n = len(ordenada)

    def _indice(frac: float) -> float:
        return float(ordenada[int(np.floor(frac * (n - 1)))])

    return _indice(0.25), _indice(0.50), _indice(0.75)


def aplicar(
    gemas_instrumento: dict[str, list[Gema]], bpm: float
) -> dict[str, dict[str, list[Gema]]]:
    """Experto por instrumento → 4 niveles; densidad local define el grado."""
    if bpm <= 0:
        raise ValueError("bpm debe ser positivo")
    resultado: dict[str, dict[str, list[Gema]]] = {}
    for instrumento, lista in gemas_instrumento.items():
        lista = sorted(lista, key=lambda g: (g.tick, g.lane))
        max_lanes = MAX_LANES.get(instrumento, 3)
        if bpm > BPM_FUSION_MIN:
            lista = _fusionar(lista, max_lanes)
        lista = _recortar_acordes(lista, max_lanes)  # cap SIEMPRE, fusion o no
        if not lista:
            resultado[instrumento] = {nivel: [] for nivel in DIFICULTADES}
            continue
        tiempos = np.array(
            [tiempo_de_ticks(g.tick, bpm) for g in lista], dtype=np.float64
        )
        densidades = np.array(
            [(np.abs(tiempos - t) < DENSIDAD_VENTANA_S).sum() for t in tiempos],
            dtype=np.int64,
        )
        u25, u50, u75 = _umbrales(densidades)
        lista_easy, lista_medium, lista_hard = [], [], []
        for gema, densidad in zip(lista, densidades):
            if densidad <= u25:  # banda 1: en Easy, Medium y Hard
                lista_easy.append(gema)
                lista_medium.append(gema)
                lista_hard.append(gema)
            elif densidad <= u50:  # banda 2: en Medium y Hard
                lista_medium.append(gema)
                lista_hard.append(gema)
            elif densidad <= u75:  # banda 3: solo Hard
                lista_hard.append(gema)
            # resto (banda 4): SOLO Expert
        niveles = {
            "Easy": lista_easy,
            "Medium": lista_medium,
            "Hard": lista_hard,
            "Expert": list(lista),  # Expert SIEMPRE lleva todo
        }
        resultado[instrumento] = niveles
    return resultado
