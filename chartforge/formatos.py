"""Constantes y utilidades del formato Clone Hero/YARG.

Cada regla citada está justificada en docs/research/clone-hero-formatos.md
(con copias crudas de las fuentes en docs/research/raw/).
"""
from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# song.ini (wiki de Clone Hero, "Mandatory Tags": [Song] y name obligatorios;
# delay y song_length NO se escriben: "not recommended")
# ---------------------------------------------------------------------------
CAMPOS_SONG_INI: dict[str, str] = {
    "name": "",   # obligatorio — lo rellena la etapa de empaquetado con el título
    "artist": "",  # recomendado — ídem con el artista
    "charter": "ChartForge",
}

# ---------------------------------------------------------------------------
# Stems de audio (Supported-Audio-Files.md + stems-mixer de OCTAVE; mute-miss:
# CH silencia el stem del instrumento que el jugador falla)
# ---------------------------------------------------------------------------
NOMBRES_AUDIO_STEMS: dict[str, str] = {
    "cancion": "song.ogg",
    "bateria": "drums.ogg",
    "guitarra": "guitar.ogg",
    "bajo": "bass.ogg",
    "voz": "vocals.ogg",
}

# Stem cuya ausencia de sonido evidencia el miss ("mute miss") en cada
# instrumento: None = no jugable en Clone Hero (la voz), no hay muting.
SILENCIA_A_FALLO: dict[str, str | None] = {
    "bateria": "drums.ogg",
    "guitarra": "guitar.ogg",
    "bajo": "bass.ogg",
    "voz": None,
}

# ---------------------------------------------------------------------------
# notes.chart
# ---------------------------------------------------------------------------
RESOLUCION = 192  # ticks por negra (spec F1: valores estándar 192 o 480)

DIFICULTADES: tuple[str, ...] = ("Easy", "Medium", "Hard", "Expert")
# Nombre de instrumento .chart para cada instrumento interno (spec F1: la
# sección es [Dificultad + Instrumento], ejemplos [ExpertSingle], [MediumDrums])
TRACK_INSTRUMENTO: dict[str, str] = {
    "guitarra": "Single",
    "bajo": "DoubleBass",
    "bateria": "Drums",
}

# Lanes válidas por instrumento (spec F1 §N):
#   - guitarra/bajo: frets 0-4, open 7, flags forced=5 y tap=6
#   - bateria: kick=0, lanes 1-4, Expert+ kick=32; sin sustain
LANES_GUITARRA = {0, 1, 2, 3, 4, 5, 6, 7}
LANES_BATERIA = {0, 1, 2, 3, 4, 5, 32}

FASE_INICIO = "phrase_start"  # eventos obligatorios de letra (spec F1 + Lyrics.md)
FASE_FIN = "phrase_end"

_LETRAS_INVALIDAS = re.compile(r'["\\]')
# caracteres prohibidos en nombres de carpeta en Windows
_CARPETA_INVALIDOS = re.compile(r'[\\/:*?"<>|]')
_ESPACIOS = re.compile(r"\s+")
_GUIONES = re.compile(r"-+")

# Parser de líneas de evento: "480 = N 2 96" o '480 = E "lyric hola"'
_LINEA_EVENTO = re.compile(r"^\s*(\d+)\s*=\s*([A-Z]+)\s*(.*)$")
# Tipos cuyo valor es numérico en el formato
_CON_ENTEROS = {"N", "S", "B", "TS", "A"}


def escribir_gema_linea(instrumento: str, lane: int, tick: int, longitud: int = 0) -> str:
    """Línea de nota de notes.chart: "<tick> = N <lane> <sustain>".

    Same formato de ChartWriter de Moonscraper (s_noteFormat = " = N {0} {1}");
    la batería nunca lleva sustain.
    """
    if instrumento == "bateria":
        if lane not in LANES_BATERIA:
            raise ValueError(f"lane {lane} no existe en batería")
        if longitud != 0:
            raise ValueError("la batería no soporta sustains")
    elif instrumento in ("guitarra", "bajo"):
        if lane not in LANES_GUITARRA:
            raise ValueError(f"lane {lane} no existe en guitarra/bajo")
    else:
        raise ValueError(f"instrumento sin gemas: {instrumento!r}")
    if tick < 0:
        raise ValueError("tick negativo")
    return f"{int(tick)} = N {int(lane)} {int(longitud)}"


def LETRA_LINEA(tick: int, palabra: str) -> str:
    """Evento de letra del [Events] global: '<tick> = E "lyric <palabra>"' (spec F1)."""
    if _LETRAS_INVALIDAS.search(palabra):
        raise ValueError("comillas o barra invertida en la letra")
    return f'{int(tick)} = E "lyric {palabra}"'


def NOMBRE_CARPETA(artista: str, titulo: str) -> str:
    """'Artista - Titulo' con los caracteres prohibidos en Windows reemplazados por '-'."""

    def _sanea(parte: str) -> str:
        limpio = _ESPACIOS.sub(" ", _GUIONES.sub("-", _CARPETA_INVALIDOS.sub("-", parte))).strip(" .-")
        return limpio if limpio else "Desconocido"

    return f"{_sanea(artista)} - {_sanea(titulo)}"


def parsear_chart(texto: str) -> dict[tuple, object]:
    """Parser mínimo de notes.chart para round-trip en tests.

    Devuelve un dict con clave tupla:
      ("Seccion", tick, tipo)  -> tupla de eventos parrafo en ese punto
                                  (cada evento: tupla de enteros, o str para E)
      ("Song", "meta", campo)  -> valor de metadata (str)
    """
    resultado: dict[tuple, list[object]] = {}
    seccion = ""
    for linea in (l.strip() for l in texto.splitlines()):
        if not linea or linea in ("{", "}"):
            continue
        if linea.startswith("[") and linea.endswith("]"):
            seccion = linea[1:-1].strip()
            continue
        coincide = _LINEA_EVENTO.match(linea)
        if coincide:
            tick, tipo, resto = int(coincide.group(1)), coincide.group(2), coincide.group(3)
            if tipo == "E" and resto.startswith('"') and resto.endswith('"'):
                resto = resto[1:-1]
            if tipo in _CON_ENTEROS:
                enteros = tuple(int(tok) for tok in resto.split())
                evento: object = enteros[0] if len(enteros) == 1 else enteros
            else:
                evento = resto.strip()
            resultado.setdefault((seccion, tick, tipo), []).append(evento)
            continue
        coincide_meta = re.match(r"^([\w_]+)\s*=\s*(.*)$", linea)
        if coincide_meta and seccion:
            resultado.setdefault((seccion, "meta", coincide_meta.group(1)), []).append(
                coincide_meta.group(2).strip()
            )
    return {clave: tuple(valores) for clave, valores in resultado.items()}
