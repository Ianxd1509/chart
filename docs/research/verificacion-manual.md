# Verificación manual en Clone Hero (Task 11, spec §11.1)

Checklist humano, una vez terminado el pipeline automático. El criterio de
aceptación es el del spec (§11.1): la carpeta se aprueba si (a) carga sin
errores, (b) sincroniza, (c) es jugable en las 4 dificultades × 4 instrumentos,
y (d) el mute-miss funciona. La sensación subjetiva de calidad editorial NO es
criterio de aprobación.

## Preparación (una vez)

1. Convertir una canción real (`convertir.bat`) y confirmar que en `D:\charf1\CL`
   quedó la carpeta `<Artista> - <Titulo>` con: `song.ini`, `notes.chart`,
   `song.ogg`, `drums.ogg`, `guitar.ogg`, `bass.ogg`, `vocals.ogg`.
2. En Clone Hero: Settings de songs, agrega la carpeta (`Add Song Folder`)
   con la ruta `D:\charf1\CL` y guarda. Alternativa: copiar la carpeta de la
   canción a la carpeta de canciones que ya usas.
3. En el juego: **Re-scan Songs** y localizar la canción por el nombre.

## Checklist de aprobación

### (a) Carga sin errores
- [ ] La canción aparece en la lista (sin esperar >5 s extra ni colgar el indexado).
- [ ] Entra al juego con Start sin mensajes de error del juego ni de video.
- [ ] El audio arranca en el tiempo 0 con offset normal (sin necesidad de
      ajustar `delay` en song.ini: ChartForge no escribe ese campo).

### (b) Sincronía
- [ ] Con el mix (song.ogg) suena alineado: en Practice (velocidad 100 %),
      un golpe de kick de batería visible no se anticipa ni atrasa respecto
      al audio audible.
- [ ] El sustain de guitarra no termina perceptiblemente antes del audio.
- [ ] Si hay letra, los eventos de letra aparecen en el momento de la palabra.

### (c) Jugabilidad en 4 dificultades × 4 instrumentos
- [ ] **Batería**: Easy tiene pocos golpes (kick y un pad); Hard/Expert
      combinan kick y pads. En Expert nunca exige más de un golpe físico
      simultáneo (sin gemas cuadruplicadas).
- [ ] **Guitarra**: Easy (pocas notas), Medium/Hard más densas, Expert el chart
      completo; acordes de máx. 3 gemas; verificar que no existan acordes de
      4 gemas (imposibles de pisar).
- [ ] **Bajo**: existe y difiere de la guitarra (patrón más escaso que sigue
      su propio stem).
- [ ] Las 4 dificultades DIFIEREN entre sí en cada instrumento (entrar a
      Practice y comparar el número de notas por dificultad).

### (d) Mute-miss (stems)
- [ ] Fallar a propósito notas de guitarra → el stem `guitar.ogg` se silencia
      suave (mute miss) mientras song.ogg sigue.
- [ ] Ídem batería y bajo.
- [ ] La voz (`vocals.ogg`) NO se silencia por gameplay (no es jugable en CH).

## Si algo falla

- Anotar: canción convertida, sección del checklist, instrumento/dificultad,
  y (si aplica) tiempo aproximado de la canción donde ocurre.
- Tipos de fallo esperables y qué módulo sospechar:
  - *No aparece la canción* → `empaquetado` (song.ini, `notes.chart` corrupto).
  - *Dessincronía global* → BPM del beat_track (`pipeline._bpm_de`).
  - *Sobre-notado / notes imposibles* → `chartgen.dificultades` (paneo de
    fusiones y acordes).
  - *Stems no se silencian* → nombre de OGG o ruta (`NOMBRES_AUDIO_STEMS`).
- Con `notes.chart` abierto en Moonscraper se confirma cuál es la sección
  problemática sin reconvertir.
