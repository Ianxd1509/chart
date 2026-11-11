"""Tests de empaquetado (Task 8): carpeta de cancion con song.ini, notes.chart
y OGG por stem. Fijan los Rulings: song.ini SIN delay/song_length (Task 2,
wiki CH), letras como eventos globales, audio ffmpeg VBR q6.
"""
from __future__ import annotations

import configparser
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from chartforge.chartgen.modelo import Gema, Letra, PistaCancion
from chartforge.etapas.empaquetado import crear_carpeta_cancion
from chartforge.formatos import NOMBRE_CARPETA, NOMBRES_AUDIO_STEMS, parsear_chart

SR = 44100
DURACION_S = 2


@pytest.fixture()
def rutas_audio(tmp_path):
    """2 s de silencio WAV: rapidos de codificar."""
    datos = np.zeros((SR * DURACION_S, 2), dtype=np.float32)
    rutas: dict[str, Path] = {}
    for nombre in ("bateria", "guitarra", "bajo", "voz", "mix"):
        ruta = tmp_path / f"{nombre}.wav"
        sf.write(str(ruta), datos, SR, subtype="PCM_16")
        rutas[nombre] = ruta
    return rutas


@pytest.fixture()
def pista_sintetica():
    """bpm 120, letra de 1 linea, guitarra/bateria con gemas conocidas."""
    letra = Letra(palabras=[(0.5, "hola")], lineas=[(0.5, "hola")])
    return PistaCancion(
        bpm=120.0,
        letra=letra,
        gemas={
            "guitarra": {"Expert": [Gema(0, 2, 0)]},
            "bateria": {"Expert": [Gema(0, 0, 0)]},
            "bajo": {"Expert": []},
        },
    )


def _stems_de(rutas_audio):
    return {k: v for k, v in rutas_audio.items() if k != "mix"}


def test_carpeta_saneada_y_devuelta(tmp_path, rutas_audio, pista_sintetica):
    resultado = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="T: /bin", artista="Bad /Char", destino=tmp_path,
    )
    esperado = tmp_path / NOMBRE_CARPETA("Bad /Char", "T: /bin")
    assert resultado == esperado
    assert resultado.is_dir()
    prohibidos = set('\\/:*?"<>|')
    assert not (set(NOMBRE_CARPETA("Bad /Char", "T: /bin")) & prohibidos)


def test_song_ini_campos_minimos_sin_delay(tmp_path, rutas_audio, pista_sintetica):
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="Titulo", artista="Artista", destino=tmp_path,
    )
    ini = carpeta / "song.ini"
    assert ini.is_file()
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(str(ini), encoding="utf-8")
    seccion = "song"
    assert any(s.lower() == "song" for s in parser.sections()), parser.sections()
    campos = {k.lower(): v for s in parser.sections() for k, v in parser.items(s)}
    assert campos.get("name") == "Titulo"
    assert campos.get("artist") == "Artista"
    assert campos.get("charter") == "ChartForge"
    assert "delay" not in campos, "delay NO se escribe (Ruling Task 2: wiki CH 'not recommended')"
    assert "song_length" not in campos


def test_song_ini_diff_y_tags(tmp_path, rutas_audio, pista_sintetica, monkeypatch):
    """#3: diff_* refleja las dificultades generadas + album/year/genre del origen."""
    monkeypatch.setattr(
        "chartforge.etapas.empaquetado.leer_tags",
        lambda _audio: {"album": "99.9", "year": "2019", "genre": "J-Rock"},
    )
    monkeypatch.setattr(
        "chartforge.etapas.empaquetado.extraer_caratula", lambda _audio, _dst: None
    )
    mensajes: list[str] = []
    audio_fake = tmp_path / "origen.mp3"
    audio_fake.write_bytes(b"fake")
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="T", artista="A", destino=tmp_path,
        audio_origen=audio_fake, reportar=mensajes.append,
    )
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(str(carpeta / "song.ini"), encoding="utf-8")
    campos = {k.lower(): v.lower() for s in parser.sections() for k, v in parser.items(s)}
    assert campos["album"] == "99.9"
    assert campos["year"] == "2019"
    assert campos["genre"] == "j-rock"
    assert campos["diff_guitar"] == "4"  # Expert con gema (pista_sintetica)
    assert campos["diff_drums"] == "4"
    assert campos["diff_bass"] == "0"  # Expert sin gemas
    assert campos["diff_band"] == "0"  # min(guitarra, bajo, bateria)
    assert campos["diff_vocals"] == "0"
    assert campos["pro_drums"] == "false"
    assert "delay" not in campos and "song_length" not in campos
    assert any("carátula" in m for m in mensajes), "aviso de carátula ausente"


def test_song_ini_caratula_embebida(tmp_path, rutas_audio, pista_sintetica, monkeypatch):
    """#4: si el audio trae carátula, se incluye como album.jpg."""
    def _extraer(_audio, destino):
        Path(destino).write_bytes(b"\xff\xd8\xfffake")
        return Path(destino)

    monkeypatch.setattr(
        "chartforge.etapas.empaquetado.leer_tags", lambda _a: {}
    )
    monkeypatch.setattr(
        "chartforge.etapas.empaquetado.extraer_caratula", _extraer
    )
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="T", artista="A", destino=tmp_path,
        audio_origen=tmp_path / "origen.mp3", reportar=lambda *a, **k: None,
    )
    assert (carpeta / "album.jpg").is_file()


def test_song_ini_sin_audio_origen(tmp_path, rutas_audio, pista_sintetica):
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="T", artista="A", destino=tmp_path,
    )
    contenido = (carpeta / "song.ini").read_text(encoding="utf-8")
    assert "album" not in contenido
    assert not (carpeta / "album.jpg").exists()


def test_notes_chart_roundtrip(tmp_path, rutas_audio, pista_sintetica):
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="Titulo", artista="Artista", destino=tmp_path,
    )
    texto = (carpeta / "notes.chart").read_text(encoding="utf-8")
    parseado = parsear_chart(texto)
    # [Song]: Name/Artist/Offset/Resolution
    assert parseado[("Song", "meta", "Name")] == ("Titulo",)
    assert parseado[("Song", "meta", "Artist")] == ("Artista",)
    assert parseado[("Song", "meta", "Resolution")] == ("192",)
    assert parseado[("Song", "meta", "Offset")] == ("0",)
    # [SyncTrack]: tempo 120 * 1000 + TS 4
    assert parseado[("SyncTrack", 0, "B")] == (120000,)
    assert parseado[("SyncTrack", 0, "TS")] == (4,)
    # gemas conocidas: gema de guitarra en tick 0 lane 2; de bateria tick 0 lane 0
    assert parseado[("ExpertSingle", 0, "N")] == ((2, 0),)
    assert parseado[("ExpertDrums", 0, "N")] == ((0, 0),)
    # letra en [Events] global (sin pista Vocals)
    assert "lyric hola" in parseado[("Events", 192, "E")]
    assert not any(seccion.endswith("Vocals") for (seccion, _t, _tipo) in parseado)


def test_audio_ogg_por_stem(tmp_path, rutas_audio, pista_sintetica):
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista_sintetica,
        titulo="Artista", artista="Titulo", destino=tmp_path,
    )
    for archivo_esperado in NOMBRES_AUDIO_STEMS.values():
        ruta = carpeta / archivo_esperado
        assert ruta.is_file(), f"falta {archivo_esperado}"
        info = sf.info(str(ruta))
        assert info.format == "OGG", f"{archivo_esperado} no es OGG: {info.format}"
        assert info.samplerate == SR
        assert abs(info.frames / info.samplerate - DURACION_S) < 0.5


def test_error_stem_desconocido(tmp_path, rutas_audio, pista_sintetica):
    stems = _stems_de(rutas_audio)
    stems["teclado"] = rutas_audio["guitarra"]  # no existe en NOMBRES_AUDIO_STEMS
    with pytest.raises(ValueError):
        crear_carpeta_cancion(
            stems, rutas_audio["mix"], pista_sintetica,
            "Artista", "Titulo", tmp_path,
        )


def test_no_falla_con_letra_vacia(tmp_path, rutas_audio):
    pista = PistaCancion(bpm=120.0, letra=None, gemas={"guitarra": {"Expert": [Gema(0, 2, 0)]}})
    carpeta = crear_carpeta_cancion(
        _stems_de(rutas_audio), rutas_audio["mix"], pista,
        titulo="B", artista="A", destino=tmp_path,
    )
    texto = (carpeta / "notes.chart").read_text(encoding="utf-8")
    assert '"#sin-letras"' in texto
