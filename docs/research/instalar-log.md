=== ChartForge instalacion (1/6): ffmpeg ===
ffmpeg OK: C:\Users\art64\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe
=== (2/6): espacio libre en D: ===
Espacio disponible: 458.3 GB libres en D:\
=== (3/6): entorno virtual venv\ ===
Python 3.12.10
=== (4/6): torch solo-CPU (evita bajar CUDA de ~2.5 GB) ===
Looking in indexes: https://download.pytorch.org/whl/cpu
Collecting torch
  Downloading https://download-r2.pytorch.org/whl/cpu/torch-2.15.0%2Bcpu-cp312-cp312-win_amd64.whl.metadata (36 kB)
Collecting filelock (from torch)
  Downloading filelock-4.2.4-py3-none-any.whl.metadata (2.0 kB)
Collecting typing-extensions>=4.13.0 (from torch)
  Downloading typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
Collecting setuptools>=77.0.3 (from torch)
  Downloading https://download.pytorch.org/whl/setuptools-78.1.0-py3-none-any.whl.metadata (6.6 kB)
Collecting sympy>=1.13.3 (from torch)
  Downloading sympy-1.14.0-py3-none-any.whl.metadata (12 kB)
Collecting networkx>=2.5.1 (from torch)
  Downloading networkx-3.7-py3-none-any.whl.metadata (6.7 kB)
Collecting jinja2 (from torch)
  Downloading https://download.pytorch.org/whl/jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting fsspec>=0.8.5 (from torch)
  Downloading fsspec-2026.9.0-py3-none-any.whl.metadata (10 kB)
Collecting mpmath<1.4,>=1.1.0 (from sympy>=1.13.3->torch)
  Downloading mpmath-1.3.0-py3-none-any.whl.metadata (8.6 kB)
Collecting MarkupSafe>=2.0 (from jinja2->torch)
  Downloading https://download.pytorch.org/whl/markupsafe-3.0.3-cp312-cp312-win_amd64.whl.metadata (2.8 kB)
Downloading https://download-r2.pytorch.org/whl/cpu/torch-2.15.0%2Bcpu-cp312-cp312-win_amd64.whl (126.6 MB)
   ---------------------------------------- 126.6/126.6 MB 4.6 MB/s eta 0:00:00
Downloading fsspec-2026.9.0-py3-none-any.whl (221 kB)
Downloading networkx-3.7-py3-none-any.whl (2.1 MB)
   ---------------------------------------- 2.1/2.1 MB 4.6 MB/s eta 0:00:00
Downloading https://download.pytorch.org/whl/setuptools-78.1.0-py3-none-any.whl (1.3 MB)
   ---------------------------------------- 1.3/1.3 MB 1.5 MB/s eta 0:00:00
Downloading sympy-1.14.0-py3-none-any.whl (6.3 MB)
   ---------------------------------------- 6.3/6.3 MB 5.4 MB/s eta 0:00:00
Downloading typing_extensions-4.16.0-py3-none-any.whl (45 kB)
Downloading filelock-4.2.4-py3-none-any.whl (162 kB)
Downloading https://download.pytorch.org/whl/jinja2-3.1.6-py3-none-any.whl (134 kB)
Downloading https://download.pytorch.org/whl/markupsafe-3.0.3-cp312-cp312-win_amd64.whl (15 kB)
Downloading mpmath-1.3.0-py3-none-any.whl (536 kB)
   ---------------------------------------- 536.2/536.2 kB 1.5 MB/s eta 0:00:00
Installing collected packages: mpmath, typing-extensions, sympy, setuptools, networkx, MarkupSafe, fsspec, filelock, jinja2, torch
Successfully installed MarkupSafe-3.0.3 filelock-4.2.4 fsspec-2026.9.0 jinja2-3.1.6 mpmath-1.3.0 networkx-3.7 setuptools-78.1.0 sympy-1.14.0 torch-2.15.0+cpu typing-extensions-4.16.0
=== (5/6): resto del requirements.txt ===
Requirement already satisfied: torch in d:\charf1\venv\lib\site-packages (from -r requirements.txt (line 1)) (2.15.0+cpu)
Collecting demucs (from -r requirements.txt (line 2))
  Downloading demucs-4.1.0-py3-none-any.whl.metadata (20 kB)
Collecting faster-whisper (from -r requirements.txt (line 3))
  Downloading faster_whisper-1.2.1-py3-none-any.whl.metadata (16 kB)
Collecting librosa (from -r requirements.txt (line 4))
  Downloading librosa-1.0.0-py3-none-any.whl.metadata (6.7 kB)
Collecting soundfile (from -r requirements.txt (line 5))
  Downloading soundfile-0.14.0-py2.py3-none-win_amd64.whl.metadata (18 kB)
Collecting psutil (from -r requirements.txt (line 6))
  Downloading psutil-7.2.2-cp37-abi3-win_amd64.whl.metadata (22 kB)
Collecting pytest (from -r requirements.txt (line 7))
  Downloading pytest-9.2.0-py3-none-any.whl.metadata (7.9 kB)
Requirement already satisfied: filelock in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (4.2.4)
Requirement already satisfied: typing-extensions>=4.13.0 in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (4.16.0)
Requirement already satisfied: setuptools>=77.0.3 in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (78.1.0)
Requirement already satisfied: sympy>=1.13.3 in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (1.14.0)
Requirement already satisfied: networkx>=2.5.1 in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (3.7)
Requirement already satisfied: jinja2 in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (3.1.6)
Requirement already satisfied: fsspec>=0.8.5 in d:\charf1\venv\lib\site-packages (from torch->-r requirements.txt (line 1)) (2026.9.0)
Collecting einops (from demucs->-r requirements.txt (line 2))
  Downloading einops-0.8.2-py3-none-any.whl.metadata (13 kB)
Collecting huggingface-hub (from demucs->-r requirements.txt (line 2))
  Downloading huggingface_hub-2.4.0-py3-none-any.whl.metadata (16 kB)
Collecting julius>=0.2.3 (from demucs->-r requirements.txt (line 2))
  Downloading julius-0.2.8-py3-none-any.whl.metadata (7.6 kB)
Collecting lameenc>=1.2 (from demucs->-r requirements.txt (line 2))
  Downloading lameenc-1.9.0-cp312-cp312-win_amd64.whl.metadata (966 bytes)
Collecting pyyaml (from demucs->-r requirements.txt (line 2))
  Downloading pyyaml-6.0.3-cp312-cp312-win_amd64.whl.metadata (2.4 kB)
Collecting safetensors (from demucs->-r requirements.txt (line 2))
  Downloading safetensors-0.8.0-cp310-abi3-win_amd64.whl.metadata (4.2 kB)
Collecting sphn>=0.1.12 (from demucs->-r requirements.txt (line 2))
  Downloading sphn-0.2.1-cp312-cp312-win_amd64.whl.metadata (275 bytes)
Collecting tqdm (from demucs->-r requirements.txt (line 2))
  Downloading tqdm-4.70.1-py3-none-any.whl.metadata (57 kB)
Collecting ctranslate2<5,>=4.0 (from faster-whisper->-r requirements.txt (line 3))
  Downloading ctranslate2-4.8.5-cp312-cp312-win_amd64.whl.metadata (11 kB)
Collecting tokenizers<1,>=0.13 (from faster-whisper->-r requirements.txt (line 3))
  Downloading tokenizers-0.23.3-cp310-abi3-win_amd64.whl.metadata (10 kB)
Collecting onnxruntime<2,>=1.14 (from faster-whisper->-r requirements.txt (line 3))
  Downloading onnxruntime-1.31.1-cp312-cp312-win_amd64.whl.metadata (6.1 kB)
Collecting av>=11 (from faster-whisper->-r requirements.txt (line 3))
  Downloading av-19.0.2-cp312-abi3-win_amd64.whl.metadata (5.1 kB)
Collecting numba>=0.61.0 (from librosa->-r requirements.txt (line 4))
  Downloading numba-0.68.1-cp312-cp312-win_amd64.whl.metadata (2.9 kB)
Collecting numpy>=2.1.0 (from librosa->-r requirements.txt (line 4))
  Downloading numpy-2.5.4-cp312-cp312-win_amd64.whl.metadata (6.6 kB)
Collecting scipy>=1.15.0 (from librosa->-r requirements.txt (line 4))
  Downloading scipy-1.18.1-cp312-cp312-win_amd64.whl.metadata (61 kB)
Collecting scikit-learn>=1.6.0 (from librosa->-r requirements.txt (line 4))
  Downloading scikit_learn-1.9.1-cp312-cp312-win_amd64.whl.metadata (9.3 kB)
Collecting joblib>=1.2 (from librosa->-r requirements.txt (line 4))
  Downloading joblib-1.6.0-py3-none-any.whl.metadata (6.5 kB)
Collecting decorator>=5.2.1 (from librosa->-r requirements.txt (line 4))
  Downloading decorator-5.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting pooch>=1.7 (from librosa->-r requirements.txt (line 4))
  Downloading pooch-1.9.0-py3-none-any.whl.metadata (10 kB)
Collecting soxr>=1.0.0 (from librosa->-r requirements.txt (line 4))
  Downloading soxr-1.1.0-cp312-abi3-win_amd64.whl.metadata (5.8 kB)
Collecting lazy_loader>=0.3 (from librosa->-r requirements.txt (line 4))
  Downloading lazy_loader-0.6-py3-none-any.whl.metadata (6.0 kB)
Collecting msgpack>=1.0.5 (from librosa->-r requirements.txt (line 4))
  Downloading msgpack-1.2.4-cp312-cp312-win_amd64.whl.metadata (8.5 kB)
Collecting cffi>=1.0 (from soundfile->-r requirements.txt (line 5))
  Downloading cffi-2.1.1-cp312-cp312-win_amd64.whl.metadata (2.6 kB)
Collecting colorama>=0.4 (from pytest->-r requirements.txt (line 7))
  Downloading colorama-0.4.6-py2.py3-none-any.whl.metadata (17 kB)
Collecting iniconfig>=2 (from pytest->-r requirements.txt (line 7))
  Downloading iniconfig-2.3.1-py3-none-any.whl.metadata (2.8 kB)
Collecting packaging>=24 (from pytest->-r requirements.txt (line 7))
  Downloading packaging-26.3-py3-none-any.whl.metadata (3.5 kB)
Collecting pluggy<2,>=1.6 (from pytest->-r requirements.txt (line 7))
  Downloading pluggy-1.7.0-py3-none-any.whl.metadata (5.0 kB)
Collecting pygments>=2.15 (from pytest->-r requirements.txt (line 7))
  Downloading pygments-2.21.0-py3-none-any.whl.metadata (2.5 kB)
Collecting pycparser (from cffi>=1.0->soundfile->-r requirements.txt (line 5))
  Downloading pycparser-3.12-py3-none-any.whl.metadata (9.7 kB)
Collecting click<9.0.0,>=8.4.2 (from huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading click-8.5.1-py3-none-any.whl.metadata (2.6 kB)
Collecting hf-xet<2.0.0,>=1.6.0 (from huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading hf_xet-1.8.0-cp38-abi3-win_amd64.whl.metadata (4.9 kB)
Collecting httpx2<3,>=2.0.0 (from huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading httpx2-2.16.0-py3-none-any.whl.metadata (10 kB)
Collecting cloudpickle>=3.0 (from joblib>=1.2->librosa->-r requirements.txt (line 4))
  Downloading cloudpickle-3.1.2-py3-none-any.whl.metadata (7.1 kB)
Collecting llvmlite<0.51,>=0.50.0dev0 (from numba>=0.61.0->librosa->-r requirements.txt (line 4))
  Downloading llvmlite-0.50.0-cp312-cp312-win_amd64.whl.metadata (5.2 kB)
Collecting flatbuffers (from onnxruntime<2,>=1.14->faster-whisper->-r requirements.txt (line 3))
  Downloading flatbuffers-25.12.19-py2.py3-none-any.whl.metadata (1.0 kB)
Collecting protobuf>=4.25.8 (from onnxruntime<2,>=1.14->faster-whisper->-r requirements.txt (line 3))
  Downloading protobuf-7.36.2-cp310-abi3-win_amd64.whl.metadata (595 bytes)
Collecting platformdirs>=2.5.0 (from pooch>=1.7->librosa->-r requirements.txt (line 4))
  Downloading platformdirs-4.14.5-py3-none-any.whl.metadata (5.7 kB)
Collecting requests>=2.19.0 (from pooch>=1.7->librosa->-r requirements.txt (line 4))
  Downloading requests-2.34.2-py3-none-any.whl.metadata (4.8 kB)
Collecting narwhals>=2.0.1 (from scikit-learn>=1.6.0->librosa->-r requirements.txt (line 4))
  Downloading narwhals-2.28.0-py3-none-any.whl.metadata (15 kB)
Collecting threadpoolctl>=3.5.0 (from scikit-learn>=1.6.0->librosa->-r requirements.txt (line 4))
  Downloading threadpoolctl-3.8.0-py3-none-any.whl.metadata (29 kB)
Requirement already satisfied: mpmath<1.4,>=1.1.0 in d:\charf1\venv\lib\site-packages (from sympy>=1.13.3->torch->-r requirements.txt (line 1)) (1.3.0)
Requirement already satisfied: MarkupSafe>=2.0 in d:\charf1\venv\lib\site-packages (from jinja2->torch->-r requirements.txt (line 1)) (3.0.3)
Collecting anyio>=4.10 (from httpx2<3,>=2.0.0->huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading anyio-4.16.0-py3-none-any.whl.metadata (4.7 kB)
Collecting httpcore2==2.16.0 (from httpx2<3,>=2.0.0->huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading httpcore2-2.16.0-py3-none-any.whl.metadata (27 kB)
Collecting idna>=3.18 (from httpx2<3,>=2.0.0->huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading idna-3.20-py3-none-any.whl.metadata (7.2 kB)
Collecting truststore>=0.10 (from httpx2<3,>=2.0.0->huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading truststore-0.10.5-py3-none-any.whl.metadata (4.5 kB)
Collecting h11>=0.16 (from httpcore2==2.16.0->httpx2<3,>=2.0.0->huggingface-hub->demucs->-r requirements.txt (line 2))
  Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting charset_normalizer<4,>=2 (from requests>=2.19.0->pooch>=1.7->librosa->-r requirements.txt (line 4))
  Downloading charset_normalizer-3.5.2-cp312-cp312-win_amd64.whl.metadata (47 kB)
Collecting urllib3<3,>=1.26 (from requests>=2.19.0->pooch>=1.7->librosa->-r requirements.txt (line 4))
  Downloading urllib3-2.8.0-py3-none-any.whl.metadata (7.4 kB)
Collecting certifi>=2023.5.7 (from requests>=2.19.0->pooch>=1.7->librosa->-r requirements.txt (line 4))
  Downloading certifi-2026.10.23-py3-none-any.whl.metadata (2.5 kB)
Downloading demucs-4.1.0-py3-none-any.whl (100 kB)
Downloading faster_whisper-1.2.1-py3-none-any.whl (1.1 MB)
   ---------------------------------------- 1.1/1.1 MB 2.6 MB/s eta 0:00:00
Downloading librosa-1.0.0-py3-none-any.whl (294 kB)
Downloading soundfile-0.14.0-py2.py3-none-win_amd64.whl (1.0 MB)
   ---------------------------------------- 1.0/1.0 MB 1.7 MB/s eta 0:00:00
Downloading psutil-7.2.2-cp37-abi3-win_amd64.whl (137 kB)
Downloading pytest-9.2.0-py3-none-any.whl (411 kB)
Downloading av-19.0.2-cp312-abi3-win_amd64.whl (28.2 MB)
   ---------------------------------------- 28.2/28.2 MB 4.2 MB/s eta 0:00:00
Downloading cffi-2.1.1-cp312-cp312-win_amd64.whl (185 kB)
Downloading colorama-0.4.6-py2.py3-none-any.whl (25 kB)
Downloading ctranslate2-4.8.5-cp312-cp312-win_amd64.whl (20.4 MB)
   ---------------------------------------- 20.4/20.4 MB 4.3 MB/s eta 0:00:00
Downloading decorator-5.3.1-py3-none-any.whl (10 kB)
Downloading huggingface_hub-2.4.0-py3-none-any.whl (857 kB)
   ---------------------------------------- 857.0/857.0 kB 1.8 MB/s eta 0:00:00
Downloading iniconfig-2.3.1-py3-none-any.whl (7.6 kB)
Downloading joblib-1.6.0-py3-none-any.whl (306 kB)
Downloading julius-0.2.8-py3-none-any.whl (21 kB)
Downloading lameenc-1.9.0-cp312-cp312-win_amd64.whl (119 kB)
Downloading lazy_loader-0.6-py3-none-any.whl (8.8 kB)
Downloading msgpack-1.2.4-cp312-cp312-win_amd64.whl (77 kB)
Downloading numba-0.68.1-cp312-cp312-win_amd64.whl (2.8 MB)
   ---------------------------------------- 2.8/2.8 MB 3.6 MB/s eta 0:00:00
Downloading numpy-2.5.4-cp312-cp312-win_amd64.whl (12.6 MB)
   ---------------------------------------- 12.6/12.6 MB 4.1 MB/s eta 0:00:00
Downloading onnxruntime-1.31.1-cp312-cp312-win_amd64.whl (14.9 MB)
   ---------------------------------------- 14.9/14.9 MB 4.1 MB/s eta 0:00:00
Downloading packaging-26.3-py3-none-any.whl (129 kB)
Downloading pluggy-1.7.0-py3-none-any.whl (27 kB)
Downloading pooch-1.9.0-py3-none-any.whl (67 kB)
Downloading pygments-2.21.0-py3-none-any.whl (1.3 MB)
   ---------------------------------------- 1.3/1.3 MB 3.0 MB/s eta 0:00:00
Downloading pyyaml-6.0.3-cp312-cp312-win_amd64.whl (154 kB)
Downloading scikit_learn-1.9.1-cp312-cp312-win_amd64.whl (8.3 MB)
   ---------------------------------------- 8.3/8.3 MB 3.9 MB/s eta 0:00:00
Downloading scipy-1.18.1-cp312-cp312-win_amd64.whl (36.7 MB)
   ---------------------------------------- 36.7/36.7 MB 4.2 MB/s eta 0:00:00
Downloading soxr-1.1.0-cp312-abi3-win_amd64.whl (174 kB)
Downloading sphn-0.2.1-cp312-cp312-win_amd64.whl (1.6 MB)
   ---------------------------------------- 1.6/1.6 MB 3.4 MB/s eta 0:00:00
Downloading tokenizers-0.23.3-cp310-abi3-win_amd64.whl (2.9 MB)
   ---------------------------------------- 2.9/2.9 MB 3.4 MB/s eta 0:00:00
Downloading tqdm-4.70.1-py3-none-any.whl (80 kB)
Downloading einops-0.8.2-py3-none-any.whl (65 kB)
Downloading safetensors-0.8.0-cp310-abi3-win_amd64.whl (355 kB)
Downloading click-8.5.1-py3-none-any.whl (126 kB)
Downloading cloudpickle-3.1.2-py3-none-any.whl (22 kB)
Downloading hf_xet-1.8.0-cp38-abi3-win_amd64.whl (3.9 MB)
   ---------------------------------------- 3.9/3.9 MB 3.8 MB/s eta 0:00:00
Downloading httpx2-2.16.0-py3-none-any.whl (97 kB)
Downloading httpcore2-2.16.0-py3-none-any.whl (85 kB)
Downloading llvmlite-0.50.0-cp312-cp312-win_amd64.whl (41.9 MB)
   ---------------------------------------- 41.9/41.9 MB 4.1 MB/s eta 0:00:00
Downloading narwhals-2.28.0-py3-none-any.whl (490 kB)
Downloading platformdirs-4.14.5-py3-none-any.whl (35 kB)
Downloading protobuf-7.36.2-cp310-abi3-win_amd64.whl (456 kB)
Downloading requests-2.34.2-py3-none-any.whl (73 kB)
Downloading threadpoolctl-3.8.0-py3-none-any.whl (32 kB)
Downloading flatbuffers-25.12.19-py2.py3-none-any.whl (26 kB)
Downloading pycparser-3.12-py3-none-any.whl (62 kB)
Downloading anyio-4.16.0-py3-none-any.whl (134 kB)
Downloading certifi-2026.10.23-py3-none-any.whl (135 kB)
Downloading charset_normalizer-3.5.2-cp312-cp312-win_amd64.whl (207 kB)
Downloading idna-3.20-py3-none-any.whl (69 kB)
Downloading truststore-0.10.5-py3-none-any.whl (19 kB)
Downloading urllib3-2.8.0-py3-none-any.whl (135 kB)
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Installing collected packages: flatbuffers, urllib3, truststore, threadpoolctl, sphn, safetensors, pyyaml, pygments, pycparser, psutil, protobuf, pluggy, platformdirs, packaging, numpy, narwhals, msgpack, llvmlite, lameenc, iniconfig, idna, hf-xet, h11, einops, decorator, colorama, cloudpickle, click, charset_normalizer, certifi, av, tqdm, soxr, scipy, requests, pytest, onnxruntime, numba, lazy_loader, joblib, httpcore2, ctranslate2, cffi, anyio, soundfile, scikit-learn, pooch, julius, httpx2, librosa, huggingface-hub, tokenizers, demucs, faster-whisper
Successfully installed anyio-4.16.0 av-19.0.2 certifi-2026.10.23 cffi-2.1.1 charset_normalizer-3.5.2 click-8.5.1 cloudpickle-3.1.2 colorama-0.4.6 ctranslate2-4.8.5 decorator-5.3.1 demucs-4.1.0 einops-0.8.2 faster-whisper-1.2.1 flatbuffers-25.12.19 h11-0.16.0 hf-xet-1.8.0 httpcore2-2.16.0 httpx2-2.16.0 huggingface-hub-2.4.0 idna-3.20 iniconfig-2.3.1 joblib-1.6.0 julius-0.2.8 lameenc-1.9.0 lazy_loader-0.6 librosa-1.0.0 llvmlite-0.50.0 msgpack-1.2.4 narwhals-2.28.0 numba-0.68.1 numpy-2.5.4 onnxruntime-1.31.1 packaging-26.3 platformdirs-4.14.5 pluggy-1.7.0 pooch-1.9.0 protobuf-7.36.2 psutil-7.2.2 pycparser-3.12 pygments-2.21.0 pytest-9.2.0 pyyaml-6.0.3 requests-2.34.2 safetensors-0.8.0 scikit-learn-1.9.1 scipy-1.18.1 soundfile-0.14.0 soxr-1.1.0 sphn-0.2.1 threadpoolctl-3.8.0 tokenizers-0.23.3 tqdm-4.70.1 truststore-0.10.5 urllib3-2.8.0
powershell : 
En línea: 1 Carácter: 25
+ ...  D:\charf1; powershell -NoProfile -ExecutionPolicy Bypass -File "D:\c ...
+                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (:String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
[notice] A new release of pip is available: 25.0.1 -> 26.3
[notice] To update, run: D:\charf1\venv\Scripts\python.exe -m pip install --upgrade pip
=== (6/6): descarga de modelos dentro de modelos\ ===
Espacio disponible: 456.7 GB libres en D:\charf1
TORCH_HOME = D:\charf1\modelos\torch
HF_HOME = D:\charf1\modelos\hf
Descargando modelo demucs htdemucs...
D:\charf1\venv\Lib\site-packages\huggingface_hub\file_download.py:149: UserWarning: `huggingface_hub` cache-system 
uses symlinks by default to efficiently store duplicated files but your machine does not support them in 
D:\charf1\modelos\hf\hub\models--adefossez--HTDemucs. Caching files will still work but in a degraded version that 
might require more space on your disk. This warning can be disabled by setting the `HF_HUB_DISABLE_SYMLINKS_WARNING` 
environment variable. For more details, see https://huggingface.co/docs/huggingface_hub/how-to-cache#limitations.
To support symlinks on Windows, you either need to activate Developer Mode or to run Python as an administrator. In 
order to activate developer mode, see this article: 
https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development
  warnings.warn(message)
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits 
and faster downloads.
D:\charf1\venv\Lib\site-packages\huggingface_hub\file_download.py:149: UserWarning: `huggingface_hub` cache-system 
uses symlinks by default to efficiently store duplicated files but your machine does not support them in 
D:\charf1\modelos\hf\hub. Caching files will still work but in a degraded version that might require more space on 
your disk. This warning can be disabled by setting the `HF_HUB_DISABLE_SYMLINKS_WARNING` environment variable. For 
more details, see https://huggingface.co/docs/huggingface_hub/how-to-cache#limitations.
To support symlinks on Windows, you either need to activate Developer Mode or to run Python as an administrator. In 
order to activate developer mode, see this article: 
https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development
  warnings.warn(message)
demucs htdemucs listo (42.0M parßmetros)
Descargando modelo whisper base (Systran/faster-whisper-base)...

Fetching 6 files:   0%|          | 0/6 [00:00<?, 
?it/s]D:\charf1\venv\Lib\site-packages\huggingface_hub\file_download.py:149: UserWarning: `huggingface_hub` 
cache-system uses symlinks by default to efficiently store duplicated files but your machine does not support them in 
D:\charf1\modelos\hf\hub\models--Systran--faster-whisper-base. Caching files will still work but in a degraded version 
that might require more space on your disk. This warning can be disabled by setting the 
`HF_HUB_DISABLE_SYMLINKS_WARNING` environment variable. For more details, see 
https://huggingface.co/docs/huggingface_hub/how-to-cache#limitations.
To support symlinks on Windows, you either need to activate Developer Mode or to run Python as an administrator. In 
order to activate developer mode, see this article: 
https://docs.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development
  warnings.warn(message)

Fetching 6 files:  17%|#6        | 1/6 [00:00<00:01,  2.85it/s]
Fetching 6 files:  33%|###3      | 2/6 [00:00<00:00,  4.18it/s]
Fetching 6 files:  50%|#####     | 3/6 [00:00<00:00,  4.84it/s]
Fetching 6 files:  67%|######6   | 4/6 [00:00<00:00,  4.98it/s]
Fetching 6 files:  83%|########3 | 5/6 [00:01<00:00,  2.58it/s]
Fetching 6 files: 100%|##########| 6/6 [01:41<00:00, 34.21s/it]
Fetching 6 files: 100%|##########| 6/6 [01:41<00:00, 16.91s/it]
whisper base listo
Modelos descargados dentro de modelos\ del proyecto.
convertir.bat creado en D:\charf1
Tamanos finales: venv = 1241.1 MB; modelos = 221.3 MB; cache pip = 311.8 MB
Instalacion completa. Para convertir una cancion, arrastra un MP3/FLAC sobre convertir.bat.
