"""Test E2E con una cancion REAL completa del corpus (Task 10, slow).

Corre la CLI en subprocess (como convertir.bat) con la cancion 1 del corpus:
demucs + whisper + charting + OGG sobre la cancion entera, y al final la
carpeta debe estar en CL con todos sus archivos y un chart que hace
round-trip. Tarda ~10-30 min; se ejecuta con `pytest -m slow` (o la suite
completa, que tambien incluye los slow). Limpia la carpeta al final (tambien
si falla). El test opera sobre la CL REAL del proyecto (config.RUTA_SALIDA),
nunca sobre tmp_path.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

import chartforge.config as config
from chartforge.formatos import NOMBRE_CARPETA, NOMBRES_AUDIO_STEMS, parsear_chart

CANCION = Path(r"C:\Users\art64\Downloads\musica de prueba\1_spotdown.org.mp3")
TIMEOUT_S = 45 * 60


@pytest.mark.slow
def test_e2e_cancion_completa_del_corpus():
    if not CANCION.is_file():
        pytest.skip("corpus no disponible en esta maquina")

    from chartforge.cli import parsear_titulo_artista

    titulo, artista = parsear_titulo_artista(CANCION.name)
    carpeta = config.RUTA_SALIDA / NOMBRE_CARPETA(artista, titulo)

    inicio = time.monotonic()
    proceso = subprocess.Popen(
        [sys.executable, "-m", "chartforge.cli", str(CANCION)],
        cwd=str(config.RUTA_PROYECTO),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        proceso.stdin.write("\n\n")  # acepta artista y titulo por defecto
        proceso.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    try:
        salida, _ = proceso.communicate(timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.communicate()
        pytest.fail(f"la conversion no termino en {TIMEOUT_S // 60} min")
    duracion = time.monotonic() - inicio
    print(f"\n[e2e] Duracion total de la conversion: {duracion:.0f} s")
    assert proceso.returncode == 0, f"exit code {proceso.returncode}\n{salida[-4000:]}"

    try:
        assert carpeta.is_dir(), f"no quedo la carpeta {carpeta}"
        for nombre in NOMBRES_AUDIO_STEMS.values():
            assert (carpeta / nombre).is_file(), f"falta {nombre}"
        assert (carpeta / "song.ini").is_file()
        ruta_chart = carpeta / "notes.chart"
        parseado = parsear_chart(ruta_chart.read_text(encoding="utf-8"))
        secciones = {clave[0] for clave in parseado}
        assert "SyncTrack" in secciones and "Events" in secciones
        assert any(s.startswith("ExpertSingle") for s in secciones), "guitarra sin Expert"
        assert any(s.startswith("ExpertDrums") for s in secciones), "bateria sin Expert"
        # spec §11.1(c): las 4 dificultades presentes por familia de pista y
        # anidadas Easy⊆Medium⊆Hard⊆Expert (guitarra=Single, bajo=DoubleBass,
        # bateria=Drums; la voz es solo evento global, Ruling Task 2)
        niveles = ("Easy", "Medium", "Hard", "Expert")
        for familia in ("Single", "DoubleBass", "Drums"):
            nombres = [f"{n}{familia}" for n in niveles]
            for nombre in nombres:
                assert nombre in secciones, f"falta la seccion [{nombre}]"
            notas = {
                n: {c[1] for c in parseado if c[0] == f"{n}{familia}" and c[2] == "N"}
                for n in niveles
            }
            assert notas["Easy"], f"[Easy{familia}] sin notas"
            assert (
                notas["Easy"] <= notas["Medium"] <= notas["Hard"] <= notas["Expert"]
            ), f"anidado roto en {familia}"
        eventos = [str(v) for (s, _t, _tipo), vals in parseado.items() if s == "Events" for v in vals]
        assert any("lyric" in ev or "#sin-letras" in ev for ev in eventos)
        print(f"[e2e] Carpeta OK: {carpeta}")
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
