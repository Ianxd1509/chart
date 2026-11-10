"""Tests de chartgen (Task 7): drums, guitar/bass, vocals + dificultades.

Fixtures sinteticas deterministas: click 120 BPM, melodias de senoides a
frecuencias fijas, clusters de acorde. Tolerancias cubren ruido de librosa
(±30 ms de onsets, mediana de pyin), pero las expectativas de tick son exactas.
"""
from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from chartforge.chartgen.dificultades import aplicar
from chartforge.chartgen.drums import generar as generar_drums
from chartforge.chartgen.features import ExtraccionStems
from chartforge.chartgen.guitar_bass import generar as generar_guitarra
from chartforge.chartgen.modelo import Gema, Letra, PistaCancion
from chartforge.chartgen.vocals import generar as generar_voz
from chartforge.formatos import parsear_chart

SR = 44100
BPM = 120.0
TICK_BEAT = 192  # RESOLUCION por negra a resolution 192


def _escribir_mono(ruta, datos):
    sf.write(str(ruta), np.stack([datos, datos], axis=1), SR, subtype="PCM_16")


def _segmentos(frecuencias, intervalos, amp=0.5):
    """Senoide con ataque corto por segmento [t0, t1): onset limpio por inicio."""
    fin = intervalos[-1][1] + 1.0
    datos = np.zeros(int(SR * fin), dtype=np.float32)
    for (t0, t1), f in zip(intervalos, frecuencias):
        i0, i1 = int(t0 * SR), int(t1 * SR)
        n = i1 - i0
        tt = np.arange(n) / SR
        envolvente = np.minimum(1.0, tt / 0.030) * np.exp(-tt * 0.5)
        datos[i0:i1] += (amp * np.sin(2 * np.pi * f * tt) * envolvente).astype(np.float32)
    return datos


@pytest.fixture()
def feat_drums_clicks(tmp_path):
    """drums = clicks 100 Hz cada beat desde 0.5 s (1.5 compases + impares)."""
    datos = np.zeros(SR * 5, dtype=np.float32)
    for t_click in [0.5 * i for i in range(1, 7)]:  # 0.5..3.0
        i0 = int(t_click * SR)
        tt = np.arange(int(0.15 * SR)) / SR
        burst = np.sin(2 * np.pi * 100.0 * tt) * np.exp(-tt * 25.0)
        datos[i0 : i0 + len(tt)] += burst.astype(np.float32)
    pico = np.abs(datos).max()
    _escribir_mono(tmp_path / "drums.wav", (datos / pico * 0.9).astype(np.float32))
    for resto in ("bass", "other", "vocals"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(SR * 5, dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    return ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])


@pytest.fixture()
def feat_melodia(tmp_path):
    """other = melodias de 3 alturas en intervalos; drums/vocals/bass vacios."""
    datos = _segmentos(
        [220.0, 330.0, 440.0, 440.0],
        [(0.5, 1.5), (1.5, 2.0), (2.0, 2.5), (2.5, 3.5)],
    )
    _escribir_mono(tmp_path / "other.wav", datos)
    for resto in ("drums", "bass", "vocals"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(SR * 5, dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    extra = ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])
    return extra


@pytest.fixture()
def feat_acorde(tmp_path):
    """other = nota 220 Hz + segunda nota 440 Hz 30 ms despues (cluster <50 ms)."""
    datos = _segmentos([220.0, 440.0, 440.0], [(0.5, 1.4), (0.53, 1.4), (1.4, 2.4)])
    _escribir_mono(tmp_path / "other.wav", datos)
    for resto in ("drums", "bass", "vocals"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(SR * 5, dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    return ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])


@pytest.fixture()
def feat_voz(tmp_path):
    """vocals = tono 300 Hz en dos burst; drums/bass/other vacios."""
    datos = _segmentos([300.0, 300.0], [(0.5, 0.8), (1.0, 1.3)], amp=0.4)
    _escribir_mono(tmp_path / "vocals.wav", datos)
    for resto in ("drums", "bass", "other"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(SR * 5, dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    return ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])


# ---------------------------------------------------------------------------
# duracion (metodo aditivo de features que Task 7 consume)
# ---------------------------------------------------------------------------
def test_duracion_del_stem(feat_drums_clicks):
    assert feat_drums_clicks.duracion("drums") == pytest.approx(5.0, abs=0.02)


# ---------------------------------------------------------------------------
# drums
# ---------------------------------------------------------------------------
def test_drums_kick_en_cada_beat(feat_drums_clicks):
    gemas = generar_drums(feat_drums_clicks, BPM)
    ticks = {g.tick for g in gemas}
    esperados = {192 * i for i in range(1, 7)}  # beats 0.5..3.0
    assert esperados.issubset(ticks), f"faltan kicks en beats: {sorted(esperados - ticks)}"
    kicks = [g for g in gemas if g.tick in esperados]
    assert all(g.lane == 0 for g in kicks), "todo beat fuerte es kick (lane 0)"
    assert all(g.longitud == 0 for g in gemas), "bateria sin sustains"
    # jugable por diseno: max 4 lanes por tick, sin duplicados mismo tick+lane
    por_tick: dict[int, set[int]] = {}
    for g in gemas:
        assert g.lane not in por_tick.setdefault(g.tick, set()), f"duplicado tick {g.tick}"
        por_tick[g.tick].add(g.lane)
    assert all(len(lanes) <= 4 for lanes in por_tick.values())


def test_drums_fill_en_compas_vacio(tmp_path):
    """Compas [2.0, 4.0) sin onsets → 4 gemas de fill (lane 4, max 16/compas)."""
    datos = np.zeros(SR * 7, dtype=np.float32)
    for t_click in [0.5, 1.0, 1.5, 4.0, 4.5, 5.0, 5.5]:
        i0 = int(t_click * SR)
        tt = np.arange(int(0.15 * SR)) / SR
        burst = np.sin(2 * np.pi * 100.0 * tt) * np.exp(-tt * 25.0)
        datos[i0 : i0 + len(tt)] += burst.astype(np.float32)
    pico = np.abs(datos).max()
    _escribir_mono(tmp_path / "drums.wav", (datos / pico * 0.9).astype(np.float32))
    for resto in ("bass", "other", "vocals"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(SR * 7, dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    extra = ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])

    gemas = generar_drums(extra, BPM)
    compas_vacio = [g for g in gemas if 768 <= g.tick < 768 * 2]
    ticks_fill = {g.tick for g in compas_vacio}
    assert ticks_fill == {768, 960, 1152, 1344}, f"compas vacio: {sorted(ticks_fill)}"
    assert len(compas_vacio) <= 16, "fill max 16 gemas por compas"
    assert {g.lane for g in compas_vacio} == {4}, "fill con lane de cymbal"


def test_drums_clasifica_snare_de_banda_media(tmp_path):
    """Click de 800 Hz (media) → snare lane 1, NO kick."""
    datos = np.zeros(SR * 3, dtype=np.float32)
    for t_click in (0.5, 1.0, 1.5, 2.0):
        i0 = int(t_click * SR)
        tt = np.arange(int(0.15 * SR)) / SR
        burst = np.sin(2 * np.pi * 800.0 * tt) * np.exp(-tt * 25.0)
        datos[i0 : i0 + len(tt)] += burst.astype(np.float32)
    pico = np.abs(datos).max()
    _escribir_mono(tmp_path / "drums.wav", (datos / pico * 0.9).astype(np.float32))
    for resto in ("bass", "other", "vocals"):
        _escribir_mono(tmp_path / f"{resto}.wav", np.zeros(SR * 3, dtype=np.float32))
    campos = {n: tmp_path / f"{n}.wav" for n in ("drums", "bass", "other", "vocals")}
    extra = ExtraccionStems(campos["drums"], campos["bass"], campos["other"], campos["vocals"])

    gemas = generar_drums(extra, BPM)
    golpes = [g for g in gemas if g.tick in {192, 384, 576, 768}]
    assert golpes and all(g.lane == 1 for g in golpes), f"800 Hz es snare: {golpes}"


# ---------------------------------------------------------------------------
# guitarra / bajo
# ---------------------------------------------------------------------------
def test_guitarra_lanes_por_pitch_y_sustain(feat_melodia):
    gemas = generar_guitarra(feat_melodia, "other", BPM)
    por_tick = {g.tick: g for g in gemas}
    # onsets en {0.5, 1.5, 2.0, 2.5} → ticks {192, 576, 768, 960}
    assert {192, 576, 768, 960}.issubset(por_tick), f"ticks: {sorted(por_tick)}"
    assert por_tick[192].lane == 0, "220 Hz → lane baja"
    assert por_tick[576].lane == 2, "330 Hz → lane media"
    assert por_tick[768].lane == 4, "440 Hz → lane alta"
    # sustain: 220 sostiene 1.0 s (next onset cambia >1 semitono) → 384 ticks
    assert por_tick[192].longitud == 384
    assert por_tick[576].longitud == 192
    # 440→440 same pitch → sustain 0 (no solapado)
    assert por_tick[768].longitud == 0
    assert all(g.longitud >= 0 for g in gemas)


def test_guitarra_acorde_onsets_juntos(feat_acorde):
    """Onsets a 30 ms → un solo tick con acorde (2 gemas, lanes consecutivas)."""
    gemas = generar_guitarra(feat_acorde, "other", BPM)
    por_tick: dict[int, list[Gema]] = {}
    for g in gemas:
        por_tick.setdefault(g.tick, []).append(g)
    acordes = {t: gemas_t for t, gemas_t in por_tick.items() if len(gemas_t) >= 2}
    assert acordes, f"no se fusiono el cluster <50 ms: {sorted((g.tick, g.lane) for g in gemas)}"
    lanes_del_acorde = sorted(g.lane for g in next(iter(acordes.values())))
    assert len(acordes) == 1, "solo el cluster forma acorde"
    assert lanes_del_acorde == [lanes_del_acorde[0] + i for i in range(len(lanes_del_acorde))]
    assert len(lanes_del_acorde) <= 3, "acordes max 3 gemas"


def test_bajo_genera_desde_stem_bass(feat_melodia):
    gemas = generar_guitarra(feat_melodia, "bass", BPM)
    assert isinstance(gemas, list)
    # bass.wav esta vacio en la fixture: el chart de bajo es vacio, no error
    assert gemas == []


# ---------------------------------------------------------------------------
# vocals
# ---------------------------------------------------------------------------
def test_voz_sin_letra_y_evento(feat_voz):
    gemas = generar_voz(feat_voz, None, BPM)
    ticks = {g.tick for g in gemas}
    assert {192, 384}.issubset(ticks), f"gemas por onsets de voz: {sorted(ticks)}"

    pista = PistaCancion(bpm=BPM, letra=None, gemas={"voz": {"Expert": gemas}})
    texto = pista.to_chart_text({"name": "T", "artist": "A"})
    assert '"#sin-letras"' in texto, "evento #sin-letras sin letra"
    assert "lyric" not in texto


def test_voz_con_letra_gemas_por_palabra(feat_voz):
    letra = Letra(palabras=[(0.5, "a"), (1.0, "b")], lineas=[(0.5, "a b")])
    gemas = generar_voz(feat_voz, letra, BPM)
    ticks = {g.tick for g in gemas}
    assert ticks == {192, 384}, f"gemas de palabras a su tiempo: {sorted(ticks)}"


def test_letras_como_eventos_globales(feat_voz):
    """Lyrics van en [Events] global (Task 2), con phrase_start/phrase_end."""
    letra = Letra(palabras=[(0.5, "hola"), (1.0, "chao")], lineas=[(0.5, "hola chao")])
    pista = PistaCancion(bpm=BPM, letra=letra, gemas={})
    texto = pista.to_chart_text({"name": "T", "artist": "A"})
    eventos = parsear_chart(texto).get(("Events", 192, "E"), ())
    assert "lyric hola" in eventos
    assert "phrase_start" in eventos
    assert "lyric chao" in parsear_chart(texto).get(("Events", 384, "E"), ())
    assert "phrase_end" in parsear_chart(texto).get(("Events", 384, "E"), ())


# ---------------------------------------------------------------------------
# dificultades
# ---------------------------------------------------------------------------
def _gemas_sinteticas():
    """12 aisladas (1.0 s entre si, d=1), 10 medias (24 ticks, d=4..7),
    12 densas (12 ticks, d=8..15): la ladder de densidades es exacta a 120 BPM
    con ventana 0.25 s estricta e umbrales 'lower' (ver dificultades.py)."""
    aisladas = [192 + 384 * i for i in range(12)]
    medias = [5760 + 24 * i for i in range(10)]
    densas = [6528 + 12 * i for i in range(12)]
    return [Gema(t, 2) for t in aisladas + medias + densas]


def test_dificultades_nucleo_comun_y_densidad():
    d = aplicar({"guitarra": _gemas_sinteticas()}, BPM)["guitarra"]
    assert set(d) == {"Easy", "Medium", "Hard", "Expert"}
    ticks = {niv: {g.tick for g in d[niv]} for niv in d}
    assert ticks["Easy"] <= ticks["Medium"], "Easy incluido en Medium"
    assert ticks["Medium"] <= ticks["Hard"], "Medium incluido en Hard"
    assert ticks["Hard"] <= ticks["Expert"], "Hard incluido en Expert"
    assert ticks["Easy"] == {192 + 384 * i for i in range(12)}, "aisladas en Easy"
    assert ticks["Medium"] - ticks["Easy"] == {5760, 5784, 5808, 5928, 5952, 5976}
    assert ticks["Hard"] - ticks["Medium"] == {5832, 5856, 5880, 5904} | {6528, 6540, 6648, 6660}
    assert ticks["Expert"] - ticks["Hard"] == {
        6552, 6564, 6576, 6588, 6600, 6612, 6624, 6636
    }, "solo lo mas denso se queda en Expert"

def test_fusion_respeta_cap_de_lanes_por_instrumento():
    """Fusion >160 BPM: guitarra/bajo max 3 gemas por acorde, bateria 4, voz 1.

    Alinea el codigo con el checklist de verificacion manual (acordes de
    cuerdas max 3 gemas) y el diseño Task 7; la bateria de CH SI admite 4
    (kick + 3 pads a la vez).
    """
    gemas = {
        "guitarra": [Gema(192, lane) for lane in range(5)],
        "bajo": [Gema(192, lane) for lane in range(5)],
        "bateria": [Gema(192, lane) for lane in range(5)],
        "voz": [Gema(192, lane) for lane in range(2)],
    }
    resultado = aplicar(gemas, 200.0)  # >160: fusion activa (el caso de la revision)
    assert len(resultado["guitarra"]["Expert"]) == 3
    assert len(resultado["bajo"]["Expert"]) == 3
    assert len(resultado["bateria"]["Expert"]) == 4
    assert len(resultado["voz"]["Expert"]) == 1


def test_dificultades_fusion_sobre_160():
    experto = {"guitarra": _gemas_sinteticas()}
    expert120 = aplicar(experto, BPM)["guitarra"]["Expert"]
    assert len(expert120) == 34, "a 120 BPM no se fusiona nada"
    exp200 = aplicar(experto, 200.0)["guitarra"]["Expert"]
    ticks = sorted(g.tick for g in exp200)
    gaps = [ticks[i + 1] - ticks[i] for i in range(len(ticks) - 1)]
    assert min(gaps) >= 48, f"min separacion 1/16: {min(gaps)}"
    # cada lider absorbe a los que estan a <48 ticks SUYO: run de 10 a paso 24
    # queda en 5 eventos (paso 48); run denso de 12 a paso 12 queda en 3
    assert len(exp200) == 20
    assert sum(1 for t in ticks if 5760 <= t < 5980) == 5, "run medio: 5 eventos"
    assert sum(1 for t in ticks if t >= 6528) == 3, "run denso: 3 eventos"

