$ErrorActionPreference = 'Stop'
Set-Location D:\charf1
$raw = "docs\research\raw"
New-Item -ItemType Directory -Force $raw | Out-Null
# Spec canonica del formato .chart (autor FireFox, via Google Docs export txt)
Invoke-WebRequest -UseBasicParsing -Uri "https://docs.google.com/document/d/1v2v0U-9HQ5qHeccpExDOLJ5CMPZZ3QytPmAG5WF0Kzs/export?format=txt" -OutFile "$raw\spec-chart-firefox.txt"
# Docs de pistas por instrumento (TheNathannator/GuitarGame_ChartFormats, CC0)
$base = "https://raw.githubusercontent.com/TheNathannator/GuitarGame_ChartFormats/main/docs/Chart-File-Formats"
Invoke-WebRequest -UseBasicParsing -Uri "$base/chart-format/Tracks/Drums.md" -OutFile "$raw\Drums.md"
Invoke-WebRequest -UseBasicParsing -Uri "$base/chart-format/Tracks/5-Fret-Guitar.md" -OutFile "$raw\5-Fret-Guitar.md"
Invoke-WebRequest -UseBasicParsing -Uri "$base/chart-format/Tracks/Lyrics.md" -OutFile "$raw\Lyrics.md"
Invoke-WebRequest -UseBasicParsing -Uri "$base/Supported-Audio-Files.md" -OutFile "$raw\Supported-Audio-Files.md"
# Guia de stems (octave) y codigo fuente del escritor de .chart (Moonscraper)
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/opria123/octave/master/docs/guide/stems-mixer.md" -OutFile "$raw\stems-mixer-octave.md"
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/FireFox2000000/Moonscraper-Chart-Editor/master/Moonscraper%20Chart%20Editor/Assets/Scripts/Game/Charts/IO/Chart/ChartIOHelper.cs" -OutFile "$raw\ChartIOHelper.cs"
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/FireFox2000000/Moonscraper-Chart-Editor/master/Moonscraper%20Chart%20Editor/Assets/Scripts/Game/Charts/IO/Chart/ChartWriter.cs" -OutFile "$raw\ChartWriter.cs"
Get-ChildItem $raw | Select-Object Name, Length | Format-Table -AutoSize | Out-String
