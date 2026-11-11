"""Chart de bateria desde features de onsets/bandas (Task 7/v2, spec F1).

v2 (feedback del .sng de referencia): clasificacion por 4 bandas finas
(sub/tom/body/snap/brillante): kick=sub (lane 0, grid 1/8), snare=body o
snap ampl (lane 1, grid 1/16), tom=banda tom tonal (lane 3, grid 1/16),
cymbal=brillante (lane 4, grid 1/16). Onsets débiles (ratio < UMBRAL_CLASIF)
no salen como gemas: alimentan el FILL de compases totalmente vacíos
(sub→lane 2, tom/body→3, snap/brillante→4, máx 16/compas) o, si no hay,
4 crashes por beat. La detección de onsets usa delta=0.035 (más sensible que
el default de librosa; el stem de batería es percusión pura).
Sin sustains nunca (formatos valida).
"""
from __future__ import annotations

import numpy as np

from chartforge import formatos
from chartforge.chartgen.features import ExtraccionStems
from chartforge.chartgen.modelo import Gema, ticks_de_tiempo

# Lanes CH 5-lane estándar: 0=kick, 1=red (snare), 2=yellow, 3=blue, 4=green (cymbal)
LANE_SUB = 0
LANE_SNARE = 1
LANE_TOM = 3
LANE_CIMBAL = 4
LANE_FILL_SUB = 2
LANE_FILL_MEDIA = 3
LANE_FILL_ALTA = 4
UMBRAL_CLASIF = 0.25   # ratio de la banda dominante sobre el total
UMBRAL_SUB_KICK = 0.30  # ratio sub mínimo para llamar kick
UMBRAL_BRILLANTE_CIMBAL = 0.22
SENSIBILIDAD_ONSET = 0.035
MAX_FILL = 16          # (spec F1: max 16 gemas por compas en Expert)
GRID_KICK = formatos.RESOLUCION // 2   # 1/8 = corchea (la negra (1/4) era demasiado grusa)
GRID_FINO = formatos.RESOLUCION // 4     # 1/16
TICKS_COMPAS = formatos.RESOLUCION * 4   # TS 4/4


def _cuantizar(tiempo: float, bpm: float, grid: int) -> int:
    tick = ticks_de_tiempo(tiempo, bpm)
    return int(round(tick / grid) * grid)


def generar(feat: ExtraccionStems, bpm: float) -> list[Gema]:
    """Chart Expert de bateria: gemas por onset clasificado por banda fina."""
    if bpm <= 0:
        raise ValueError("bpm debe ser positivo")
    onsets = feat.onsets("drums", delta=SENSIBILIDAD_ONSET)
    if onsets.size == 0:
        return []
    df = feat.bandas_detalle("drums", onsets)
    cols = ["sub", "tom", "body", "snap", "brillante"]
    matriz = df[cols].to_numpy(dtype=np.float64)
    total = matriz.sum(axis=1)
    total = np.maximum(total, 1e-12)
    sub_r, tom_r, body_r, snap_r, bri_r = (matriz[:, i] / total for i in range(5))

    gemas: dict[tuple[int, int], Gema] = {}
    debiles: list[tuple[float, str]] = []  # (tiempo, banda_llenar) para fills
    for indice, tiempo in enumerate(onsets):
        ratios = (sub_r[indice], tom_r[indice], body_r[indice], snap_r[indice], bri_r[indice])
        dominante = max(ratios)
        sub_c, medio, brillante = ratios[0], ratios[1] + ratios[2], ratios[4]
        snap_c = ratios[3]

        if sub_c >= UMBRAL_SUB_KICK:
            lane = LANE_SUB
        elif brillante >= UMBRAL_BRILLANTE_CIMBAL:
            lane = LANE_CIMBAL
        elif dominante >= UMBRAL_CLASIF:
            if ratios[1] > ratios[2] and ratios[1] >= snap_c * 0.8:
                lane = LANE_TOM  # tonal low-mid (160-350 Hz)
            else:
                lane = LANE_SNARE
        else:
            # debil: alimenta los fills de compases vacios
            if sub_c >= 0.25:
                llenar = "baja"
            elif medio + snap_c >= 0.5:
                llenar = "media"
            else:
                llenar = "alta"
            debiles.append((float(tiempo), llenar))
            continue

        grid = GRID_KICK if lane == LANE_SUB else GRID_FINO
        tick = _cuantizar(float(tiempo), bpm, grid)
        clave = (tick, lane)
        if clave not in gemas:  # cuantizacion puede duplicar el mismo golpe
            gemas[clave] = Gema(tick, lane, 0)

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

        def _llenar(banda: str) -> int:
            return {"baja": LANE_FILL_SUB, "media": LANE_FILL_MEDIA, "alta": LANE_FILL_ALTA}[banda]

        if debiles_del_compas:
            for tiempo, banda in debiles_del_compas[:MAX_FILL]:
                tick = _cuantizar(tiempo, bpm, GRID_FINO)
                gemas.setdefault((tick, _llenar(banda)), Gema(tick, _llenar(banda), 0))
        else:
            for beat in range(4):
                tick = t0 + beat * formatos.RESOLUCION  # 1 crash por negra (1/4)
                gemas.setdefault((tick, LANE_FILL_ALTA), Gema(tick, LANE_FILL_ALTA, 0))
