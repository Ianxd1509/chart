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
    frases_sp: list[tuple[int, int]] = field(default_factory=list)  # (tick inicio, longitud ticks)
    secciones: list[tuple[int, str]] = field(default_factory=list)   # (tick, nombre) para [Events]

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
                cuerpo += [f"{tick} = S 2 {longitud}" for tick, longitud in self.frases_sp]
                cuerpo.sort(key=lambda linea: int(linea.split("=", 1)[0]))
                parrafos.append(
                    f"[{dificultad}{nombre}]\n" + "{\n" + "\n".join(cuerpo) + "\n}"
                )
        return "\n".join(parrafos) + "\n"

    # ----------------------------------------------------------------------
    def _eventos_texto(self) -> list[str]:
        """[Events] globales: letra (lyric/phrase_*), secciones ("section X") o #sin-letras."""
        lineas_eventos: list[tuple[int, str]] = []

        if self.letra is None:
            lineas_eventos.append((0, '0 = E "#sin-letras"'))
        else:
            ordenadas = sorted(self.letra.palabras, key=lambda p: p[0])
            lineas = sorted(self.letra.lineas, key=lambda l: l[0])
            eventos: list[str] = []
            for indice, (t_linea, _texto) in enumerate(lineas):
                fin_linea = lineas[indice + 1][0] if indice + 1 < len(lineas) else float("inf")
                palabras_linea = [p for p in ordenadas if t_linea <= p[0] < fin_linea]
                eventos.append((ticks_de_tiempo(t_linea, self.bpm),
                                f'{ticks_de_tiempo(t_linea, self.bpm)} = E "phrase_start"'))
                for t_palabra, palabra in palabras_linea:
                    tick = ticks_de_tiempo(t_palabra, self.bpm)
                    eventos.append((tick, LETRA_LINEA(tick, palabra)))
                if palabras_linea:
                    t_fin = max(p[0] for p in palabras_linea)
                else:
                    t_fin = t_linea
                t_tick = ticks_de_tiempo(t_fin, self.bpm)
                eventos.append((t_tick, f'{t_tick} = E "phrase_end"'))
            lineas_eventos.extend(eventos)

        for tick, nombre in self.secciones:
            nombre_limpio = str(nombre).replace('"', "").replace("\\", "").strip() or "Section"
            lineas_eventos.append((int(tick), f'{int(tick)} = E "section {nombre_limpio}"'))

        lineas_eventos.sort(key=lambda par: par[0])
        return [linea for _tick, linea in lineas_eventos]
