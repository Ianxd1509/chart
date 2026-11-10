"""Tests de entrada del CLI (Task 5): validación de archivos y parseo de nombre."""
from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

import chartforge.cli as cli
import chartforge.config as config

FIXTURES = config.RUTA_PROYECTO / "tests" / "fixtures"
FAKE = FIXTURES / "fake.mp3"
TONO = FIXTURES / "tono.mp3"


@pytest.fixture(autouse=True)
def _sin_limpieza_real_de_tmp(monkeypatch):
    """Ningun test del CLI toca tmp real: borraria jobs EN CURSO del E2E."""
    monkeypatch.setattr(cli.pipeline, "limpiar_tmp_pendiente", lambda: None)


def test_validar_archivo_rechaza_falso_mp3():
    with pytest.raises(cli.ErrorEntrada) as falla:
        cli.validar_archivo(FAKE)
    mensaje = falla.value.mensaje
    assert isinstance(mensaje, str) and mensaje  # mensaje en español, no vacío
    assert "mp3" in mensaje.lower() or "decodificar" in mensaje.lower()


def test_validar_archivo_acepta_tono():
    cli.validar_archivo(TONO)  # no lanza


def test_validar_archivo_pegados_casos():
    with pytest.raises(cli.ErrorEntrada):
        cli.validar_archivo(FIXTURES / "no-existe.mp3")  # inexistente
    ubicacion = FIXTURES / "sin-ext.mp3.tmp"
    ubicacion.write_text("x", encoding="utf-8")
    try:
        with pytest.raises(cli.ErrorEntrada):
            cli.validar_archivo(ubicacion)  # extension invalida
    finally:
        ubicacion.unlink()


def test_parsear_titulo_artista_limpia_basura():
    titulo, artista = cli.parsear_titulo_artista("99.9_spotdown.org.mp3")
    assert "99.9" not in titulo and "99.9" not in artista
    assert "spotdown.org" not in titulo and "spotdown.org" not in artista

    titulo2, artista2 = cli.parsear_titulo_artista("Artista - Cancion.mp3")
    assert (titulo2, artista2) == ("Cancion", "Artista")


def test_main_crea_carpeta_de_salida(monkeypatch, tmp_path):
    """El CLI confirma titulo/artista, corre el pipeline y reporta la carpeta.

    Con el pipeline real (Task 9) main ya no produce un stub: se parchea
    run_pipeline para probar SOLO la orquestacion del CLI sin demucs/whisper.
    """
    entradas = iter(["", ""])  # enter en ambos prompts (acepta defaults)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(entradas))
    monkeypatch.setattr(config, "RUTA_SALIDA", tmp_path)  # carpeta CL de prueba

    def run_fake(audio, titulo, artista, cfg, reportar, salida=None):
        carpeta = tmp_path / f"{artista} - {titulo}"
        carpeta.mkdir()
        (carpeta / "notes.chart").write_text("[Song]\n{\n}\n", encoding="utf-8")
        return carpeta

    monkeypatch.setattr(cli.pipeline, "run_pipeline", run_fake)
    codigo = cli.main([str(TONO)])
    assert codigo == 0
    creado = list(tmp_path.iterdir())
    assert len(creado) == 1  # la carpeta que devolvio el pipeline
    assert creado[0].is_dir()
    assert list(creado[0].iterdir())


def test_main_archivo_invalido_devuelve_1(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "RUTA_SALIDA", tmp_path)
    codigo = cli.main([str(FAKE)])
    assert codigo == 1
    assert list(tmp_path.iterdir()) == []  # no creó nada


def test_main_lee_config_ini_del_proyecto(monkeypatch, tmp_path):
    """El CLI carga config.ini del proyecto (modelo whisper, stems, etc.)."""
    captada: dict = {}

    def run_fake(audio, titulo, artista, cfg, reportar, salida=None):
        captada["cfg"] = cfg
        carpeta = tmp_path / "salida"
        carpeta.mkdir()
        return carpeta

    monkeypatch.setattr(cli.pipeline, "run_pipeline", run_fake)
    entradas = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(entradas))
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)
    monkeypatch.setattr(config, "RUTA_SALIDA", tmp_path / "CL")
    (tmp_path / "config.ini").write_text(
        "[stems]\nmodelo = htdemucs_ft\n[letras]\nmodelo = small\n[extranho]\nx = 1\n",
        encoding="utf-8",
    )
    codigo = cli.main([str(TONO)])
    assert codigo == 0
    assert captada["cfg"]["letras"]["modelo"] == "small"
    assert captada["cfg"]["stems"]["modelo"] == "htdemucs_ft"
    assert captada["cfg"]["letras"]["activada"] is True  # sección ausente usa default


# ---------------------------------------------------------------------------
# [salida] carpeta de config.ini es un knob REAL (revision: Important 8)
# ---------------------------------------------------------------------------
def test_main_honra_carpeta_de_salida_de_config_ini(monkeypatch, tmp_path):
    """`carpeta = MIS_CANCIONES` manda sobre el default CL."""
    captada: dict = {}

    def run_fake(audio, titulo, artista, cfg, reportar, salida=None):
        captada["salida"] = Path(salida) if salida is not None else None
        carpeta = Path(salida) / f"{artista} - {titulo}"
        carpeta.mkdir(parents=True)
        return carpeta

    monkeypatch.setattr(cli.pipeline, "run_pipeline", run_fake)
    entradas = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(entradas))
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)
    monkeypatch.setattr(config, "RUTA_SALIDA", tmp_path / "CL")  # el knob debe ganarle
    (tmp_path / "config.ini").write_text("[salida]\ncarpeta = MIS_CANCIONES\n", encoding="utf-8")
    codigo = cli.main([str(TONO)])
    assert codigo == 0
    assert captada["salida"] == tmp_path / "MIS_CANCIONES"
    assert (tmp_path / "MIS_CANCIONES" / "Desconocido - tono").is_dir()


def test_main_rechaza_carpeta_de_salida_invalida(monkeypatch, tmp_path, capsys):
    """`carpeta = ..\\escape` (o absoluta): ERROR español, sin correr pipeline."""

    def _bomba(*a, **k):
        raise AssertionError("la carpeta invalida debe abortar ANTES del pipeline")

    monkeypatch.setattr(cli.pipeline, "run_pipeline", _bomba)
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)
    (tmp_path / "config.ini").write_text("[salida]\ncarpeta = ..\\escape\n", encoding="utf-8")
    codigo = cli.main([str(TONO)])
    assert codigo == 1
    assert "ERROR" in capsys.readouterr().out


def test_main_config_ini_invalido_es_error_espanol(monkeypatch, tmp_path, capsys):
    """`segmento = seis` rompe _normalizar → ERROR español, exit 1, sin traceback."""

    def _bomba(*a, **k):
        raise AssertionError("con config rota NO se corre el pipeline")

    monkeypatch.setattr(cli.pipeline, "run_pipeline", _bomba)
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)
    (tmp_path / "config.ini").write_text("[stems]\nsegmento = seis\n", encoding="utf-8")
    codigo = cli.main([str(TONO)])
    assert codigo == 1
    salida = capsys.readouterr().out
    assert "ERROR" in salida and "config" in salida.lower()


# ---------------------------------------------------------------------------
# contrato de errores: NUNCA traceback en inglés (revision: Important 1)
# ---------------------------------------------------------------------------
def test_main_captura_errores_de_adquisicion(monkeypatch, tmp_path, capsys):
    """ErrorEntrada desde el pipeline (ffmpeg falla a mitad) → ERROR español."""
    entradas = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(entradas))

    def run_fake(audio, titulo, artista, cfg, reportar, salida=None):
        raise cli.ErrorEntrada('No se pudo decodificar "tono.mp3"')

    monkeypatch.setattr(cli.pipeline, "run_pipeline", run_fake)
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)  # salida de prueba, no CL real
    codigo = cli.main([str(TONO)])
    assert codigo == 1
    salida = capsys.readouterr().out
    assert "ERROR" in salida and "decodificar" in salida.lower()


def test_main_sigue_con_el_siguiente_archivo_tras_error_arbitrario(monkeypatch, tmp_path, capsys):
    """SubprocessError del pipeline → 'ERROR: error inesperado...' y SIGUE."""
    intentos: list[str] = []

    def run_fake(audio, titulo, artista, cfg, reportar, salida=None):
        intentos.append(Path(audio).name)
        if len(intentos) == 1:
            raise subprocess.SubprocessError("ffmpeg se murio")
        carpeta = Path(salida) / f"{artista} - {titulo}"
        carpeta.mkdir(parents=True)
        return carpeta

    monkeypatch.setattr(cli.pipeline, "run_pipeline", run_fake)
    entradas = iter(["", "", "", ""])  # 2 archivos × 2 prompts
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(entradas))
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)  # salida de prueba, no CL real
    codigo = cli.main([str(TONO), str(TONO)])
    assert intentos == ["tono.mp3", "tono.mp3"], "debe continuar con el siguiente archivo"
    assert codigo == 1, "algo fallo en la cola"
    salida = capsys.readouterr().out
    # SubprocessError es error PREVISIBLE (tuple explicito): mensaje directo;
    # los IMPREVISIBLES (LookupError) salen como "error inesperado" (otro test)
    assert "ERROR" in salida and "ffmpeg se murio" in salida


def test_main_catch_final_de_excepciones_desconocidas(monkeypatch, tmp_path, capsys):
    """Un error raro (torch/librosa/etc.) NO imprime traceback; ERROR y sigue."""

    def run_fake(audio, titulo, artista, cfg, reportar, salida=None):
        raise LookupError("no tengo idea de que es esto")

    entradas = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(entradas))
    monkeypatch.setattr(cli.pipeline, "run_pipeline", run_fake)
    monkeypatch.setattr(config, "RUTA_PROYECTO", tmp_path)  # salida de prueba, no CL real
    codigo = cli.main([str(TONO)])
    assert codigo == 1
    salida = capsys.readouterr().out
    assert "ERROR" in salida and "inesperado" in salida.lower()


# ---------------------------------------------------------------------------
# limites de validacion (Review Focus 1, cierre) 
# ---------------------------------------------------------------------------
def test_validar_archivo_rechaza_archivo_pesado(monkeypatch):
    monkeypatch.setattr(cli, "TAMANO_MAXIMO_MB", 0)
    with pytest.raises(cli.ErrorEntrada, match="MB"):
        cli.validar_archivo(FAKE)


def test_validar_archivo_rechaza_duracion_de_mas_de_20_min(monkeypatch):
    monkeypatch.setattr(cli, "_ffprobe_duracion", lambda ruta: 1300.0)
    with pytest.raises(cli.ErrorEntrada, match="maximo 20 min"):
        cli.validar_archivo(TONO)
