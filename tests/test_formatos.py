"""Tests de chartforge.formatos: constantes del formato Clone Hero con round-trip."""
from __future__ import annotations

import pytest

import chartforge.formatos as fmt


def test_campos_song_ini_presentes():
    assert "name" in fmt.CAMPOS_SONG_INI
    assert "artist" in fmt.CAMPOS_SONG_INI
    assert fmt.CAMPOS_SONG_INI["charter"] == "ChartForge"


def test_campos_song_ini_omite_lo_deprecado():
    assert "delay" not in fmt.CAMPOS_SONG_INI
    assert "song_length" not in fmt.CAMPOS_SONG_INI


def test_nombres_stems_conocidos():
    esperados = {"bateria": "drums.ogg", "guitarra": "guitar.ogg", "bajo": "bass.ogg", "voz": "vocals.ogg"}
    for instrumento, archivo in esperados.items():
        assert fmt.NOMBRES_AUDIO_STEMS[instrumento] == archivo
    assert fmt.NOMBRES_AUDIO_STEMS["cancion"] == "song.ogg"


def test_silencia_a_fallo_por_instrumento():
    assert fmt.SILENCIA_A_FALLO["guitarra"] == "guitar.ogg"
    assert fmt.SILENCIA_A_FALLO["bajo"] == "bass.ogg"
    assert fmt.SILENCIA_A_FALLO["bateria"] == "drums.ogg"
    # la voz no es jugable en CH: no hay stem que silenciar
    assert fmt.SILENCIA_A_FALLO["voz"] is None


def test_gema_guitarra():
    assert fmt.escribir_gema_linea("guitarra", 2, 480, 96) == "480 = N 2 96"
    assert fmt.escribir_gema_linea("guitarra", 7, 240) == "240 = N 7 0"
    assert fmt.escribir_gema_linea("guitarra", 5, 480) == "480 = N 5 0"


def test_gema_bajo_y_bateria():
    assert fmt.escribir_gema_linea("bajo", 0, 192) == "192 = N 0 0"
    assert fmt.escribir_gema_linea("bateria", 0, 96) == "96 = N 0 0"
    assert fmt.escribir_gema_linea("bateria", 32, 768) == "768 = N 32 0"


def test_gema_rechaza_valores_invalidos():
    with pytest.raises(ValueError):
        fmt.escribir_gema_linea("voz", 0, 480)  # la voz no lleva gemas
    with pytest.raises(ValueError):
        fmt.escribir_gema_linea("guitarra", 9, 480)  # lane inexistente
    with pytest.raises(ValueError):
        fmt.escribir_gema_linea("bateria", 3, 480, 50)  # batería sin sustain


def test_letra_linea():
    assert fmt.LETRA_LINEA(576, "hola") == '576 = E "lyric hola"'


def test_fases_de_letra():
    assert fmt.FASE_INICIO == "phrase_start"
    assert fmt.FASE_FIN == "phrase_end"


def test_nombre_carpeta_sano():
    assert fmt.NOMBRE_CARPETA("AC/DC", "Back in Black") == "AC-DC - Back in Black"
    ilegal = 'Bar:"X"|<>'
    assert fmt.NOMBRE_CARPETA(ilegal, "Song?") == "Bar-X - Song"
    assert fmt.NOMBRE_CARPETA("", "") == "Desconocido - Desconocido"


def test_parsear_chart_leyendo_metadata_y_eventos():
    texto = "[Song]\n{\n  Resolution = 192\n  Offset = 0\n}\n"
    texto += "[ExpertSingle]\n{\n  480 = N 2 96\n}\n"
    p = fmt.parsear_chart(texto)
    assert p[("Song", "meta", "Resolution")] == ("192",)
    assert p[("Song", "meta", "Offset")] == ("0",)
    assert p[("ExpertSingle", 480, "N")] == ((2, 96),)


def test_round_trip_gema_y_letra():
    # dos E en el mismo tick (frase + primera palabra) deben sobrevivir al parseo
    gema = fmt.escribir_gema_linea("guitarra", 4, 768, 240)
    texto = (
        "[ExpertSingle]\n{\n" + gema + "\n}\n"
        "[Events]\n{\n"
        '  960 = E "phrase_start"\n' + fmt.LETRA_LINEA(960, "trozo") + "\n}\n"
    )
    p = fmt.parsear_chart(texto)
    assert p[("ExpertSingle", 768, "N")] == ((4, 240),)
    assert p[("Events", 960, "E")] == ("phrase_start", "lyric trozo")
