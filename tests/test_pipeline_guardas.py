"""Tests del pipeline completo + guardas de recursos (Task 9).

Fijan los Rulings: guardas falla-rapida entre etapas (disco 2 GB, RAM 1.5 GB),
trabajo intermedio en RUTA_PROYECTO\\tmp\\job_<id> y movimiento a CL SOLO al
final, limpiar_tmp_pendiente borra TODO lo pendiente al arrancar la CLI
(regla una-cancion-a-la-vez), orden de 5 etapas con percent=None, y letra
agrupada por pausas > 2 s.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import chartforge.config as config
from chartforge import pipeline
from chartforge.formatos import NOMBRE_CARPETA, NOMBRES_AUDIO_STEMS, parsear_chart

SR = 44100


# ---------------------------------------------------------------------------
# fixtures y fakes de etapas
# ---------------------------------------------------------------------------
@pytest.fixture()
def config_parchado(tmp_path, monkeypatch):
    """Proyecto y CL falsos: pipeline lee config.RUTA_* en runtime."""
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)
    monkeypatch.setattr(config, "RUTA_SALIDA", tmp_path / "CL")
    (tmp_path / "tmp").mkdir()  # ya existe: los asserts de limpieza son fiables
    return tmp_path


def _silencio(ruta: Path, segundos: float = 2.0) -> Path:
    sf.write(str(ruta), np.zeros((int(SR * segundos), 2), dtype=np.float32), SR, subtype="PCM_16")
    return ruta


def _fake_decodificar(audio, destino_wav):
    return _silencio(Path(destino_wav))


def _fake_extraer_stems(audio, destino, cfg, reportar=print):
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    return {n: _silencio(destino / f"{n}.wav") for n in ("drums", "bass", "other", "vocals")}


# ---------------------------------------------------------------------------
# (a) guarda de recursos: fail-rapido, tmp limpio, CL intacta
# ---------------------------------------------------------------------------
def test_guarda_arranque_disponible_antes_de_gastar_cpu(config_parchado, monkeypatch, tmp_path):
    """Disco <4 GB al arrancar (plan Global Constraints): ErrorRecursos español.

    La guarda de 4 GB es de ARRANQUE (antes de decodificar); la de 2 GB es
    entre etapas. Ambas limpian tmp y no crean nada en CL.
    """
    monkeypatch.setattr(pipeline, "ESPACIO_ARRANQUE_BYTES", 1 << 62)  # imposible
    llamadas: list[str] = []
    monkeypatch.setattr(pipeline, "decodificar", lambda *a, **k: llamadas.append("adqui"))
    with pytest.raises(pipeline.ErrorRecursos, match="recursos insuficientes"):
        pipeline.run_pipeline(tmp_path / "cancion.mp3", "Titulo", "Artista")
    assert llamadas == [], "la guarda de arranque corta ANTES de la etapa 1"
    assert list((config.RUTA_PROYECTO / "tmp").iterdir()) == []


def test_guarda_de_recursos_falla_rapido_y_limpia(config_parchado, monkeypatch, tmp_path):
    """Disco 'sin espacio': ErrorRecursos en español, tmp vacio, CL sin carpeta."""
    monkeypatch.setattr(pipeline, "ESPACIO_MINIMO_BYTES", 1 << 62)  # imposible
    llamadas: list[str] = []
    monkeypatch.setattr(pipeline, "decodificar", _fake_decodificar)

    def _no_stems(audio, destino, cfg, reportar=print):
        llamadas.append("stems")
        return {}

    monkeypatch.setattr(pipeline, "extraer_stems", _no_stems)
    with pytest.raises(pipeline.ErrorRecursos, match="recursos insuficientes"):
        pipeline.run_pipeline(tmp_path / "cancion.mp3", "Titulo", "Artista")
    assert llamadas == [], "la guarda corta antes de la etapa siguiente"
    assert list((config.RUTA_PROYECTO / "tmp").iterdir()) == [], "el job se limpia igual"
    assert not (config.RUTA_SALIDA / NOMBRE_CARPETA("Artista", "Titulo")).exists()


# ---------------------------------------------------------------------------
# (c) orden de etapas + integracion con charting/empaquetado reales
# ---------------------------------------------------------------------------
def test_etapas_en_orden_con_salida_en_CL(config_parchado, monkeypatch):
    """5 etapas en orden y percent None; carpeta completa en CL; tmp queda vacio."""
    # umbrales chicos: los umbrales reales dependen de la carga de la maquina
    # (psutil con demucs corriendo en paralelo flanquea); el comportamiento de
    # la guarda ya se prueba aparte con umbral imposible.
    monkeypatch.setattr(pipeline, "ESPACIO_MINIMO_BYTES", 1024 * 1024)
    monkeypatch.setattr(pipeline, "RAM_MINIMA_BYTES", 1024 * 1024)
    registro: list[tuple[str, object, str]] = []

    def reportar(etapa, percent, texto):
        registro.append((etapa, percent, texto))

    monkeypatch.setattr(pipeline, "decodificar", _fake_decodificar)
    monkeypatch.setattr(pipeline, "extraer_stems", _fake_extraer_stems)
    monkeypatch.setattr(
        pipeline, "transcribir", lambda wav, cfg, reportar=print: [(0.5, "hola"), (1.4, "mundo")]
    )

    destino = pipeline.run_pipeline(
        Path("no-importa.mp3"), "Titulo", "Artista", cfg=None, reportar=reportar
    )
    carpeta = config.RUTA_SALIDA / NOMBRE_CARPETA("Artista", "Titulo")
    assert destino == carpeta and carpeta.is_dir()
    # las etapas en orden por PRIMERA aparicion: los avisos de stem vacio
    # (charting) viajan en el mismo reporter y no alteran el orden de etapas
    primeras = list(dict.fromkeys(e for e, _p, _t in registro))
    assert primeras == [
        "adquisicion", "stems", "letras", "charting", "empaquetado",
    ]
    assert all(p is None for _e, p, _t in registro), "percent None; el CLI arma el mensaje"

    for nombre in NOMBRES_AUDIO_STEMS.values():
        assert (carpeta / nombre).is_file(), f"falta {nombre}"
    assert (carpeta / "song.ini").is_file()
    assert (carpeta / "notes.chart").is_file()

    parseado = parsear_chart((carpeta / "notes.chart").read_text(encoding="utf-8"))
    eventos = [
        valor
        for (seccion, _tick, _tipo), valores in parseado.items()
        if seccion == "Events"
        for valor in valores
    ]
    assert any("lyric hola" in str(v) for v in eventos)
    assert any("lyric mundo" in str(v) for v in eventos)

    assert list((config.RUTA_PROYECTO / "tmp").iterdir()) == [], "job eliminado tras mover a CL"


def test_bpm_fallback_en_silencio(config_parchado, monkeypatch):
    """Sin pulso detectable el chart sale a 120 BPM (SyncTrack B 120000)."""
    monkeypatch.setattr(pipeline, "ESPACIO_MINIMO_BYTES", 1024 * 1024)
    monkeypatch.setattr(pipeline, "RAM_MINIMA_BYTES", 1024 * 1024)
    monkeypatch.setattr(pipeline, "decodificar", _fake_decodificar)
    monkeypatch.setattr(pipeline, "extraer_stems", _fake_extraer_stems)
    monkeypatch.setattr(pipeline, "transcribir", lambda wav, cfg, reportar=print: [])
    config.RUTA_SALIDA.mkdir(parents=True, exist_ok=True)
    carpeta = pipeline.run_pipeline(Path("no-importa.mp3"), "A", "B", cfg=None)
    texto = (carpeta / "notes.chart").read_text(encoding="utf-8")
    parseado = parsear_chart(texto)
    assert parseado[("SyncTrack", 0, "B")] == (120000,)
    assert parseado[("Song", "meta", "Offset")] == ("0",)


def test_bpm_nan_cae_al_fallback(monkeypatch, tmp_path):
    """beat_track que devuelve NaN no rompe el chart: fallback a 120.

    `nan < 60` y `nan > 200` son False: NaN atravesaba el filtro y revienta
    en int(round(nan*1000)) con un ValueError en INGLES al final.
    """
    import librosa

    mix = _silencio(tmp_path / "mix.wav")
    monkeypatch.setattr(
        librosa, "load", lambda _ruta, sr=None, mono=None: (np.zeros(100, dtype=np.float32), 22050)
    )
    monkeypatch.setattr(librosa.beat, "beat_track", lambda y, sr: (float("nan"), None))
    assert pipeline._bpm_de(mix) == 120.0


# ---------------------------------------------------------------------------
# letra: agrupacion por pausas
# ---------------------------------------------------------------------------
def test_construir_letra_agrupa_lineas_por_pausa():
    """Pausa > 2 s abre linea nueva; el texto de cada linea une sus palabras."""
    palabras = [(11.0, "frase"), (11.2, "post"), (14.5, "hola"), (14.9, "chao")]
    letra = pipeline.construir_letra(palabras)
    assert letra.palabras == palabras
    assert letra.lineas == [(11.0, "frase post"), (14.5, "hola chao")]


def test_construir_letra_vacia_da_none():
    assert pipeline.construir_letra([]) is None


def test_construir_letra_sanitiza_comillas_y_barras():
    """Whisper puede emitir `"` o `\\`: el chart no puede, se descartan.

    Sin esto, la conversion aborta con ValueError en el ULTIMO paso (2 min de
    demucs gastados). Solo pierde la palabra si queda vacia tras limpiar.
    """
    letra = pipeline.construir_letra([(2.0, 'pa"la'), (2.1, "bra\\slash"), (2.2, '"')])
    assert letra is not None
    assert letra.palabras == [(2.0, "pala"), (2.1, "braslash")]
    assert letra.lineas == [(2.0, "pala braslash")]


def test_construir_letra_solo_prohibidas_da_none():
    assert pipeline.construir_letra([(1.0, '"'), (1.1, "\\")]) is None


# ---------------------------------------------------------------------------
# no sobreescritura de la carpeta destino
# ---------------------------------------------------------------------------
def test_no_sobreescribe_carpeta_existente(config_parchado):
    """"Ya existe" en español y con contenido intacto (sin gastar CPU)."""
    destino = config.RUTA_SALIDA / NOMBRE_CARPETA("Artista", "Titulo")
    destino.mkdir(parents=True)
    (destino / "song.ini").write_text("viejo", encoding="utf-8")
    with pytest.raises(FileExistsError, match="ya existe"):
        pipeline.run_pipeline(Path("no-importa.mp3"), "Titulo", "Artista")
    assert (destino / "song.ini").read_text(encoding="utf-8") == "viejo"


# ---------------------------------------------------------------------------
# limpieza de jobs pendientes
# ---------------------------------------------------------------------------
def test_limpiar_tmp_pendiente_borra_todos_los_jobs(config_parchado):
    """Regla una-cancion-a-la-vez: al arrancar NO hay jobs validos; tmp se vacia."""
    tmp_raiz = config.RUTA_PROYECTO / "tmp"
    (tmp_raiz / "job_viejo").mkdir(parents=True)
    (tmp_raiz / "job_viejo" / "y.wav").write_bytes(b"y")
    (tmp_raiz / "suelto.txt").write_text("x", encoding="utf-8")
    pipeline.limpiar_tmp_pendiente()
    assert list(tmp_raiz.iterdir()) == []


def test_limpiar_tmp_respeta_job_de_conversion_en_curso(config_parchado, capsys):
    """Job con pid+create_time de proceso vivo: no se borra + aviso en español.

    Prohibe el incidente Task 10: una segunda instancia de la CLI borro el
    job de demucs a mitad de separacion y mato la conversion en curso.
    """
    import psutil

    tmp_raiz = config.RUTA_PROYECTO / "tmp"
    vivo = tmp_raiz / "job_vivo"
    vivo.mkdir()
    marca = f"{os.getpid()} {psutil.Process(os.getpid()).create_time():.3f}"
    (vivo / "pid.txt").write_text(marca, encoding="utf-8")
    pipeline.limpiar_tmp_pendiente()
    assert vivo.is_dir(), "la limpieza borro el trabajo de una conversion EN CURSO"
    salida = capsys.readouterr().out.lower()
    assert "conversion en curso" in salida, salida


def test_limpiar_tmp_borra_jobs_muertos_sin_pid_o_basura(config_parchado, monkeypatch):
    """pid muerto, pid.txt con basura o ausente: job de muerto, se borra."""
    monkeypatch.setattr(pipeline, "_proceso_vivo", lambda pid, create_time=None: False)  # determinista
    tmp_raiz = config.RUTA_PROYECTO / "tmp"
    por_hijo = {"job_muerto": "987654321", "job_basura": "no-soy-un-pid", "job_sin_pid": None}
    for nombre, contenido in por_hijo.items():
        carpeta = tmp_raiz / nombre
        carpeta.mkdir()
        if contenido is not None:
            (carpeta / "pid.txt").write_text(contenido, encoding="utf-8")
    (tmp_raiz / "suelto.txt").write_text("x", encoding="utf-8")
    pipeline.limpiar_tmp_pendiente()
    assert list(tmp_raiz.iterdir()) == []


def test_limpiar_tmp_trata_pid_reutilizado_como_muerto(config_parchado):
    """En Windows el pid puede reutilizarse: el create_time discrimina al original
    de una reencarnacion. pid + create_time mio + create_time 1.0 (muy lejano)
    = job de muerto: se borra."""
    import psutil

    tmp_raiz = config.RUTA_PROYECTO / "tmp"
    zombbi = tmp_raiz / "job_pid_reusado"
    zombbi.mkdir()
    (zombbi / "pid.txt").write_text(f"{os.getpid()} 1.0", encoding="utf-8")
    pipeline.limpiar_tmp_pendiente()
    assert not zombbi.exists(), "un pid reutilizado no debe conservar el job ajeno"


# ---------------------------------------------------------------------------
# avisos por instrumento sin gemas (stem silencioso)
# ---------------------------------------------------------------------------
def test_crear_pista_avisa_instrumento_vacio(monkeypatch, tmp_path):
    """Sin gemas para un instrumento → aviso por consola; la conversion sigue.

    Politica fijada por la revision: no se inventa musica, pero el usuario
    debe enterarse de que la pista vacia no fue un error.
    """
    from chartforge.chartgen.modelo import Gema

    mix = _silencio(tmp_path / "mix.wav")
    stems = {n: _silencio(tmp_path / f"{n}.wav") for n in ("drums", "bass", "other", "vocals")}
    monkeypatch.setattr(pipeline, "generar_bateria", lambda feat, bpm: [])
    monkeypatch.setattr(pipeline, "generar_cuerdas", lambda feat, nombre, bpm: [Gema(0, 0)])
    monkeypatch.setattr(pipeline, "generar_voz", lambda feat, letra, bpm: [])
    informes: list[str] = []
    pista = pipeline._crear_pista(mix, stems, [], informar=informes.append)
    texto = " | ".join(informes).lower()
    assert "bateria" in texto and "voz" in texto, texto
    assert "guitarra" not in texto and "bajo" not in texto, texto
    assert pista.bpm == 120.0  # silencio → fallback a 120; igualmente termino


def test_cli_limpia_tmp_pendiente_al_arrancar(monkeypatch, config_parchado, capsys):
    """cli.main limpia tmp ANTES de validar la entrada."""
    llamadas: list[bool] = []
    monkeypatch.setattr(pipeline, "limpiar_tmp_pendiente", lambda: llamadas.append(True))
    from chartforge import cli

    codigo = cli.main(["no-existe.mp3"])
    assert llamadas == [True], "la limpieza va PRIMERO, antes de validar"
    assert codigo == 1
    assert "ERROR" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# (b) SLOW: kill real a mitad de demucs — tmp queda con el job; una corrida
# posterior limpia tmp al arrancar y CL nunca recibio nada a medias
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_kill_mitad_de_proceso_deja_job_y_limpieza_lo_borra():
    clip = config.RUTA_PROYECTO / "tests" / "fixtures" / "clip30.mp3"
    if not clip.is_file():
        pytest.skip("clip30.mp3 (fixture privada, audio de terceros) no esta en el repo publico")
    tmp_raiz = config.RUTA_PROYECTO / "tmp"

    def listar_cl():
        if not config.RUTA_SALIDA.is_dir():
            return []
        return sorted(p.name for p in config.RUTA_SALIDA.iterdir())

    antes = listar_cl()
    proceso = subprocess.Popen(
        [sys.executable, "-m", "chartforge.cli", str(clip)],
        cwd=str(config.RUTA_PROYECTO),
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        proceso.stdin.write(b"\n\n")  # acepta artista y titulo por defecto
        proceso.stdin.close()
    except (BrokenPipeError, OSError):
        pass
    time.sleep(45)
    if proceso.poll() is None:
        proceso.terminate()
    proceso.wait(timeout=120)
    if proceso.returncode == 0:
        pytest.skip("la conversion termino antes del kill; no se puede probar el kill")

    jobs = list(tmp_raiz.glob("job_*")) if tmp_raiz.is_dir() else []
    assert jobs, "despues del kill, el job queda pendiente en tmp"
    assert listar_cl() == antes, "CL no recibe nada cuando la conversion no termino"

    # En Windows la destruccion del hijo pesado (demucs) finaliza de forma
    # ASINCRONA: Windows puede seguir reportando el objeto como existente
    # durante un instante tras wait(), y limpiar_tmp_pendiente decide en ese
    # momento. Soltamos el Popen para cerrar sus handles y reintentamos la
    # limpieza unas veces: el ciclo entero (kill -> arrancar -> tmp limpio)
    # debe funcionar; lo que no se exige es instantaneidad del probe.
    del proceso
    import gc

    gc.collect()
    for intento in range(6):
        pipeline.limpiar_tmp_pendiente()
        if not list(tmp_raiz.glob("job_*")):
            break
        time.sleep(0.5)
    assert not list(tmp_raiz.glob("job_*")), "la corrida siguiente limpia tmp al arrancar"
