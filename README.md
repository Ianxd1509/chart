# ChartForge

Conversor **local y gratuito**: convierte un MP3/FLAC en una carpeta de
canción jugable en **Clone Hero** (YARG acepta el mismo formato de carpeta):
stems de audio por instrumento, charts de 4 instrumentos × 4 dificultades y
letras sincronizadas. Sin nube, sin cuentas, sin editar nada a mano. Una
canción a la vez, todo en una sola carpeta de proyecto.

- Org: Windows 11 consola (arrastrar y soltar; sin navegador, sin servidor).
- Fuente de verdad del diseño: `docs/superpowers/specs/2026-11-10-chartforge-design.md`.
- Formatos Clone Hero/YARG implementados: `docs/research/clone-hero-formatos.md`.
- Licencia: **MIT** (ver `LICENSE`).

## Requisitos

1. **Windows 11** (probado en 11 con CPU Intel, sin GPU).
2. **ffmpeg** en el PATH (`winget install Gyan.FFmpeg`, o descargarlo de
   gyan.dev y agregar su carpeta al PATH).
3. **Python 3.12** en el PATH si el instalador no lo encuentra
   (`winget install Python.Python.3.12`).

## Instalación (una sola vez)

```powershell
cd D:\charf1
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```

El instalador hace 6 pasos y todo queda DENTRO de `D:\charf1\`:

| Carpeta | Uso | Tamaño real |
|---------|-----|-------------|
| `venv\` | entorno virtual con torch CPU y el resto de paquetes | ~1.3 GB |
| `modelos\torch\` | modelo demucs `htdemucs` | ~0.7 GB total con hf |
| `modelos\hf\` | modelo whisper `base` | (dentro del total) |
| `.pipcache\` | caché de pip (solo para reinstalar) | ~0.3 GB |
| `CL\` | carpeta de salida con tus conversiones; ahí la apunta el juego | crece por canción |
| `tmp\` | trabajo intermedio, se limpia solo al arrancar cada conversion | temporal |

Acepta tambien los umbrales de recursos: si el disco del proyecto queda con
menos de 4 GB libres para empezar (o 2 GB entre etapas, o menos de 1.5 GB de
RAM libre), la conversion se detiene con un mensaje en español y no deja nada
a medias en `CL\`.

## Ajustes: config.ini

`config.ini` (junto a `instalar.ps1`) se lee en cada arranque. Secciones:

- `[salida] carpeta = CL`: carpeta de salida junto al proyecto (editable; si
  la cambias, apunta también el juego a esa carpeta).
- `[stems] modelo = htdemucs`, `segmento = 6`: modelo demucs y trozos de CPU.
- `[letras] activada = true`, `modelo = base`, `vad = false`: whisper on/off y su tamaño;
  `small` es ~5x mas lento y en mediciones no escribio mejor que `base`. `vad = true`
  (filtro de voz) era el defecto original y se traga la voz cantada densa
  (medido: las primeras palabras del anime OP salían a los 91 s; con `false`,
  la cobertura quedó casi completa). El default actual es `false`; si ves
  palabras inventadas en instrumentales muy limpios, vuelve a `true`.

## Uso: convertir una canción

1. **Arrastra un MP3 o FLAC sobre `convertir.bat`** (o corre
   `convertir.bat` y pega la ruta del archivo).
2. La consola muestra el artista y título adivinados del nombre del archivo:
   **Enter** los acepta, o escribes otras palabras.
3. La conversión corre 5 etapas con su avance en la consola:
   `adquisición → stems (demucs) → letras (whisper) → charting → empaquetado`.
   Demora **~2× a ~2.5× la duración de la canción** (medido: 3:50 de audio →
   ~9.7 min el E2E completo, ver abajo).
4. Al terminar, la carpeta queda en `CL\<Artista> - <Titulo>` con
   `song.ini`, `notes.chart`, `song.ogg` y el OGG de cada stem
   (`drums.ogg`, `guitar.ogg`, `bass.ogg`, `vocals.ogg`). ¡Nada se instala
   en otra parte! El `song.ini` incluye `album`/`year`/`genre` (si el
   archivo los trae), los `diff_*` segun las dificultades generadas
   (cero = pista vacia) y, cuando el audio trae caratula embebida,
   `album.jpg` en la raiz de la carpeta.

Reglas:

- **No sobreescribe**: si la carpeta destino ya existe, avisa y corta
  (bórrala o renómbrala y vuelve a intentar).
- **Pistas vacías**: si un stem (p. ej. sin batería real) queda sin notas, la
  conversión avisa en consola y esa pista sale vacía; el audio se guarda igual.
- **Batería (v2)**: kick por banda sub (<160 Hz, grid 1/8), snare (350–1000 Hz),
  tom (160–350 Hz tonal, lane blue), cymbal (>4 kHz, lane green); 5 carriles
  estándar (`pro_drums=False`). Es una **heurística tonal**: un tom de ~80-100 Hz
  no se distingue de un bombo; el chart queda completo y jugable, su nivel es
  el de un autobreak genérico, no el de un charter humano.
- **Star Power y secciones**: el chart lleva frases `S 2` (Star Power) en los
  picos de energía del mix y secciones globales `Intro/Verse/Chorus/Outro`
  (aproximación por energía, no entiende la canción). Si la selección del mix
  es ambigua, simplemente no se escriben.
- **Tamaños**: cada canción convertida pesa ~15-40 MB en `CL\` (5 OGG q6 + chart).
- **Letras**: whisper transcribe la voz; si el audio con voz es muy sucio o
  la etapa falla, la canción sale igual con el evento `#sin-letras` (las
  gemas de voz se generan por onsets, el audio `vocals.ogg` siempre está).
- **Canción por vez**: si se abortó o se mató una conversión previa, al
  arrancar la siguiente se limpia `tmp\`.

## Apuntar Clone Hero a tus canciones

En Clone Hero: **Settings ▸ Video/General ▸ Song Folders** → agregar
`D:\charf1\CL` (o copia la carpeta de una canción a tu carpeta de canciones
habitual). Después, **Re-scan Songs**. La verificación paso a paso con el
juego real está en `docs/research/verificacion-manual.md`.

## Exportar una canción como `.sng`

El formato `.sng` es un contenedor único (un archivo por canción) que YARG y
Clone Hero aceptan como alternativa a la carpeta suelta. Para una canción con
la carpeta ya armada en `CL\`:

```powershell
cd D:\charf1
.\venv\Scripts\python.exe -m chartforge.sng "CL\MOB CHOIR, sajou no hana - 99.9"
```

Genera `CL\MOB CHOIR, sajou no hana - 99.9.sng` junto a la carpeta. El `.sng`
contiene `notes.chart` y el resto de los archivos (enmascarados con el spec
público `SNGPKG` v1; `song.ini` se exporta como metadatos, no como archivo).
La implementación es propia (no se copió código de terceros) y está cubierta
por tests con un parser independiente dentro del test (`tests/test_sng.py`).
El `.sng` es opcional: la carpeta suelta ya carga en ambos juegos.

## Desinstalación: borrar la carpeta

**Borra la carpeta `D:\charf1\`** y ya: todo (venv, modelos, caché, código,
canciones convertidas) vive ahí. Nada toca el registro ni carpetas fuera de `D:\`.

## Cuidado del disco

- Si el disco del proyecto queda con **menos de 8 GB libres**, la conversión
  ni arranca (guarda de 4 GB + 2 GB por etapa). Borra `.pipcache\` (se
  re-crea si reinstalas) y `tmp\` (se limpia solo; si un proceso murió a
  medias puede quedar un `job_*` que la limpieza siguiente borra).
- Cada canción convertida ocupa ~15-40 MB en `CL\` (5 OGG q6).

## Tiempos reales medidos (corpus del proyecto)

Corpus de pruebas: 3 MP3 reales en `C:\Users\art64\Downloads\musica de prueba\`.
Medición E2E de la canción 1 (`1_spotdown.org.mp3`, 3:50 de audio; htdemucs
CPU + whisper base int8 + charting + OGG): **~9.7 min (580 s)** por la CLI
completa. La separación con demucs domina el tiempo (de ahí la regla de ~2×).

Regla rápida: **~2× a 2.5× la duración de la canción**, incluida la carga de
modelos (≈1 min que no depende del audio).

## Desarrollo (tests)

```powershell
cd D:\charf1
venv\Scripts\python.exe -m pytest tests -q          # suite rápida + slow (~2-20 min)
venv\Scripts\python.exe -m pytest tests -m slow -q  # solo pruebas con modelos reales
```
