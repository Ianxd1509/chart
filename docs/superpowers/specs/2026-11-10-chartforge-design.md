# Diseño — ChartForge (nombre provisional)

Fecha: 2026-11-10 · Rev. 2 (versión consola)
Estado: aprobado por el usuario (el borrador web se sustituye por la versión consola a petición del usuario el 2026-11-10)
Origen: análisis RE de autochart.eu (evidencias `ev_ff0fef…`, `ev_e3fdde4…`) + encargo del usuario: "que haga lo mismo que AutoChart pero gratis, para mí, localmente".

## 1. Intención y porqué

ChartForge es un **conversor de consola local** (sin servidor ni navegador) que convierte una canción MP3/FLAC en una **carpeta de canción jugable en Clone Hero y YARG**:

- arrastras el MP3/FLAC sobre el icono `convertir.bat` (o lo abres y pegas la ruta),
- la ventana de consola muestra el progreso etapa por etapa,
- al terminar, la carpeta `<Artista> - <Titulo>` queda en `D:\charf1\CL`, lista para que Clone Hero la escanee.

La motivación es tener la función de AutoChart.eu sin pagar créditos y sin subir audio a servidores de terceros: **todo el procesamiento ocurre en la máquina del usuario**.

## 2. Metas, no-metas y anti-metas

**Metas**
- Pipeline completo: separación de stems → letras sincronizadas → charting por instrumento → empaquetado de carpeta de canción.
- Charts jugables en Clone Hero (y YARG) sin edición manual (correctos, no "autora profesional").
- Las 4 dificultades (Easy/Medium/Hard/Expert) para drums, guitar, bass, vocals.
- Letras con tiempos por palabra si el modelo las produce; línea a línea como mínimo.
- Audio por pista (mute-miss: al fallar una nota, tu instrumento sale de la mezcla).
- Uso en español y sin navegador: arrastrar el audio sobre `convertir.bat` → progreso en consola → canción lista en `CL\`.
- Todo instalable con un script; sin dependencias de nube.

**No-metas**
- Sin cuentas, créditos, pagos, referidos, analítica, correos ni páginas legales.
- No replicar la marca, textos, ni diseño visual de AutoChart.eu.
- No soportar ediciones manuales tipo Mojo/Moonscraper (deja editar la salida con herramientas existentes).
- Sin multiusuario ni servidor web: un solo usuario local, una canción a la vez.

**Anti-metas (fracaso incluso si "funciona")**
- Colgar la memoria del equipo o llenar el disco durante una conversión.
- Silenciar errores o fingir progreso: si una etapa falla, el proceso aborta con mensaje claro en español y no deja carpeta a medias en `CL\`.
- Enviar nada por red salvo la descarga puntual de dependencias/modelos durante la instalación.

## 3. Raíces y límites medidos del entorno

- CPU Intel i3-1005G1 (2 núcleos/4 hilos, 1.2 GHz), RAM 7.8 GB, GPU Intel UHD (sin CUDA)
- Discos: C: (SSD sistema) con solo 20.3 GB libres; **D: (HDD Toshiba 1 TB) con 458.3 GB libres** → el proyecto completo vive en D:
- Implicaciones: modelo CPU-only; una conversión a la vez; guardas de recursos sobre la **unidad del proyecto (D:)**; una conversión ~10–30 min según canción (el cuello de botella es la CPU, no el disco)
- Python 3.12 y ffmpeg 8.1 ya instalados (en C:)

## 4. Enfoques considerados

| Enfoque | Qué era | Veredicto |
|---|---|---|
| **A. Conversor de consola con arrastre (elegido)** | Pipeline entero en una ventana de consola; se usa arrastrando el audio sobre `convertir.bat` | Elegido por el usuario tras el borrador web ("más fácil"): sin servidor ni navegador; el motor es el mismo |
| B. Mini-app web local (descartado) | Servidor local + página única con progreso por etapas | Experiencia tipo autochart, pero más código y más superficie de fallo; descartado a petición del usuario |
| C. Aceleración en nube (Colab) | GPU gratis a cambio de cuenta Google | Anti-metas: no local, requiere cuenta |

## 5. Arquitectura

### 5.1 Resumen

```
[Explorer]  arrastra MP3/FLAC sobre convertir.bat
    v
[CLI (chartforge.cli), ventana de consola]
    valida (extensión MP3/FLAC, ffprobe, ≤20 min, ≤200 MB, disco D: ≥4 GB)
    confirma título/artista  (Enter = autocompletado desde el nombre del archivo)
    v
[pipeline en el mismo proceso: etapas en serie, progreso impreso en consola]
    wav normalizado -> demucs htdemucs (segment calibrado) -> stems 16-bit
    stems           -> faster-whisper base                 -> letras con tiempos
    stems           -> motor charting (librosa)            -> notes.chart
    stems + mix     -> ffmpeg                              -> song.ogg + stems OGG
    todos           -> song.ini + carpeta "Artista - Titulo"
    v
[D:\charf1\CL\<Artista> - <Titulo>]   (sin ZIP)
```

### 5.2 Componentes

1. **CLI (`chartforge/cli.py`, arrancada por `convertir.bat`)**
   - `convertir.bat`: usa como argumentos los archivos arrastrados; si se abre sin arrastrar nada, pide pegar la ruta. Una canción a la vez; si le arrastras varias, las hace secuencialmente.
   - Valida cada archivo (extensión MP3/FLAC, decodificable por ffprobe, duración ≤ 20 min, tamaño ≤ 200 MB, disco libre ≥ 4 GB en D:). Si algo falla: mensaje claro en español y el proceso termina con código ≠ 0, sin crear nada en `CL\`.
   - Título/artista: autocompletados desde el nombre del archivo; la consola los muestra para confirmar (Enter = aceptar) antes de gastar 10–30 min de CPU.
   - Progreso: cada etapa imprime su cabecera (`[2/5] stems (demucs)`) y porcentaje/tiempo transcurrido.

2. **Pipeline (mismo proceso de la CLI, etapas en serie)**
   - **adquisición**: decodifica con ffmpeg a WAV 44.1 kHz; normaliza pico a −1 dBFS.
   - **stems (demucs)**: `htdemucs` CPU, hasta ~20 min, `segment` y `batch` calibrados a 7.8 GB RAM (medición del spike del plan). Intermedios: `drums.wav`, `bass.wav`, `other.wav`, `vocals.wav` en `tmp\<job>\`.
   - **letras (faster-whisper)**: modelo `base` multilingüe (configurable); timestamps por palabra alineados al stem vocals; idioma autodetectado o override en config. Si no hay letra fiable: canción marcada `#sin-letras` y vocals por onsets.
   - **charting (motor propio, módulo `chartgen/`)**:
     - drums: onsets sobre el stem drums; clase por banda espectral (kick=baja, caja=media-transitoria, cymbal=alta); fills automáticos en compases vacíos; sin Expert+ kicks salvo doble pedal claro (configurable off).
     - guitar: sobre el stem `other` (demucs aísla el bajo aparte): onsets + pitch salience; acordes = gemas múltiples; sustain por continuidad de tono.
     - bass: igual sobre el stem `bass`.
     - vocals: onsets sobre el stem vocals + alineado a palabras del paso de letras.
     - cuantización a grid de BPM (tempo estimado con librosa; si inestable, grid por onsets); 4 dificultades por distribución de densidad (percentiles).
     - jugable por diseño: gema mínima 1/16 a BPM>160 en Expert, acordes máx. 4 gemas, sin notas solapadas en la misma lane.
   - **empaquetado**: escribe `song.ini` (name, artist, delay=0, charter="ChartForge"), `notes.chart` (texto estándar de la comunidad; `notes.mid` opcional si la investigación lo facilita), `song.ogg` + stems OGG (ffmpeg VBR q6) con nombres validados (§7); deja la carpeta lista.

3. **Salida (`D:\charf1\CL`)**: `<Artista> - <Titulo>` con caracteres seguros para Windows/CH. La carpeta se escribe en el `tmp` del job y se **mueve a `CL\` solo al terminar** → nunca queda una canción a medias en el juego. Sin ZIP: apuntas la carpeta de canciones de Clone Hero a `D:\charf1\CL` (Settings) y listo.

4. **Config (`config.ini`)**: `carpeta_salida=CL` (junto al proyecto, editable), modelo whisper (`base`), demucs (`htdemucs`, segmento, batch), letras on/off. La ventana de consola es el único estado: no hay jobs ni registros en memoria.

### 5.3 Dependencias (instalación por script `instalar.ps1`)

```
torch (cpu), demucs, faster-whisper, librosa, soundfile, psutil
```
Total estimado ~4-6 GB (torch domina). Modelos pre-descargados por el script: htdemucs (~500 MB), whisper base (~150 MB).
Script: verifica Python y ffmpeg, crea `venv\` dentro del proyecto, pip install con `PIP_CACHE_DIR=D:\charf1\.pipcache` (nunca infla C:), descarga modelos con barra, deja `convertir.bat` listo. Desinstalar = borrar la carpeta del proyecto.

## 6. Calidad de charting — expectativa honesta

Motor determinista basado en onsets, tono y energía: los charts serán correctos (jugables, sincronizados, estilos coherentes) pero no con la calidad de autoría a mano de un chartista profesional, y probablemente inferiores al resultado de AutoChart en densidad/estilo en canciones muy complejas. La mejora iterativa del motor es trabajo posterior; el diseño deja el módulo `chartgen/` aislado para reemplazar heurísticas por modelos mejores si surge uno abierto que lo justifique.

## 7. Formatos de salida — a validar en la fase de plan

La lógica es la que la comunidad espera; en la fase de plan se validará ANTES de codear contra:
- nombres exactos de los archivos de audio en packs Clone Hero/YARG (song.ogg, drums_1.ogg, bass.ogg, vocals_1.ogg, other.ogg…),
- sintaxis de `notes.chart` (posiciones, eventos de sección, SyEvents de letras) y/o salida a `notes.mid` MIDI estándar,
- campos mínimos de `song.ini` que ambos juegos exigen,
- comportamiento de mute-miss con stems (qué archivo exige cada juego).

Fuente de verdad: repositorios documentados (Clone Hero Docs, YARG docs, Moonscraper directamente del código, catálogo de uso común). Nada de estos formatos se inventa en el motor: si la investigación no lo confirma, no se shippea.

## 8. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| RAM 7.8 GB con demucs grandes | segment/batch calibrados en el spike; etapas en serie; borrado obligatorio de intermedios; guardas de memoria entre etapas |
| Disco C: con solo 20.3 GB libres | todo el proyecto (venv, modelos, caché pip, temporales, salida) vive en D:; guard ≤4 GB al empezar y ≤2 GB entre etapas; aviso en consola |
| CPU lenta → desesperanza del usuario | progreso por etapa con porcentaje/tiempo en la consola; modo rápido = sin Expert+ kicks (config) |
| Cierre accidental de la ventana a mitad de conversión | carpeta a medias imposible: la salida se mueve a `CL\` solo al terminar; el siguiente arranque limpia `tmp\` colgados |
| Whisper mala letra en canciones con coros fuertes | opción "sin letras" (chart sin eventos de letra); aviso en consola |
| Formatos CH/YARG mal calculados | investigación documental obligatoria antes de escribir el motor de salida (§7) |

## 9. Decisiones ya tomadas

1. Stack: Python CLI sin servidor (sin FastAPI/uvicorn); pipeline en el mismo proceso. Sin navegador, sin puertos.
2. Nombre provisional: **ChartForge** (carpeta `chartforge/`); el usuario puede renombrarlo.
3. Ubicación del proyecto: **`D:\charf1\`** (elegida por el usuario; D: tiene 458 GB libres frente a los 20.3 de C: — todo lo pesado, venv y modelos incluidos, vive aquí).
4. Uso: arrastrar MP3/FLAC sobre `convertir.bat` (o abrirlo y pegar la ruta); una canción a la vez.
5. Salida: **`D:\charf1\CL\<Artista> - <Titulo>`** (decisión del usuario 2026-11-10: carpeta `CL` junto al proyecto), sin ZIP.
6. `.chart` como formato de notas fuente (texto determinista, debuggable); MIDI opcional tras investigación.

## 10. Pendiente explícito del plan de implementación

- [ ] Investigación de formatos §7 con fuentes citadas.
- [ ] Medición real de tiempo/RAM de demucs en esta CPU con el corpus (spike del plan).
- [ ] Elegir modelo whisper definitivo (base vs small) midiendo precisión/tiempo.
- [ ] Calibrar los ajustes de charting con el corpus de prueba (3 canciones) para dificultad Expert.
- [ ] Test de integración: canción de prueba de 30 s end-to-end hasta carpeta en `CL\` en <15 min.

## 11. Ajustes tras el builder check (2026-11-10)

1. **Criterio de aceptación de "jugable sin edición manual"**: la carpeta de salida se considera aprobada si (a) el juego carga la canción sin errores ni fallos de indexado, (b) las notas caen alineadas a lo audible (sync correcto), (c) las 4 dificultades × 4 instrumentos difieren entre sí y ninguna produce acordes imposibles (>4 gemas simultáneas) ni notas más cortas que el grid permitido del juego, (d) mute-miss funciona con los stems presentes. La sensación subjetiva de calidad queda fuera de la barra de aprobación (mejora iterativa del motor, §6).
2. **Corpus de pruebas**: DISPONIBLE — canciones del usuario en `C:\Users\art64\Downloads\musica de prueba` (3 MP3). El spike, la calibración y el test E2E usan ese corpus.
3. **Instalación**: venv dentro de la carpeta del proyecto (~4-6 GB en `D:\charf1\`), no `pip --user`. Caché de pip dirigida a `D:\charf1\.pipcache` para no inflar C:. La promesa de desinstalación queda verdadera: borrar la carpeta elimina todo (código, venv, modelos, caché). Las guardas de disco cuentan la unidad D:.
4. **Evidencia RE de autochart.eu**: no es un recurso del proyecto. El motor se calibra contra el corpus de pruebas del punto 2, no contra parámetros internos de AutoChart (propietarios e inobservables).
5. **Prioridad de compatibilidad**: RESUELTO — el usuario juega **Clone Hero**. En divergencia de empaquetado, manda Clone Hero (YARG se beneficia salvo diferencia real). La verificación funcional definitiva se hace con la instalación de Clone Hero del usuario, apuntando su carpeta de canciones a `D:\charf1\CL`.
6. **Escalera de recortes si algo desborda**: primero letras por palabra → solo por línea; luego Expert+ kicks (ya opcional); luego `notes.mid` (ya opcional). El núcleo no se recorta: charts de 4 instrumentos × 4 dificultades + audio por pista + `song.ini`/`notes.chart` + carpeta lista en `CL\`.
