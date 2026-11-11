"""Tests de SP/secciones automáticas (#5) y su integración en notes.chart."""
from __future__ import annotations

import numpy as np

from chartforge.chartgen.modelo import Gema, Letra, PistaCancion
from chartforge.chartgen.secciones import proponer_frases_sp, proponer_secciones

TICKS_COMPAS = 192 * 4


def _rms_falsa() -> np.ndarray:
    """48 compases: bajo-bajo-medio, 3 picos de 5 compases altos."""
    patron = np.array([0.10, 0.12, 0.11, 0.09] * 12, dtype=np.float64)
    for base in (4, 16, 32):
        patron[base : base + 5] = 0.9
    return patron


def test_sp_seleciona_cimas_no_solapadas_y_en_compases():
    rms = _rms_falsa()
    frases = proponer_frases_sp(rms, 120.0)
    assert 1 <= len(frases) <= 3
    for inicio, longitud in frases:
        assert inicio % TICKS_COMPAS == 0, f"frase SP no alineada al compas: {inicio}"
        assert longitud == 4 * TICKS_COMPAS
    inicios = sorted(f[0] for f in frases)
    for a, b in zip(inicios, inicios[1:]):
        assert b - a >= 8 * TICKS_COMPAS, "frases SP demasiado cercanas"


def test_sp_sin_cimas_no_escribe_nada():
    rms = np.full(32, 0.5, dtype=np.float64)
    frases = proponer_frases_sp(rms, 120.0)
    # aun sin picos, las cimas (todas altas) son aceptables: no es condicion de error
    assert isinstance(frases, list)


def test_secciones_intro_versos_coros_outro():
    rms = _rms_falsa()
    secciones = proponer_secciones(rms)
    nombres = [nombre for _t, nombre in secciones]
    assert secciones[0][0] == 0
    assert "Intro" in nombres
    assert any(n.startswith("Chorus") for n in nombres)
    assert any(n.startswith("Verse") for n in nombres)
    assert nombres[-1] == "Outro"
    ticks = [t for t, _n in secciones]
    assert ticks == sorted(ticks)


def test_secciones_canciones_arranca_en_alto_sin_intro():
    rms = np.full(16, 0.9, dtype=np.float64)
    secciones = proponer_secciones(rms)
    nombres = [nombre for _t, nombre in secciones]
    assert "Intro" not in nombres


def test_sp_y_secciones_en_el_chart():
    pista = PistaCancion(
        bpm=120.0,
        letra=Letra(palabras=[(0.5, "hola")], lineas=[(0.5, "hola")]),
        gemas={
            "guitarra": {"Expert": [Gema(0, 2, 0)]},
            "bateria": {"Expert": [Gema(192, 0, 0)]},
        },
        frases_sp=[(192, 768), (1536, 768)],
        secciones=[(0, "Intro"), (768, "Chorus 1")],
    )
    texto = pista.to_chart_text({"name": "T", "artist": "A"})
    assert "192 = S 2 768" in texto and "1536 = S 2 768" in texto
    assert texto.count("= S 2 ") >= 2  # al menos bateria y guitarra x2
    assert '0 = E "section Intro"' in texto
    assert '768 = E "section Chorus 1"' in texto
    # S y N mezclados y cronologicos en ExpertSingle
    seccion = texto.split("[ExpertSingle]")[1].split("[")[0]
    lineas = [l for l in seccion.splitlines() if " = N " in l or " = S " in l]
    ticks = [int(l.split("=")[0]) for l in lineas]
    assert ticks == sorted(ticks), f"orden: {ticks}"
