# ChartForge — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conversor de consola local: se arrastra un MP3/FLAC sobre `convertir.bat` y se obtiene la carpeta de canción Clone Hero/YARG completa (stems + charts 4 instrumentos × 4 dificultades + letras sincronizadas + audio por pista) en `D:\charf1\CL\<Artista> - <Titulo>`, sin nube.

**Architecture:** CLI Python en ventana de consola (sin servidor ni navegador): `convertir.bat` pasa las rutas arrastradas a `chartforge.cli`, que valida cada archivo, confirma título/artista (Enter = autocompletado) y corre el pipeline en el mismo proceso por etapas en serie (adquisición → stems demucs → letras whisper → charting librosa → empaquetado ffmpeg) imprimiendo progreso. La carpeta de la canción se escribe en el `tmp` del job y se mueve atómicamente a `D:\charf1\CL\` al terminar (sin ZIP). Proyecto autocontenido: venv + modelos + caché pip dentro → desinstalar = borrar carpeta.

**Tech Stack:** Python 3.12 (venv en el proyecto), torch CPU, demucs, faster-whisper, librosa, soundfile, psutil, ffmpeg 8.1 (ya en sistema), pytest.

**Spec:** `docs/superpowers/specs/2026-11-10-chartforge-design.md` (leer junto al plan; el plan aplica sus decisiones, incluidas las §11).

## Global Constraints

- Python: venv en `D:\charf1\venv\` — **todo** python/pytest/pip se invoca como `venv\Scripts\python.exe ...` (nunca el Python global, salvo crear la venv).
- Proceso CLI único: una canción a la vez, etapas en serie en el mismo proceso. Sin servidor, sin puertos, sin red en runtime.
- Caché de pip: toda llamada pip del instalador exporta `PIP_CACHE_DIR=D:\charf1\.pipcache`; `.pipcache\` en `.gitignore`.
- Entrada: MP3/FLAC, ≤200 MB, ≤20 min (ffprobe). Todos los mensajes y prompts en español.
- Modelos dentro del proyecto (`modelos\`) con `TORCH_HOME=modelos\torch` y `HF_HOME=modelos\hf` (desinstalar la carpeta = limpiar todo).
- Guarda de disco sobre D:: no empezar conversión con <4 GB libres; abortar etapa con <2 GB. Los WAV intermedios se borran al terminar cada etapa; la salida se mueve a `CL\` solo al final (nunca carpeta a medias); al arrancar la CLI se limpian temporales colgados en `tmp\`.
- Formatos de salida: la verdad la fija el Task 2 (`docs/research/clone-hero-formatos.md` + constantes en `chartforge/formatos.py`); no se shippea ningún formato sin cita. Clone Hero manda en divergencias (spec §11.5).
- Carpeta de salida: `D:\charf1\CL\<Artista> - <Titulo>` con caracteres seguros para Windows/CH (no `\/:*?"<>|`); sin ZIP.
- Tests: pytest con marcador `slow` para los que ejecutan demucs/whisper reales (>2 min); los demás corren <60 s sin modelos.
- Commits pequeños por paso, mensajes convención en inglés (`feat:`, `test:`, `chore:`).
- Corpus de pruebas real: `C:\Users\art64\Downloads\musica de prueba\` (3 MP3: `1_spotdown.org.mp3`, `99.9_spotdown.org.mp3`, `99_spotdown.org.mp3`).

## Review Focus

1. **Archivo no-MP3/FLAC o corrupto con extensión válida** → mensaje en español, código de salida ≠ 0, y ninguna carpeta creada en `CL\`; nunca un proceso colgado. Test en Task 5 (fixture MP3 que es texto).
2. **Nombres de archivo sucios** ("99.9_spotdown.org.mp3", espacios, guiones) → título/artista autocompletados a partir del nombre y carpeta "Artista - Titulo" sin caracteres ilegales; el juego indexa la carpeta sin warnings. Tests en Tasks 5 y 8.
3. **Disco/RAM al límite a mitad de conversión** → error claro en español, intermedios borrados, nada parcial en `CL\`, la CLI sigue usable para la siguiente canción. Test en Task 9.
4. **Ctrl+C o cierre de la ventana a mitad de conversión** → no queda carpeta a medias en `CL\`; el siguiente arranque limpia temporales colgados en `tmp\`. Test en Task 9 (kill del proceso + segunda corrida).
5. **Canción sin letra detectable** (instrumental o voz ruidosa) → chart de vocals generado por onsets con evento `#sin-letras` y carpeta igualmente válida; no crashea ni deja secciones raras. Test en Task 7.

---

### Task 1: Arranque del repo y estructura

**Files:**
- Create: `.gitignore` (venv/, tmp/, .pipcache/, CL/, modelos/ con excepción .gitkeep), `README.md` (stub), `requirements.txt` (torch, demucs, faster-whisper, librosa, soundfile, psutil), `config.ini`, `chartforge/__init__.py`, `chartforge/config.py` (Task solo lo escribe en Step 4), `tests/__init__.py`, `tests/test_config.py`
- Create dirs: `docs/research/`, `chartforge/etapas/`, `chartforge/chartgen/`, `modelos/` (con `.gitkeep`), `CL/` (con `.gitkeep`, no ignorado del arranque pero sí del git)

**Interfaces:**
- Produces: `chartforge.config.cargar_config(ruta: str = "") -> dict` (defaults si falta config.ini); constantes `RUTA_MODELOS`, `RUTA_SALIDA` resueltas relativas a la raíz del proyecto (nunca al CWD).

- [ ] **Step 1: git init + árbol de carpetas y archivos stub** (config.ini con `[salida] carpeta=CL`, `[stems] modelo=htdemucs segmento=6 batch=1`, `[letras] activada=true modelo=base`).
- [ ] **Step 2: escribir el test que falla** — `tests/test_config.py::test_defaults_ok`: importa config y corrobora carpeta de salida `CL`, modelo demucs `htdemucs`, modelo letras `base`, y que `RUTA_SALIDA` apunta a `<raíz>\CL` aunque el CWD sea otro.
- [ ] **Step 3: correr con Python global (venv no existe aún):** `python -m pytest tests/test_config.py -v` → FAIL (ImportError).
- [ ] **Step 4: implementar `chartforge/config.py`.**
- [ ] **Step 5: correr el test** → PASS.
- [ ] **Step 6: commit** `chore: project skeleton`.

### Task 2: Investigación de formatos Clone Hero (bloqueante de Tasks 7-8)

**Files:**
- Create: `docs/research/clone-hero-formatos.md`, `chartforge/formatos.py`, `tests/test_formatos.py`

**Interfaces:**
- Produces (consumen Tasks 7, 8, 9): `chartforge.formatos` con datos confirmados con cita:
  - `CAMPOS_SONG_INI`: dict de pares requeridos (name, artist, album, genre, year, charter="ChartForge", delay=0…).
  - `NOMBRES_AUDIO_STEMS`: dict instrumento→nombre exacto de archivo, más qué stem silencia cada instrumento para mute-miss.
  - `escribir_gema_linea(instrumento, lane, tick, longitud: int = 0) -> str`: línea exacta de `notes.chart` para una gema (con sustain si longitud > 0).
  - `LETRA_LINEA(tick, texto) -> str`: evento de letra exacto (SyEvent).
  - `NOMBRE_CARPETA(artista, titulo) -> str`: sanitizado para Windows/CH.
  - `parsear_chart(texto) -> dict[tuple]`: parser mínimo de round-trip para tests.
- Consumes: nada previo; `tests/test_formatos.py` valida la forma del módulo (claves no vacías, round-trip escribir→parsear reproduce la gema).

- [ ] **Step 1: buscar fuentes primarias en la web** (docs de Clone Hero, docs de YARG, código del ChartReader de Moonscraper, guías de charting de la comunidad) — guardar cada enlace + cita literal como bulletpoints.
- [ ] **Step 2: escribir `docs/research/clone-hero-formatos.md`** con exactamente: (a) campos mínimos de song.ini que ambos juegos exigen, (b) nombre exacto de cada stem y su papel en mute-miss, (c) sintaxis completa de `notes.chart`: `[meta]` (BPM, Offset, Resolution), `[InstrumentTrack]` (Name, NEvents/SEvents/líneas de nota `tick lane longitud`, SyEvents de letra, secciones).
- [ ] **Step 3: escribir `tests/test_formatos.py::test_constantes_presentes`** — falla porque el módulo no existe.
- [ ] **Step 4: escribir `chartforge/formatos.py`** según el doc del Step 2.
- [ ] **Step 5: correr pytest** → PASS.
- [ ] **Step 6: commit** `feat: clone hero format research + constants`.

### Task 3: Instalador y descarga de modelos

**Files:**
- Create: `instalar.ps1`, `convertir.bat`, `chartforge/descarga_modelos.py`, `tests/test_instalador_imports.py`
- Uses system Python solo para `python -m venv venv`; todo lo demás dentro de la venv con `PIP_CACHE_DIR=D:\charf1\.pipcache`.

**Interfaces:**
- Produces: `venv\Scripts\python.exe -c "import torch, demucs, faster_whisper, librosa, soundfile, psutil"` exit 0; `python -m chartforge.descarga_modelos --todo` descarga demucs htdemucs + whisper base dentro de `modelos\` con barra y reporta espacio libre en D:; `convertir.bat` raíz ejecuta `venv\Scripts\python.exe -m chartforge.cli %*`.

- [ ] **Step 1: escribir el test de imports del venv** (skip con mensaje español "correr instalar.ps1 primero" si `venv\` no existe).
- [ ] **Step 2: escribir `instalar.ps1`** — pasos con eco: comprobar ffmpeg y espacio en D: ≥20 GB; `python -m venv venv`; pip install torch (índice CPU) y luego requirements.txt; `python -m chartforge.descarga_modelos --todo` (con `TORCH_HOME`/`HF_HOME` del proyecto); crear `convertir.bat`.
- [ ] **Step 3: ejecutar `instalar.ps1`** y capturar en `docs/research/instalar-log.md` la salida real (incluye tamaños finales de venv y modelos).
- [ ] **Step 4: correr test de imports** → PASS.
- [ ] **Step 5: commit** `feat: installer + model predownload`.

### Task 4: Spike demucs + whisper (medición real en esta CPU)

**Files:**
- Create: `docs/research/spike-demucs.md`, `chartforge/etapas/stems.py`, `chartforge/etapas/letras.py`, `tests/test_stems.py`
- Consumes: Task 3 (venv + modelos); corpus real (Global Constraints).

**Interfaces:**
- Produces: `etapas.stems.extraer_stems(audio: Path, destino: Path, cfg: dict) -> dict[str, Path]` (claves drums/bass/other/vocals → WAV 16-bit 44.1 kHz); `etapas.letras.transcribir(wav_vocals: Path, cfg: dict) -> list[tuple[float, str]]` (palabras con tiempo). Config defaults que vengan de la medición.
- Test: `tests/test_stems.py::test_extraer_stems_30s`, marcado `slow`; usa clip de 30 s del corpus (ffmpeg trim) — verifica 4 archivos y duración ≈30 s ±0.1.

- [ ] **Step 1: con ffmpeg, fabricar `tests/fixtures/clip30.mp3`** (30 s del primer MP3 del corpus, 96 kbps).
- [ ] **Step 2: escribir el test slow que falla** (la función no existe).
- [ ] **Step 3: implementar `chartforge/etapas/stems.py`** (API demucs con `TORCH_HOME=modelos\torch`; segmento/batch de cfg) **y `chartforge/etapas/letras.py`** (faster-whisper a WAV mono 16 kHz).
- [ ] **Step 4: `python -m pytest tests/test_stems.py -m slow -v`** — medir con psutil tiempo total y RAM pico del stem de 30 s; registrar en `docs/research/spike-demucs.md`.
- [ ] **Step 5: medición whisper fuera de tests:** transcribir clip30 con `base` y con `small` (descarga small a `modelos\hf` si falta), comparar tiempo y texto contra lo audible del corpus; elegir modelo y escribirlo en `config.ini` citando la medición.
- [ ] **Step 6: correr 1 canción completa del corpus con demucs** (manual, no test) para estimar duración real por canción; anotarla en el spike doc.
- [ ] **Step 7: revisar config.ini** — si la medición exige segmento/batch distinto, actualizar citando la medición.
- [ ] **Step 8: commit** `feat: stems + lyrics stages + performance measurements`.

### Task 5: CLI — entrada, validación y cola de archivos

**Files:**
- Create: `chartforge/cli.py`, `chartforge/pipeline.py` (stub: su firma real se rellena en Task 9), `tests/test_cli_entrada.py`
- Fixtures: `tests/fixtures/fake.mp3` (archivo de texto con extensión .mp3), `tests/fixtures/tono.mp3` (sinusoide 5 s vía ffmpeg).

**Interfaces:**
- Produces (lo que consumen Tasks 8-10):
  - `cli.ErrorEntrada(Exception)` con `mensaje` en español.
  - `cli.validar_archivo(ruta: Path) -> None` — lanza `ErrorEntrada` si: no existe, extensión ≠ .mp3/.flac, ffprobe no decodifica, duración > 1200 s, tamaño > 200 MB.
  - `cli.parsear_titulo_artista(nombre_archivo: str) -> tuple[str, str]` — pura: quita extensión, prefijos numéricos basura ("99", "99.9"), marcas de sitio ("spotdown.org"), divide por " - " si existe.
  - `cli.main(args: list[str]) -> int` — sin args: pega la ruta por `input()`; con 1+: las procesa en orden. Por cada archivo: validar → confirmar título/artista (default del nombre; Enter acepta) → `pipeline.run_pipeline(...)` → imprime resultado. Exit 0 si todas ok, 1 si alguna falla, sin crear nada en `CL\`.
  - `pipeline.run_pipeline(audio: Path, titulo: str, artista: str, cfg: dict, reportar: Callable[[str, float | None, str], None]) -> Path` — stub en este task (crea carpeta destino con un marcador); firma final idéntica en Task 9.

- [ ] **Step 1: escribir tests que fallan** — (a) `validar_archivo(fake.mp3)` lanza `ErrorEntrada` con mensaje español; (b) `validar_archivo(tono.mp3)` no lanza; (c) `parsear_titulo_artista("99.9_spotdown.org.mp3")` no devuelve "99.9" ni "spotdown.org" en título ni artista; (d) `main([tono.mp3])` con `run_pipeline` stub (monkeypatch) crea la carpeta destino correcta en `CL\` y devuelve 0; (e) `main([fake.mp3])` devuelve 1 sin crear carpeta en `CL\`.
- [ ] **Step 2: `python -m pytest tests/test_cli_entrada.py -v`** → FAIL.
- [ ] **Step 3: implementar cli.py + pipeline.py (stub)**.
- [ ] **Step 4: pytest** → PASS.
- [ ] **Step 5: commit** `feat: cli entry + validation + file queue`.

### Task 6: Etapa adquisición + extracción de features de stems

**Files:**
- Create: `chartforge/etapas/adquisicion.py`, `chartforge/chartgen/features.py`, `tests/test_features.py`

**Interfaces:**
- Produces (consume Task 7):
  - `adquisicion.decodificar(audio: Path, destino_wav: Path) -> Path` — ffmpeg → WAV 44.1 kHz; normaliza pico a −1 dBFS; fallo → `ErrorEntrada` con mensaje español.
  - `chartgen.features.ExtraccionStems(ruta_drums, ruta_bass, ruta_other, ruta_vocals, sr=44100)` con métodos:
    - `onsets(nombre_stem: str) -> np.ndarray[float]` (librosa onset_detect con backtrack).
    - `energias_bandas(nombre_stem: str, onsets: np.ndarray) -> pd.DataFrame[tiempo, baja, media, alta]` (energía STFT en 3 bandas por onset).
    - `pitch_principal(nombre_stem: str, tiempos: np.ndarray) -> np.ndarray[float | NaN]` (librosa pyin en ventana corta).
  - El audio se carga una vez y se lee en streaming (`soundfile`) para no duplicar RAM.

- [ ] **Step 1: escribir tests deterministas con fixtures sintéticas** — click a 120 BPM en drums.wav y ruido blanco en other.wav: onsets ≈ tiempos esperados (±30 ms), energía del click concentrada en banda `baja`, pitch NaN en ruido homogéneo.
- [ ] **Step 2: pytest FAIL → Step 3: implementar → Step 4: pytest PASS → Step 5: commit** `feat: acquisition + stem features`.

### Task 7: Chartgen — drums, guitar, bass, vocals + 4 dificultades

**Files:**
- Create: `chartforge/chartgen/drums.py`, `chartforge/chartgen/guitar_bass.py`, `chartforge/chartgen/vocals.py`, `chartforge/chartgen/dificultades.py`, `chartforge/chartgen/modelo.py` (Gema, PistaCancion, Letra), `tests/test_chartgen.py`

**Interfaces:**
- Consumes: Task 6 (ExtraccionStems), Task 2 (formatos/ticks).
- Produces (consumen Tasks 8-9):
  - `modelo.Gema(tick: int, lane: int, longitud: int = 0)`; `modelo.Letra(palabras: list[tuple[float, str]], lineas: list[tuple[float, str]])`; `modelo.PistaCancion` con `to_chart_text(metadatos) -> str` usando `formatos.escribir_gema_linea` y `formatos.LETRA_LINEA`.
  - `drums.generar(feat: ExtraccionStems) -> dict[str, list[Gema]]` (por dificultad): kick en `lane 0` (onsets de banda baja fuerte), snare `lane 1` (media transitoria), cymbal `lane 4` (alta); kick cuantizado a grid de 1/4; compás vacío → fill de por bandas (máx. 16 gemas/compás en Expert).
  - `guitar_bass.generar(feat, stem: str["other"|"bass"]) -> dict[str, list[Gema]]` — gemas por onset, lane 0-4 por pitch; acordes: onsets dentro de 50 ms fusionados (máx. 3); sustain si el pitch sostiene ≥1/4 sin variar >1 semitono.
  - `vocals.generar(feat, letra: Letra | None) -> dict[str, list[Gema]]` — con letra: gemas por palabra a su tiempo; sin letra (Review Focus 5): gemas por onsets del stem vocals y evento `#sin-letras`.
  - `dificultades.aplicar(gemas_expert: dict[str, list[Gema]], bpm: float) -> dict[str, dict[str, list[Gema]]]` — Easy/Medium/Hard/Expert por percentiles de densidad (p05-25 / p25-50 / p50-75 / resto); Expert nunca gemas separadas <1/16 a BPM>160 (fusión de gemas cercanas); sin acordes >4 por diseño.

- [ ] **Step 1: escribir tests con fixtures sintéticas exactas** — click 120 BPM → chart Expert con kick en cada beat y cero acordes >4; melodía determinista (seno de 220→440 Hz en segmentos) → gemas en lanes según pitch, sustain donde el tono se sostiene; vocals sin letra → gemas generadas + `#sin-letras`; dificultades: núcleo común Easy ⊆ Medium ⊆ Hard ⊆ Expert y densidad ascendente.
- [ ] **Step 2: pytest FAIL → Step 3: implementar → Step 4: pytest PASS → Step 5: commit** `feat: chartgen instrument generators + difficulties`.

### Task 8: Empaquetado — song.ini, notes.chart, audio OGG y carpeta

**Files:**
- Create: `chartforge/etapas/empaquetado.py`, `tests/test_empaquetado.py`

**Interfaces:**
- Consumes: Task 2 (CAMPOS_SONG_INI, NOMBRES_AUDIO_STEMS, NOMBRE_CARPETA, parsear_chart), Task 7 (PistaCancion).
- Produces (consume Task 9): `empaquetado.crear_carpeta_cancion(stems_wav: dict[str, Path], mix_wav: Path, pista: PistaCancion, titulo: str, artista: str, destino: Path) -> Path` — escribe en `destino` la carpeta `<Artista> - <Titulo>` sanitizada con: `song.ini` (campos de CAMPOS_SONG_INI + sección [Song] con delay=0), `notes.chart` (meta BPM + secciones + letras si hay), `song.ogg` + un OGG por stem según NOMBRES_AUDIO_STEMS (ffmpeg VBR q6). Devuelve la ruta de la carpeta. **No toca CL\ ni crea ZIP.**

- [ ] **Step 1: escribir el test que falla** — con stems sintéticos de 2 s: carpeta creada con nombre sanitizado ("Bad \/Char" → limpio), song.ini con campos ⊇ requeridos, notes.chart con round-trip vía `parsear_chart` que reproduce las gemas, y archivos de audio exactos según NOMBRES_AUDIO_STEMS.
- [ ] **Step 2: pytest FAIL → Step 3: implementar → Step 4: pytest PASS → Step 5: commit** `feat: song folder packaging`.

### Task 9: Pipeline completo + guardas de recursos + movimiento atómico a CL

**Files:**
- Modify: `chartforge/pipeline.py` (cableado real: adquisición → stems → letras → charting (Tasks 6-7) → empaquetado (Task 8) a `tmp\<job>\`, luego **mover a `RUTA_SALIDA`**), `chartforge/cli.py` (usa el pipeline real; limpia `tmp\` colgado al arrancar)
- Create: `tests/test_pipeline_guardas.py`

**Interfaces:**
- Consumes: todas las etapas (Tasks 4, 6, 7, 8).
- Produces: `run_pipeline` completo con la firma del Task 5. Reglas: `reportar(etapa, percent|None, mensaje)` con 5 etapas en orden; borra intermedios tras cada etapa; guarda entre etapas (disco D: ≥2 GB, RAM libre ≥1.5 GB vía psutil) → error en español + limpieza de tmp + nada movido a `CL\`; Ctrl+C/kill → finally limpia tmp y garantiza CL intacto.

- [ ] **Step 1: escribir tests que fallan** — (a) guardas: monkeypatch de espacio/RAM bajo → error español, `tmp\` vacío y `CL\` sin carpeta nueva; (b) kill a mitad de conversión (subprocess con clip corto, terminate) + segunda corrida limpia `tmp\` y no deja nada a medias en `CL\`; (c) orden de etapas: `reportar` registra las 5 etapas en orden con percent no decreciente dentro de etapa.
- [ ] **Step 2: pytest (a y c, sin modelos) FAIL → implementar → PASS.**
- [ ] **Step 3: test slow con clip30 real end-to-end** → carpeta válida en `CL\` con todo el contenido; borrada al final del test para no ensuciar. `python -m pytest -m slow`.
- [ ] **Step 4: commit** `feat: full pipeline wiring + resource guards`.

### Task 10: Test E2E con canción completa del corpus

**Files:**
- Create: `tests/test_e2e_cancion_real.py`
- Uses: Task 3 (venv+modelos), Task 5 (`cli.main`), corpus completo (Global Constraints). Marcada `slow` (~10-30 min).

**Interfaces:** ninguna nueva — valida el flujo completo: `cli.main([ruta_cancion])` → carpeta en `CL\`.

- [ ] **Step 1: test slow e2e**: corre `cli.main([<canción 1 del corpus>])` en subprocess con timeout 45 min; refrase el progreso hasta exit 0; asserts: carpeta `<Artista> - <Titulo>` en `CL\` con song.ini + notes.chart + song.ogg + stems según NOMBRES_AUDIO_STEMS, y el chart parsea (round-trip Task 2). Limpia la carpeta al terminar.
- [ ] **Step 2: correr una vez y anotar el tiempo real en README.**
- [ ] **Step 3: commit** `test: real-song e2e`.

### Task 11: Cierre — README completo y verificación manual en Clone Hero

**Files:**
- Modify: `README.md` (instalación, uso, desinstalación, tiempos reales), `docs/research/verificacion-manual.md`

- [ ] **Step 1: README** con: requisitos (Windows 11, Python 3.12 vía winget si falta, ffmpeg), pasos de `instalar.ps1`, cómo usar (`convertir.bat` arrastrando o pegando ruta), dónde queda cada cosa (`CL\`, modelos, venv), "desinstalar = borrar carpeta", sección de cuidado de disco (limpiar `.pipcache` si D: queda <8 GB), y cómo apuntar Clone Hero a `D:\charf1\CL` (o copiar la carpeta de la canción).
- [ ] **Step 2: guía de verificación manual** `docs/research/verificacion-manual.md`: checklist del spec §11.1 en CH real (carga sin errores, sync, 4 dificultades × 4 instrumentos, mute-miss con stems).
- [ ] **Step 3: suite completa:** `python -m pytest -v` (sin slow) exit 0 + `python -m pytest -m slow -v` con los slow PASSED.
- [ ] **Step 4: commit** `docs: final readme + manual CH verification guide`.

---

## Pendientes que este plan deja a decisión del constructor

- Modelo whisper final (`base` vs `small`): lo decide la medición del Task 4 Step 5; se escribe en `config.ini` con cita.
- Parámetros finos de onsets/bandas/pitch: la firma y los tests deterministas fijan el comportamiento; el valor fino se ajusta contra el corpus (Tasks 10-11).
- Densidad de dificultades: el esquema de percentiles del Task 7 es el mínimo jugable; se afina con feedback real del Task 11.
