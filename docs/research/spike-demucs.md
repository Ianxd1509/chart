# Spike Task 4: demucs + whisper en esta CPU (mediciones reales)

Máquina: Windows (venv propia), CPU desconocida — ver libs en `docs/research/instalar-log.md`.
Protocolo reproducible: `docs/research/spike_medicion.py` (tiempo con `time.perf_counter`,
RAM pico con `psutil.Process().memory_info().rss` muestreado cada 0.25-0.5 s).
Resultados crudos: `docs/research/spike-resultados.txt` (clip 30 s) y
`docs/research/spike-cancion-completa.txt` (canción entera del corpus).

## Demucs (htdemucs, segmento 6 s, demucs 4.1.0)

| Medida | clip 30 s |
|---|---|
| tiempo | 80.3 s (~2.7× tiempo real) |
| RAM pico | 1019 MB |

Salida: 4 stems WAV 16-bit PCM 44.1 kHz (`drums`, `bass`, `other`, `vocals`) —
validado por `tests/test_stems.py::test_extraer_stems_30s` (duración 30.0 ± 0.1 s).

Canción completa (corpus, `1_spotdown.org.mp3`, 229.6 s = 3.83 min):
demucs 411.9 s → **factor 1.79× tiempo real** (mejor que el clip: los runs
largos amortizan el arranque), RAM pico **1525 MB**. Detalles en
`spike-cancion-completa.txt`; stems de muestra en `tmp\spike\cancion-completa`
(acceptance manual: escuchar la separación).

**Hallazgo de API (código, no doc)**: `demucs.api.Separator.separate_tensor(wav)`
devuelve `(wav_entrada_resampleada, dict_stems)` — el *dict* va SEGUNDO.
Los stems se alimentan con soundfile tras convertir a WAV con ffmpeg
(demucs 4.1 usa torchaudio para leer, que en Windows no decodifica MP3).

**Hallazgo de modelos**: demucs 4.1 descarga htdemucs vía HuggingFace
(`adefossez/HTDemucs`) a `HF_HOME` (NO al TORCH_HOME del github release del 4.0).
Consecuencia: `HF_HOME=modelos\hf` antes de importar demucs es OBLIGATORIO,
igual que para whisper (una sola ubicación de modelos: `modelos\hf`).

## Whisper (faster-whisper CPU int8, sobre `vocals.wav` del clip)

| modelo | tiempo 30 s | RAM pico | palabras | observación |
|---|---|---|---|---|
| base | 19.8 s | 630 MB | 29 | texto parcial pero coherente |
| small | 420.7 s | 738 MB | 35 | **21× más lento**, texto similar en calidad |

**Decisión: modelo `base`** (ya en `config.ini`): small no mejora el texto en este
clip (aún ruidoso sobre stems de demucs) y cuesta 21× el tiempo. RTF base ≈ 0.66
→ una canción de 5 min ≈ 3-4 min de transcripción. Cambio de modelo = 1 línea en
config.ini si el usuario lo pide.

## Config.ini tras la medición

Sin cambios: `stems/segmento = 6`, `batch = 1` (batch no es configurable en la
API 4.1 — ver Ruling en ledger), `letras/modelo = base`. RAM pico demucs ~1 GB
cabe en las 20 GB+ del requerimiento de espacio/uso.

## Recortes afectados por datos

- Escalera del plan (letras por palabra→línea; Expert+ kicks) no cambió — no se
  necesitó recortar por rendimiento.
- Los temps de demucs dominan el tiempo total: a 1.79× real, una canción de
  ~4 min separa en ~7 min; los 3 del corpus ≈ 20 min de CPU total — corre en
  un solo proceso secuencial (una canción a la vez por diseño del producto).
