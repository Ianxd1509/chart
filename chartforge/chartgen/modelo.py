"""Modelo del chart: Gema, Letra y PistaCancion (Task 7; Task 9 lo arma).

Gema guarda TICKS (conversion t*bpm/60*RESOLUCION, RESOLUCION=192).
to_chart_text produce el texto completo de notes.chart:
[Song] / [SyncTrack] / [Events] (letras globales, sin pista Vocals —
Task 2: CH "has no vocals") / [Dificultad+Instrumento] por pista jugable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from chartforge import formatos
from chartforge.formatos import CAMPOS_SONG_INI, DIFICULTADES, LETRA_LINEA, RESOLUCION, TRACK_INSTRUMENTO

INSTRUMENTO_VOZ = "voz"  # interna: no va como pista en el .chart (S9)


@dataclass(frozen=True)
class Gema:
    """Nota de un chart: tick de 192 por negra, lane del instrumento, sustain en ticks."""
    tick: int
    lane: int
    longitud: int = 0


@dataclass
class Letra:
    """Letra transcrita: palabras y lineas con tiempo en segundos desde 0."""
    palabras: list[tuple[float, str]] = field(default_factory=list)
    lineas: list[tuple[float, str]] = field(default_factory=list)


def ticks_de_tiempo(tiempo: float, bpm: float) -> int:
    """Segundos → ticks: RESOLUCION ticks por negra, bpm negras por minuto."""
    return int(round(tiempo * bpm / 60.0 * RESOLUCION))


def tiempo_de_ticks(tick: int, bpm: float) -> float:
    """Ticks → segundos (inverso de ticks_de_tiempo)."""
    return tick * 60.0 / (bpm * RESOLUCION)


@dataclass
class PistaCancion:
    """Resultado completo del charting: bpm, letra y gemas por instrumento/dificultad."""
    bpm: float
    letra: Letra | None
    gemas: dict[str, dict[str, list[Gema]]]  # instrumento → dificultad → gemas

    # ----------------------------------------------------------------------
    def to_chart_text(self, metadatos: dict[str, str]) -> str:
        """Texto completo de notes.chart: [Song], [SyncTrack], [Events], pistas."""
        if self.bpm <= 0:
            raise ValueError("bpm debe ser positivo")
        parrafos: list[str] = []

        campos_ini = dict(CAMPOS_SONG_INI)
        campos_ini["name"] = metadatos.get("name", "")
        campos_ini["artist"] = metadatos.get("artist", "")
        # [Song] de .chart usa CamelCase (S1): Name, Artist, Charter, Offset, Resolution
        song = [
            f"Name = {campos_ini['name']}",
            f"Artist = {campos_ini['artist']}",
            f"Charter = {campos_ini['charter']}",
            "Offset = 0",
            f"Resolution = {RESOLUCION}",
        ]
        parrafos.append("[Song]\n" + "{\n" + "\n".join(song) + "\n}")

        parrafos.append(
            "[SyncTrack]\n{\n0 = TS 4\n0 = B %d\n}" % int(round(self.bpm * 1000))
        )

        eventos = self._eventos_texto()
        parrafos.append("[Events]\n{\n" + ("\n".join(eventos) if eventos else "") + "\n}")

        for instrumento, nombre in TRACK_INSTRUMENTO.items():
            por_dificultad = self.gemas.get(instrumento, {})
            for dificultad in DIFICULTADES:
                gemas = por_dificultad.get(dificultad, [])
                if not gemas:
                    continue
                cuerpo = [
                    formatos.escribir_gema_linea(instrumento, g.lane, g.tick, g.longitud)
                    for g in sorted(gemas, key=lambda g: (g.tick, g.lane))
                ]
                parrafos.append(
                    f"[{dificultad}{nombre}]\n" + "{\n" + "\n".join(cuerpo) + "\n}"
                )
        return "\n".join(parrafos) + "\n"

    # ----------------------------------------------------------------------
    def _eventos_texto(self) -> list[str]:
        """[Events] globales: letra (lyric/phrase_start/phrase_end) o #sin-letras."""
        if self.letra is None:
            return ['0 = E "#sin-letras"']
        ordenadas = sorted(self.letra.palabras, key=lambda p: p[0])
        lineas = sorted(self.letra.lineas, key=lambda l: l[0])
        eventos: list[str] = []
        for indice, (t_linea, _texto) in enumerate(lineas):
            fin_linea = lineas[indice + 1][0] if indice + 1 < len(lineas) else float("inf")
            palabras_linea = [p for p in ordenadas if t_linea <= p[0] < fin_linea]
            eventos.append(f'{ticks_de_tiempo(t_linea, self.bpm)} = E "phrase_start"')
            for t_palabra, palabra in palabras_linea:
                eventos.append(LETRA_LINEA(ticks_de_tiempo(t_palabra, self.bpm), palabra))
            if palabras_linea:
                t_fin = max(p[0] for p in palabras_linea)
            else:
                t_fin = t_linea
            eventos.append(f'{ticks_de_tiempo(t_fin, self.bpm)} = E "phrase_end"')
        return eventos
