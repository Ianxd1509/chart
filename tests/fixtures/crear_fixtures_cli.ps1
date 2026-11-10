$ErrorActionPreference = 'Stop'
Set-Location D:\charf1
# fake.mp3: texto con extension mp3 (ffprobe debe fallar)
Set-Content -Path "tests\fixtures\fake.mp3" -Value "esto no es audio" -Encoding UTF8
# tono.mp3: senoide 440 Hz de 5 s
ffmpeg -y -v error -f lavfi -i "sine=frequency=440:duration=5" -ar 44100 -ac 2 -b:a 96k "tests\fixtures\tono.mp3"
"D:\\charf1\\tests\\fixtures\\tono.mp3 creado; fake.mp3 creado"
(Get-Item tests\fixtures\fake.mp3).Length
(Get-Item tests\fixtures\tono.mp3).Length
