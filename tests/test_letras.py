"""Tests de la etapa de letras con whisper simulado (sin modelo real)."""
from __future__ import annotations

import sys
import types

import pytest

import chartforge.config as config
from chartforge.etapas import letras


def _instalar_fakes(monkeypatch, tardo: float = 8.0):
    """Simula librosa + faster_whisper y devuelve el registrador de llamadas."""
    instancias: list[dict] = []

    librosa = types.ModuleType("librosa")
    librosa.load = lambda *a, **k: ([0.0] * 16000, 16000)

    class _FakeWord:
        def __init__(self, palabra, start):
            self.word = f" {palabra}"
            self.start = start

    class _FakeSegment:
        def __init__(self, words):
            self.words = words

    class WhisperModel:
        def __init__(self, modelo, device, compute_type):
            self.modelo = modelo
            instancias.append({"modelo": modelo, "device": device})

        def transcribe(self, datos, **kwargs):
            instancias[-1]["transcribe"] = kwargs

            def gen():
                yield _FakeSegment([_FakeWord("Hola", 8.0), _FakeWord("mundo", 9.5)])
                yield _FakeSegment([_FakeWord("Otra", 12.0)])

            return gen(), None

    faster_whisper = types.ModuleType("faster_whisper")
    faster_whisper.WhisperModel = WhisperModel

    monkeypatch.setitem(sys.modules, "librosa", librosa)
    monkeypatch.setitem(sys.modules, "faster_whisper", faster_whisper)
    return instancias


def test_transcribir_usa_vad_true_por_defecto(monkeypatch, tmp_path):
    instancias = _instalar_fakes(monkeypatch)
    cfg = config.cargar_config("")
    palabras = letras.transcribir(tmp_path / "vocals.wav", cfg, reportar=lambda *a, **k: None)
    assert instancias[0]["transcribe"]["vad_filter"] is True
    assert [p for _t, p in palabras] == ["Hola", "mundo", "Otra"]
    assert [t for t, _p in palabras] == [8.0, 9.5, 12.0]


def test_transcribir_pasa_vad_desde_config(monkeypatch, tmp_path):
    instancias = _instalar_fakes(monkeypatch)
    cfg = config.cargar_config("")
    cfg["letras"]["vad"] = False
    letras.transcribir(tmp_path / "vocals.wav", cfg, reportar=lambda *a, **k: None)
    assert instancias[0]["transcribe"]["vad_filter"] is False
