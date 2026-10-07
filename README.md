# RadeonVideoAI (Reescalar)

Suite de escritorio para Windows que reescala vídeo y mejora su calidad con IA
(elimina ruido, reconstruye detalle y nitidez). Esta es una variante
simplificada, centrada exclusivamente en el reescalado/restauración por IA —
derivada del proyecto completo [RadeonVideoAI](https://github.com/diegomart44/RadeonVideoAI),
que además incluye recreación generativa e interpolación de fotogramas.

Desarrollada y probada en hardware AMD de gama media (**AMD Ryzen 5 2600 +
Radeon RX 9060 XT, 16 GB**), pero la detección de hardware es automática y no
depende de una marca: usa DirectML (DirectX 12), que acelera por GPU en
**NVIDIA, AMD e Intel** por igual sin ninguna configuración manual.

No es un clon binario de Topaz Video AI (sus modelos son propietarios), pero
cubre el mismo flujo funcional — reescalado por IA + desruido + realce de
detalle, con interfaz gráfica, vista previa lado a lado y exportación con
codificación acelerada por hardware — usando modelos de IA reales y con
pesos entrenados públicamente disponibles.

## Cómo funciona la IA

El motor usa las arquitecturas y pesos oficiales de **Real-ESRGAN**
(xinntao/Real-ESRGAN, licencia BSD-3-Clause), que son redes generativas
realmente entrenadas para super-resolución y restauración — no una red con
pesos aleatorios:

| Modelo en la interfaz | Arquitectura | Licencia | Uso recomendado |
|---|---|---|---|
| Universal Video Restoration | SRVGGNetCompact (`realesr-general-x4v3`) | BSD-3-Clause | Rápido, uso general. El deslizador de desruido interpola de verdad entre los pesos "nítido" y "con desruido" (la misma técnica que usa el CLI oficial de Real-ESRGAN). |
| Fine Details & Texture SR | RRDBNet 23 bloques (`RealESRGAN_x4plus`) | BSD-3-Clause | Máxima calidad de detalle en 4x, más lento. |
| Native 2x High Fidelity | RRDBNet 23 bloques (`RealESRGAN_x2plus`) | BSD-3-Clause | Mejor fidelidad que reescalar 4x→2x cuando solo necesitas duplicar la resolución. |
| Realistic Photo/Video Restoration | RRDBNet 23 bloques (`BSRGAN`, cszn/KAIR) | Apache-2.0 | Entrenado con un modelo de degradación más realista; suele lucir mejor en vídeo con ruido/artefactos de compresión reales. |
| Clean Animation & CG | RRDBNet 6 bloques (`RealESRGAN_x4plus_anime_6B`) | BSD-3-Clause | Animación / CG. |
| Community Ultra Sharp | RRDBNet 23 bloques (`4x-UltraSharp`, Kim2091) | **CC BY-NC-SA — solo uso no comercial** | Muy popular en la comunidad por su nitidez agresiva. Usa un tercer formato de checkpoint ("old-arch" ESRGAN, `model.0`/`model.1.sub...`) que el cargador remapea automáticamente a la arquitectura RRDBNet estándar. |

Los pesos (5–67 MB cada uno) se descargan automáticamente la primera vez que
se usa cada modelo, desde las release oficiales de GitHub/Hugging Face, y se
cachean en `models/weights/`.

### Añadir más modelos manualmente (avanzado)

El cargador soporta automáticamente los tres formatos de checkpoint ESRGAN
que circulan en la comunidad (BasicSR/Real-ESRGAN moderno, el "old-arch" de
BSRGAN con nombres `RRDB_trunk`/`upconv1`, y el "old-arch" secuencial de
`model.0`/`model.1.sub...` usado por UltraSharp) — se detectan y remapean
solos. Para añadir un nuevo checkpoint RRDBNet: descarga el `.pth` a
`models/weights/`, añade una entrada en `MODEL_REGISTRY` en `core/models.py`
apuntando a ese archivo (mismos `arch_kwargs` que `x4plus`, ajustando
`num_block` si corresponde), y aparecerá disponible en el desplegable.

### Detección automática de hardware

La app detecta el hardware al arrancar (`core/amd_backend.py`) y no requiere
configuración manual:

- **GPU**: se identifica el fabricante (NVIDIA, AMD o Intel) vía WMI, y el
  cómputo de la red neuronal corre por **ONNX Runtime con el proveedor
  DirectML**. A diferencia de CUDA o ROCm, DirectML no es específico de un
  fabricante, así que el mismo código acelera por GPU en NVIDIA, AMD e Intel
  Arc por igual, con cualquier driver moderno con soporte DirectX 12.
- **VRAM**: se lee el tamaño real desde el registro del driver; en NVIDIA se
  usa además `nvidia-smi` como confirmación. Si no se puede determinar con
  certeza, se asume un valor conservador — el sistema de tiling degrada el
  tamaño de parche automáticamente si hace falta.
- **CPU**: si no hay ninguna GPU con DirectX 12 disponible, la app usa
  automáticamente todos los núcleos físicos de la CPU detectada como
  respaldo.

**Límite honesto:** la aceleración por hardware del *encoder* de salida
(`hevc_amf`/`h264_amf`) sí es específica de AMD (AMF). En NVIDIA/Intel esto
cae automáticamente a `libx265`/`libx264` por software — la IA sigue
corriendo por GPU igual.

### Pipeline de vídeo

- Lectura/escritura de fotogramas en crudo por tuberías binarias de FFmpeg
  (sin archivos intermedios en disco).
- División en parches (tiling) con **fusión por coseno** (cosine feathering)
  para reescalar imágenes grandes sin costuras ni artefactos en los bordes,
  con degradación automática del tamaño de parche si la memoria se satura.
- Codificación de salida acelerada por hardware AMD (`hevc_amf` / `h264_amf`)
  cuando hay una GPU AMD con AMF disponible, con fallback automático a
  `libx265`/`libx264` por software en cualquier otro caso.
- El audio original se preserva intacto (remux sin recodificar).

## Requisitos

- Windows 10/11 64-bit.
- Cualquier GPU con soporte DirectX 12 (NVIDIA, AMD o Intel Arc) — probado
  principalmente en AMD Ryzen 5 2600 + Radeon RX 9060 XT. Sin GPU
  compatible, funciona igual por CPU multi-núcleo, más lento.
- Driver de GPU reciente con soporte DirectX 12/DirectML.
- Python 3.10+ si se ejecuta desde código fuente (no hace falta si usas el
  ejecutable portable compilado).
- Conexión a internet la primera vez que se usa cada modelo de IA (descarga
  de pesos).

## Instalación (modo desarrollo)

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

`ffmpeg.exe` y `ffprobe.exe` ya se incluyen en la raíz del proyecto.

## Compilar versión portable (.exe)

```bat
python build_portable.py
```

Genera `dist/RadeonVideoAI/RadeonVideoAI.exe`, listo para copiar a cualquier
PC con Windows y GPU compatible. Usa `Lanzar_App.bat` para iniciar la app
(detecta automáticamente si hay un ejecutable compilado o si debe correr
desde Python).

## Uso

1. Arrastra un vídeo a la ventana (o usa "Examinar...").
2. Elige factor de reescalado (1x restauración / 2x / 4x) y modelo de IA —
   prueba más de uno con un clip corto para comparar calidad antes de
   procesar el vídeo completo.
3. Ajusta los deslizadores de desruido y nitidez.
4. Ajusta el tamaño de parche según tu VRAM (768–1024 px aprovecha mejor una
   GPU de 16 GB; baja a 384–256 px si ves errores de memoria).
5. Pulsa "REESCALAR VIDEO". El visor central funciona como el comparador de
   Topaz: alterna entre vista **dividida**, **solo original** o **solo
   mejorada**, haz zoom con la rueda del mouse y arrastra para recorrer la
   imagen a máximo detalle — todo se actualiza en vivo mientras procesa. La
   barra inferior muestra FPS, ETA y uso de memoria en tiempo real.

### Sobre la velocidad

La super-resolución por IA real es un proceso pesado en cualquier GPU que no
sea de gama muy alta. Si notas que va lento: usa el modelo "Universal
(rápido)", sube el tamaño de parche a 768–1024 px, o baja la escala a 2x en
vez de 4x. Si el resultado no convence en calidad, compara los distintos
modelos con un clip corto — cada uno tiene fortalezas distintas según el
tipo de contenido (ver tabla arriba).

## Pruebas

```bat
python -m unittest discover -s tests
```

`test_03_ai_model_forward` y `test_e2e.py` requieren red la primera vez
(descargan los pesos oficiales); si no hay conexión, el primero se omite
automáticamente.

## Licencias de los modelos

Los pesos de Real-ESRGAN se distribuyen bajo licencia BSD-3-Clause por sus
autores (xinntao). Revisa el repositorio oficial
(https://github.com/xinntao/Real-ESRGAN) para más detalles antes de un uso
comercial.
