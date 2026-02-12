# Report Tecnico: Analisi delle Funzioni `hide_binary_file`

## Indice

1. [PVD: Pixel Value Differencing](#pvd-pixel-value-differencing)
2. [DWT: Discrete Wavelet Transform](#dwt-discrete-wavelet-transform)
3. [Confronto tra i Due Metodi](#confronto-tra-i-due-metodi)

---

## PVD: Pixel Value Differencing

### 📍 File: `src/steganografia/pvd/binary_operations.py`

### Principio di Funzionamento PVD

Il metodo **PVD (Pixel Value Differencing)** nasconde dati sfruttando le **differenze tra coppie di pixel consecutivi**. L'idea chiave è che:

- Differenze piccole tra pixel → pochi bit nascondibili (minore distorsione)
- Differenze grandi tra pixel → più bit nascondibili (distorsione già presente)

Questo rende la steganografia **adattiva**: si nascondono più dati dove l'immagine ha già variazioni naturali.

---

### 🔧 Parametri di Configurazione

```python
RANGES_QUALITY = [
    (0, 7, 2),      # diff 0-7: capacità 2 bit
    (8, 15, 3),     # diff 8-15: capacità 3 bit
    (16, 31, 3),    # diff 16-31: capacità 3 bit
    (32, 63, 4),    # diff 32-63: capacità 4 bit
    (64, 127, 4),   # diff 64-127: capacità 4 bit
]

RANGES_CAPACITY = [
    (0, 7, 3),      # Più aggressivo
    (8, 15, 3),
    (16, 31, 4),
    (32, 63, 5),
    (64, 127, 6),
    (128, 255, 7),  # Range esteso per massima capacità
]

PAIR_STEP: int = 1        # Distanza tra pixel della coppia (default: pixel adiacenti)
CHANNELS = [0, 1, 2]      # Canali RGB utilizzati
```

---

### 📦 Struttura del Payload

Il payload completo è composto da:

```text
┌─────────────┬──────────────┬────────────────┬────────────────┐
│ Magic Header│  File Size   │   File Data    │   Terminator   │
│   16 bit    │   32 bit     │   variabile    │    16 bit      │
└─────────────┴──────────────┴────────────────┴────────────────┘
```

- **Magic Header**: `1010101011110000` (16 bit) - Identifica l'inizio dei dati
- **File Size**: dimensione del file in binario (32 bit, max 4GB)
- **File Data**: contenuto del file convertito in binario
- **Terminator**: `1111000011110000` (16 bit) - Marca la fine dei dati

---

### 🔍 Algoritmo PVD `hide_binary_file` - Step by Step

#### **Step 1: Lettura e Preparazione del File**

```python
with open(file_path, "rb") as f:
    file_data = f.read()

file_size = len(file_data)
file_binary = "".join(format(byte, "08b") for byte in file_data)
```

- Legge il file in modalità binaria
- Converte ogni byte in stringa di 8 bit (es: `0xFF` → `"11111111"`)

#### **Step 2: Costruzione del Payload**

```python
magic_header = "1010101011110000"
size_binary = format(file_size, "032b")
terminator = "1111000011110000"
full_payload = magic_header + size_binary + file_binary + terminator
```

Esempio per un file di 10 byte:

```text
Header:     1010101011110000
Size:       00000000000000000000000000001010  (10 in binario)
Data:       [80 bit del file]
Terminator: 1111000011110000
Total:      144 bit
```

#### **Step 3: Conversione Immagine**

```python
if img.mode != "RGB":
    img = img.convert("RGB")
img_array = np.array(img, dtype=np.int32).copy()
```

- Forza la conversione a RGB (3 canali)
- Usa `int32` per evitare overflow durante le modifiche

#### **Step 4: Embedding Loop (Core dell'Algoritmo)**

```python
bit_index = 0
for channel in BinarySteganography.CHANNELS:  # [0, 1, 2] = R, G, B
    for row in range(height):
        for col in range(0, width - 1, 2 * PAIR_STEP):
            if bit_index >= len(full_payload):
                break

            # Estrae coppia di pixel
            pixel1 = int(img_array[row, col, channel])
            pixel2 = int(img_array[row, col + PAIR_STEP, channel])

            # Determina capacità
            _, _, capacity = BinarySteganography._get_range_capacity(pixel2 - pixel1)

            # Estrae i bit da nascondere
            bits_to_embed = full_payload[bit_index : bit_index + capacity]

            # Nasconde i bit
            if bits_to_embed:
                new_p1, new_p2 = BinarySteganography._embed_in_pair(
                    pixel1, pixel2, bits_to_embed
                )
                img_array[row, col, channel] = new_p1
                img_array[row, col + PAIR_STEP, channel] = new_p2

                # CRITICAL: incrementa di capacity (non len(bits_to_embed))
                # perché ljust() in _embed_in_pair aggiunge padding
                bit_index += capacity
```

**Ordine di scansione**:

1. Canale Rosso (0) → tutti i pixel
2. Canale Verde (1) → tutti i pixel
3. Canale Blu (2) → tutti i pixel

**Coppie di pixel**: `(col, col+PAIR_STEP)` - con PAIR_STEP=1 sono pixel adiacenti.

#### **Step 5: Verifica Capacità**

```python
if bit_index < len(full_payload):
    raise ValueError(
        ErrorMessages.IMAGE_TOO_SMALL_FILE.format(
            file_size=file_size, width=img.width, height=img.height
        )
    )
```

Se l'immagine è troppo piccola, solleva un errore.

#### **Step 6: Finalizzazione PVD**

```python
img_array = np.clip(img_array, 0, 255).astype(np.uint8)
result_img = Image.fromarray(img_array, mode="RGB")
```

- **Clipping**: forza tutti i pixel nel range 0-255
- Converte in `uint8` per compatibilità

#### **Step 7: Metriche e Backup**

```python
metrics = QualityMetrics.calculate_metrics(original_img, result_img)

params = {
    "method": "pvd",
    "size": file_size,
    "pair_step": BinarySteganography.PAIR_STEP,
    "channels": BinarySteganography.CHANNELS,
    "ranges_type": "quality" if is_quality else "capacity",
}
backup_system.save_backup_data(DataType.BINARY, params, backup_file)
```

Salva i parametri usati per il recupero futuro.

---

### 🧮 Funzione PVD `_embed_in_pair` - Logica di Embedding

Questa è la **funzione core** che nasconde i bit in una coppia di pixel.

```python
def _embed_in_pair(pixel1: int, pixel2: int, bits: str) -> tuple[int, int]:
    diff = pixel2 - pixel1  # Differenza originale
    lower, upper, capacity = BinarySteganography._get_range_capacity(diff)

    # Limita i bit alla capacità
    bits = bits[:capacity]
    if len(bits) == 0:
        return pixel1, pixel2

    # Converte bit → decimale (con padding a destra)
    decimal_value = int(bits.ljust(capacity, "0"), 2)

    # Calcola nuova differenza
    new_diff = lower + decimal_value
    new_diff = min(new_diff, upper)  # Clamp per auto-sincronizzazione

    # Mantiene il segno originale
    if diff < 0:
        new_diff = -new_diff

    # Calcola variazione necessaria
    m = abs(new_diff) - abs(diff)

    if m == 0:
        return pixel1, pixel2  # Nessuna modifica necessaria

    # Distribuisce la modifica tra i due pixel
    if diff % 2 == 0:  # Differenza pari
        new_pixel1 = pixel1 - m // 2
        new_pixel2 = pixel2 + m - m // 2
    else:  # Differenza dispari
        new_pixel1 = pixel1 - (m + 1) // 2
        new_pixel2 = pixel2 + m - (m + 1) // 2

    # Clipping 0-255
    new_pixel1 = max(0, min(255, new_pixel1))
    new_pixel2 = max(0, min(255, new_pixel2))

    return new_pixel1, new_pixel2
```

#### Esempio Pratico PVD

Supponiamo:

- `pixel1 = 100`, `pixel2 = 120` → `diff = 20`
- Range: `(16, 31, 3)` → capacità 3 bit, lower=16
- Bit da nascondere: `"101"` (5 in decimale)

**Calcoli**:

```text
decimal_value = int("101", 2) = 5
new_diff = 16 + 5 = 21
m = |21| - |20| = 1

# diff=20 è pari
new_pixel1 = 100 - 1//2 = 100 - 0 = 100
new_pixel2 = 120 + 1 - 0 = 121

Risultato: (100, 121)
```

**Verifica**: La nuova differenza è `121 - 100 = 21`, che codifica il valore 5 (`21 - 16 = 5 = "101"`).

---

### 🔓 Funzione PVD `_extract_from_pair` - Estrazione

```python
def _extract_from_pair(pixel1: int, pixel2: int) -> str:
    diff = pixel2 - pixel1
    lower, upper, capacity = BinarySteganography._get_range_capacity(diff)

    # Estrae il valore nascosto
    value = abs(diff) - lower

    # Clamp difensivo
    value = max(0, min(value, (1 << capacity) - 1))

    # Converte in binario
    bits = format(value, f"0{capacity}b")
    return bits
```

Continuando l'esempio precedente:

```text
diff = 121 - 100 = 21
lower = 16, capacity = 3
value = 21 - 16 = 5
bits = format(5, "03b") = "101"  ✓
```

---

## DWT: Discrete Wavelet Transform

### 📍 File: `src/steganografia/dwt/binary_operations.py`

### Principio di Funzionamento DWT

Il metodo **DWT (Discrete Wavelet Transform)** nasconde i dati nei **coefficienti wavelet** dell'immagine, in particolare nelle **bande di alta frequenza** (cH, cV, cD).

**Vantaggi**:

- **Robustezza**: resistente a compressione JPEG, ridimensionamento
- **Invisibilità**: le modifiche sono nelle alte frequenze (dettagli), meno percepibili
- **Flessibilità**: controllo preciso su qualità vs capacità

**Come funziona la DWT**:

1. L'immagine viene scomposta in 4 **subbande**:
   - **cA** (Approximation): componente a bassa frequenza (contenuto principale)
   - **cH** (Horizontal): dettagli orizzontali
   - **cV** (Vertical): dettagli verticali
   - **cD** (Diagonal): dettagli diagonali

2. I dati vengono nascosti **solo** nelle bande cH, cV, cD (alta frequenza)

---

### 🔧 Parametri di Configurazione (DWT)

```python
WAVELET: str = "haar"               # Tipo di wavelet (haar, db1, db2, etc.)
CHANNEL: int = 0                    # Canale principale (0=R, 1=G, 2=B)
BANDS: list[str] = ["cH"]           # Bande da usare: ["cH"], ["cH", "cV"], ["cH", "cV", "cD"]
ALPHA: float = 0.1                  # Fattore di embedding (controlla strength)
USE_ALL_CHANNELS: bool = False      # Se True usa RGB (3x capacità)
```

**Relazione ALPHA ↔ Strength**:

```python
strength = max(5.0, 1.0 / ALPHA)
```

| ----- | -------- | ---------- | ------- |
| 0.5 | 5.0 | Bassa | Alta |
| 0.1 | 10.0 | Media | Media |
| 0.05 | 20.0 | Alta | Bassa |

---

### 📦 Struttura del Payload (DWT)

```text
┌─────────────┬──────────────┬────────────────┬────────────────┐
│ Magic Header│  File Size   │   File Data    │   Terminator   │
│   64 bit    │   32 bit     │   variabile    │    16 bit      │
└─────────────┴──────────────┴────────────────┴────────────────┘
```

**Differenza con PVD**: Header di **64 bit** (invece di 16) per ridurre **falsi positivi** nell'estrazione.

```python
magic_header = "1100100100001111010110010100110011010101010011110000101011001101"  # 64 bit
```

### 🔍 Algoritmo DWT `hide_binary_file` - Step by Step

#### **Step 1-2: Preparazione (Identico a PVD)**

```python
with open(file_path, "rb") as f:
    file_data = f.read()

file_size = len(file_data)
file_binary = "".join(format(byte, "08b") for byte in file_data)

magic_header = "1100100100001111010110010100110011010101010011110000101011001101"
size_binary = format(file_size, "032b")
terminator = "1111000011110000"
full_payload = magic_header + size_binary + file_binary + terminator
```

#### **Step 3: Verifica Capacità**

```python
max_capacity = img.width * img.height * 3 // 4
if len(full_payload) > max_capacity:
    raise ValueError(...)
```

DWT ha capacità **inferiore** a PVD perché usa solo alcune subbande.

#### **Step 4: Conversione e Setup**

```python
img_array = np.array(img, dtype=np.float32)  # FLOAT32 per DWT

channels_to_use = [0, 1, 2] if USE_ALL_CHANNELS else [CHANNEL]
selected_bands = BANDS  # es. ["cH"]
```

**IMPORTANTE**: DWT lavora su float, non integer.

#### **Step 5: Embedding Loop - Trasformata Wavelet**

```python
bit_index = 0
for channel_idx in channels_to_use:
    if bit_index >= len(full_payload):
        break

    # Estrae canale
    channel_data = img_array[:, :, channel_idx]

    # Applica DWT
    coeffs = pywt.dwt2(channel_data, WAVELET)
    cA, (cH, cV, cD) = coeffs

    band_map = {"cH": cH, "cV": cV, "cD": cD}

    for band_name in selected_bands:
        if band_name not in band_map or bit_index >= len(full_payload):
            continue

        coeff_flat = band_map[band_name].flatten()

        # Embedding nei coefficienti
        for i in range(len(coeff_flat)):
            if bit_index >= len(full_payload):
                break

            bit = int(full_payload[bit_index])

            # === LOGICA DI EMBEDDING ===
            abs_val = abs(coeff_flat[i])
            if abs_val < 1.0:
                abs_val = 2.0  # Minimo valore base

            strength = max(5.0, 1.0 / ALPHA)

            if bit == 1:
                # bit=1 → GRANDE valore POSITIVO
                coeff_flat[i] = abs_val * strength
            else:
                # bit=0 → GRANDE valore NEGATIVO
                coeff_flat[i] = -abs_val * strength

            bit_index += 1

        # Aggiorna banda
        band_map[band_name] = coeff_flat.reshape(band_map[band_name].shape)

    # Ricostruzione con IDWT
    cH = band_map["cH"]
    cV = band_map["cV"]
    cD = band_map["cD"]
    reconstructed = pywt.idwt2((cA, (cH, cV, cD)), WAVELET)

    # Crop per dimensioni originali
    reconstructed = reconstructed[:channel_data.shape[0], :channel_data.shape[1]]
    img_array[:, :, channel_idx] = reconstructed
```

#### **Step 6: Finalizzazione DWT**

```python
img_array = np.clip(img_array, 0, 255).astype(np.uint8)
result_img = Image.fromarray(img_array, mode="RGB")
```

---

### 🧮 Logica di Embedding - Dettaglio

#### Strategia: Sign-Based Embedding

```python
abs_val = abs(coeff_flat[i])
if abs_val < 1.0:
    abs_val = 2.0

strength = max(5.0, 1.0 / ALPHA)

if bit == 1:
    coeff_flat[i] = abs_val * strength   # POSITIVO
else:
    coeff_flat[i] = -abs_val * strength  # NEGATIVO
```

**Perché funziona**:

- I coefficienti wavelet possono essere positivi o negativi
- **Modifichiamo il SEGNO** per codificare il bit
- Usiamo valori **grandi** (strength ≥ 5) per sopravvivere a:
  - Clipping (0-255)
  - Conversione uint8
  - Compressione JPEG

#### Esempio Pratico DWT

Dato un coefficiente `coeff = 3.5` e `ALPHA = 0.1`:

```text
strength = max(5.0, 1.0 / 0.1) = max(5.0, 10.0) = 10.0

Bit da nascondere: 1
→ coeff_new = 3.5 * 10.0 = 35.0  (POSITIVO)

Bit da nascondere: 0
→ coeff_new = -3.5 * 10.0 = -35.0  (NEGATIVO)
```

**Estrazione**:

```python
if coeff > 0:
    bit = "1"
else:
    bit = "0"
```

---

### 🔓 Estrazione DWT - Processo Bifase

L'estrazione DWT usa un **approccio in 2 fasi** per efficienza:

#### **Fase 1: Estrazione Header + Size (96 bit)**

```python
HEADER_BITS = 64
SIZE_BITS = 32
bits_needed = HEADER_BITS + SIZE_BITS

extracted_bits = []

# Estrae primi 96 bit
for ch_idx in channels_to_use:
    if len(extracted_bits) >= bits_needed:
        break

    coeffs = pywt.dwt2(channel_data, wavelet)
    cA, (cH, cV, cD) = coeffs
    band_map = {"cH": cH, "cV": cV, "cD": cD}

    for band_name in bands:
        coeff_flat = band_map[band_name].flatten()
        for coeff in coeff_flat:
            if len(extracted_bits) >= bits_needed:
                break
            # Estrazione basata su segno
            extracted_bits.append("1" if coeff > 0 else "0")
```

#### **DWT Fase 2: Calcolo Dimensione e Estrazione File**

```python
bitstream = "".join(extracted_bits)

# Verifica header
if bitstream[:HEADER_BITS] != magic_header:
    raise ValueError("Header non valido")

# Decodifica size
file_size_binary = bitstream[HEADER_BITS : HEADER_BITS + SIZE_BITS]
file_size = int(file_size_binary, 2)

# Calcola bit totali necessari
total_bits_needed = HEADER_BITS + SIZE_BITS + (file_size * 8) + TERMINATOR_BITS

# Continua estrazione se necessario
if len(extracted_bits) < total_bits_needed:
    # [estrae bit rimanenti...]
```

**Vantaggi dell'approccio bifase**:

- Non estrae l'intera immagine inutilmente
- Conosce esattamente quanti bit servono
- Più efficiente per file piccoli

---

## Confronto tra i Due Metodi

| Caratteristica        | PVD               | DWT                 |
| --------------------- | ----------------- | ------------------- |
| **Dominio**           | Spaziale (pixel)  | Frequenza (wavelet) |
| **Capacità**          | ⭐⭐⭐⭐⭐ Alta   | ⭐⭐⭐ Media        |
| **Robustezza**        | ⭐⭐ Bassa        | ⭐⭐⭐⭐⭐ Alta     |
| **Qualità Visiva**    | ⭐⭐⭐⭐ Buona    | ⭐⭐⭐⭐⭐ Ottima   |
| **Velocità**          | ⭐⭐⭐⭐⭐ Veloce | ⭐⭐⭐ Lenta        |
| **Resistenza JPEG**   | ❌ No             | ✅ Sì               |
| **Resistenza Resize** | ❌ No             | ✅ Sì (parziale)    |
| **Complessità**       | Bassa             | Alta                |
| **Header Size**       | 16 bit            | 64 bit              |
| **Tipo Dati**         | int32             | float32             |

---

### 📊 Capacità Teorica

Per un'immagine **1920x1080 RGB**:

#### **PVD (RANGES_QUALITY)**

```text
Coppie pixel: 1920 × 1080 / 2 = 1,036,800 coppie/canale
Capacità media: ~3 bit/coppia
Canali: 3

Capacità totale ≈ 1,036,800 × 3 × 3 = 9,331,200 bit ≈ 1.1 MB
```

#### **DWT (BANDS=["cH"], USE_ALL_CHANNELS=False)**

```text
Dimensione banda: (1920/2) × (1080/2) = 518,400 coefficienti
Canali: 1
Bit per coefficiente: 1

Capacità totale = 518,400 bit ≈ 63 KB
```

#### **DWT (BANDS=["cH", "cV", "cD"], USE_ALL_CHANNELS=True)**

```text
Bande: 3
Canali: 3

Capacità totale = 518,400 × 3 × 3 = 4,665,600 bit ≈ 570 KB
```

---

### 🎯 Quando Usare Quale Metodo

#### **Usa PVD quando**

- ✅ Hai bisogno di **massima capacità**
- ✅ L'immagine **non sarà compressa** (PNG, BMP)
- ✅ Vuoi **velocità di esecuzione**
- ✅ L'immagine ha **molte variazioni** (foto naturali)

#### **Usa DWT quando**

- ✅ Hai bisogno di **robustezza** (es. upload social media)
- ✅ L'immagine potrebbe subire **compressione JPEG**
- ✅ Vuoi **massima qualità visiva**
- ✅ Il file da nascondere è **relativamente piccolo**

---

## 🔬 Dettagli Implementativi Critici

### 1. **Padding in PVD**

```python
decimal_value = int(bits.ljust(capacity, "0"), 2)
```

Il `ljust()` aggiunge zeri a destra per raggiungere la capacità del range.

**Esempio**:

- Capacity: 4 bit
- Bit disponibili: `"10"` (2 bit)
- Dopo ljust: `"1000"` (4 bit)
- Valore decimale: 8

**CRITICAL**: Per questo motivo `bit_index` viene incrementato di `capacity`, **non** di `len(bits_to_embed)`.

---

### 2. **Clipping in PVD**

```python
new_diff = min(new_diff, upper)
```

Il clamping garantisce **auto-sincronizzazione**: anche se alcuni bit vengono persi, il recupero continua correttamente.

---

### 3. **Strength in DWT**

```python
strength = max(5.0, 1.0 / ALPHA)
```

Il minimo di 5.0 garantisce che i coefficienti sopravvivano al clipping uint8:

```text
Coefficiente originale: 3.5
Dopo embedding (strength=5): ±17.5
Dopo clip(0, 255): 17.5 o 0
Dopo uint8: 17 o 0

Il segno è preservato!
```

---

### 4. **Verifica Header in DWT**

```python
if bitstream[:HEADER_BITS] != magic_header:
    raise ValueError("Header non valido")
```

L'header **DEVE** essere all'inizio (no `find()`), altrimenti si rischia di estrarre dati casuali.

---

## 📈 Metriche di Qualità

Entrambi i metodi calcolano:

```python
metrics = QualityMetrics.calculate_metrics(original_img, result_img)
```

Le metriche tipiche includono:

- **PSNR** (Peak Signal-to-Noise Ratio): > 40 dB = ottimo
- **MSE** (Mean Squared Error): più basso = migliore
- **SSIM** (Structural Similarity Index): 0-1, più alto = migliore

---

## 🔐 Sistema di Backup

Entrambi i metodi salvano i parametri usati:

```python
backup_system.save_backup_data(DataType.BINARY, params, backup_file)
```

**PVD salva**:

```python
{
    "method": "pvd",
    "size": file_size,
    "pair_step": 1,
    "channels": [0, 1, 2],
    "ranges_type": "quality"  # o "capacity"
}
```

**DWT salva**:

```python
{
    "method": "dwt",
    "size": file_size,
    "wavelet": "haar",
    "channel": 0,
    "bands": ["cH"],
    "alpha": 0.1,
    "use_all_channels": False
}
```

Questo permette di **recuperare il file** anche senza conoscere i parametri originali.

---

## 🧪 Conclusioni

Entrambi i metodi sono **complementari**:

- **PVD**: eccellente per **alta capacità** in scenari controllati
- **DWT**: ideale per **robustezza** in scenari reali

La scelta dipende dal **caso d'uso specifico** e dai trade-off accettabili tra capacità, qualità e robustezza.
