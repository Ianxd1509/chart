"""Chart de bateria desde features de onsets/bandas (Task 7, spec F1).

Kick = banda baja (lane 0, grid de 1/4), snare = media (lane 1, grid 1/16),
cymbal = alta (lane 4, grid 1/16). Onsets debiles (ratio < UMBRAL_CLASIF)
no salen como gemas: alimentan el FILL de compases totalmente vacios
(baja→lane 2, media→3, alta→4, max 16/compas) o, si no hay, 4 crashes
por beat. Compases (4/4) totalmente vacios reciben fill: onsets debiles por bandas
máx 16/compas, o 4 crashes lane 4 por beat si no hay. Sin sustains nunca
(formatos valida).
"""
from __future__ import annotations

import numpy as np

from chartforge import formatos
from chartforge.chartgen.features import ExtraccionStems
from chartforge.chartgen.modelo import Gema, ticks_de_tiempo

LANE_BANDA = {"baja": 0, "media": 1, "alta": 4}        # gemas normales
LANE_FILL_BANDA = {"baja": 2, "media": 3, "alta": 4}   # onsets debiles
UMBRAL_CLASIF = 0.25   # ratio de la banda dominante sobre el total
MAX_FILL = 16          # (spec F1: max 16 gemas por compas en Expert)
GRID_KICK = formatos.RESOLUCION          # 1/4 = negra (beat)
GRID_FINO = formatos.RESOLUCION // 4     # 1/16
TICKS_COMPAS = formatos.RESOLUCION * 4   # TS 4/4


def _cuantizar(tiempo: float, bpm: float, grid: int) -> int:
    tick = ticks_de_tiempo(tiempo, bpm)
    return int(round(tick / grid) * grid)


def generar(feat: ExtraccionStems, bpm: float) -> list[Gema]:
    """Chart Expert de bateria: gemas por onset clasificado por banda."""
    if bpm <= 0:
        raise ValueError("bpm debe ser positivo")
    onsets = feat.onsets("drums")
    if onsets.size == 0:
        return []
    energias = feat.energias_bandas("drums", onsets)
    total = energias[["baja", "media", "alta"]].sum(axis=1).to_numpy()
    dominantes = energias[["baja", "media", "alta"]].to_numpy()
    banda_max_idx = dominantes.argmax(axis=1)
    bandas = np.array(["baja", "media", "alta"])[banda_max_idx]
    ratios = dominantes.max(axis=1) / np.maximum(total, 1e-12)

    gemas: dict[tuple[int, int], Gema] = {}
    debiles: list[tuple[float, str]] = []  # (tiempo, banda) para fills
    for tiempo, banda, ratio in zip(onsets, bandas, ratios):
        if ratio < UMBRAL_CLASIF:
            debiles.append((float(tiempo), str(banda)))
            continue
        es_kick = banda == "baja"
        grid = GRID_KICK if es_kick else GRID_FINO
        tick = _cuantizar(float(tiempo), bpm, grid)
        clave = (tick, LANE_BANDA[banda])
        if clave not in gemas:  # cuantizacion puede duplicar el mismo golpe
            gemas[clave] = Gema(tick, LANE_BANDA[banda], 0)

    _agregar_fills(gemas, debiles, bpm)
    salida = sorted(gemas.values(), key=lambda g: (g.tick, g.lane))
    return salida


def _agregar_fills(
    gemas: dict[tuple[int, int], Gema],
    debiles: list[tuple[float, str]],
    bpm: float,
) -> None:
    """Fills en compases (4/4) sin ninguna gema."""
    if not gemas:
        return
    ultimo = max(t for t, _l in gemas)
    compas_final = ultimo // TICKS_COMPAS
    valores = list(gemas.values())
    for compas in range(compas_final + 1):
        t0 = compas * TICKS_COMPAS
        dentro = [g for g in valores if t0 <= g.tick < t0 + TICKS_COMPAS]
        if dentro:
            continue
        debiles_del_compas = [
            (tiempo, banda)
            for tiempo, banda in debiles
            if t0 <= ticks_de_tiempo(tiempo, bpm) < t0 + TICKS_COMPAS
        ]
        if debiles_del_compas:
            for tiempo, banda in debiles_del_compas[:MAX_FILL]:
                tick = _cuantizar(tiempo, bpm, GRID_FINO)
                gemas.setdefault(
                    (tick, LANE_FILL_BANDA[banda]),
                    Gema(tick, LANE_FILL_BANDA[banda], 0),
                )
        else:
            for beat in range(4):
                tick = t0 + beat * GRID_KICK
                gemas.setdefault((tick, 4), Gema(tick, 4, 0))
