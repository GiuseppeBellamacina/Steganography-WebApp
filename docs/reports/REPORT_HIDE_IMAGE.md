# Report Tecnico: Analisi delle Funzioni `hide_image`

## Indice

1. [PVD: Pixel Value Differencing per Immagini](#pvd-pixel-value-differencing-per-immagini)
2. [DWT: Discrete Wavelet Transform per Immagini](#dwt-discrete-wavelet-transform-per-immagini)
3. [Confronto tra i Due Metodi](#confronto-tra-i-due-metodi)

---

## PVD: Pixel Value Differencing per Immagini

### 📍 File: `src/steganografia/pvd/image_operations.py`

### Principio di Funzionamento PVD

Il metodo **PVD** per nascondere immagini sfrutta la **differenza adattiva tra coppie di pixel** per incorporare un'immagine segreta all'interno di un'immagine host. A differenza del nascondimento di file binari, questo metodo:

- **Riduce la profondità di bit** dell'immagine segreta da 8 a N bit per canale
- **È intrinsecamente LOSSY**: l'immagine recuperata sarà simile ma non identica all'originale
- **Bilancia qualità e capacità**: meno bit = migliore qualità visiva ma minore fedeltà dell'immagine segreta

---

### 🔧 Parametri di Configurazione

```python
# Ranges (identici al binary_operations)
RANGES_QUALITY = [
    (0, 7, 2),
    (8, 15, 3),
    (16, 31, 3),
    (32, 63, 4),
    (64, 127, 4),
]

RANGES_CAPACITY = [
    (0, 7, 3),
    (8, 15, 3),
    (16, 31, 4),
    (32, 63, 5),
    (64, 127, 6),
    (128, 255, 7),
]

# Configurazione
RANGES = RANGES_QUALITY
PAIR_STEP: int = 1
CHANNELS = [0, 1, 2]

# Parametro critico per image hiding
SECRET_BITS = 2  # Quanti bit dell'immagine segreta vengono preservati (2-4 MSB)
```

- `SECRET_BITS = 2`: preserva i 2 bit più significativi di ogni pixel → ottima qualità visiva host
- `SECRET_BITS = 3`: preserva 3 bit → qualità media, maggiore fedeltà immagine segreta
- `SECRET_BITS = 4`: preserva 4 bit → qualità ridotta, massima fedeltà immagine segreta

---

### 📦 Struttura del Payload

A differenza dei file binari, **NON** c'è un header/terminatore. Il payload è semplicemente:

```text
┌────────────────────────────────────────────────────┐
│        Pixel dell'immagine segreta (ridotti)       │
│          WIDTH × HEIGHT × 3 × SECRET_BITS          │
└────────────────────────────────────────────────────┘
```

---

### 🔍 Algoritmo PVD `hide_image` - Step by Step

#### **Step 1: Validazione e Preparazione**

```python
ParameterValidator.validate_image_size_for_image(host_img, secret_img, 1, 8)

host_img = host_img.convert("RGB")
secret_img = secret_img.convert("RGB")

original = host_img.copy()
host = np.array(host_img, dtype=np.int32)
secret = np.array(secret_img, dtype=np.uint8).flatten()

width, height = secret_img.size
```

- Verifica che l'immagine host sia abbastanza grande per contenere quella segreta
- Converte entrambe le immagini a RGB
- Appiattisce l'immagine segreta in un array 1D

#### **Step 2: Riduzione Profondità di Bit (CRITICAL)**

```python
SECRET_BITS = 2
shift = 8 - SECRET_BITS  # shift = 6
secret_bits = "".join(format(px >> shift, f"0{SECRET_BITS}b") for px in secret)
```

**Esempio pratico** con `SECRET_BITS = 2`:

```text
Pixel originale: 185 (10111001 in binario)
Shift right di 6: 185 >> 6 = 2 (00000010)
Formato 2 bit:    "10"

Pixel originale: 217 (11011001 in binario)
Shift right di 6: 217 >> 6 = 3 (00000011)
Formato 2 bit:    "11"
```

#### **Step 3: Embedding Loop**

```python
bit_idx = 0
h, w, _ = host.shape

for ch in ImageSteganography.CHANNELS:  # [0, 1, 2]
    for y in range(h):
        for x in range(0, w - PAIR_STEP, 2 * PAIR_STEP):
            if bit_idx >= len(secret_bits):
                break

            p1 = host[y, x, ch]
            p2 = host[y, x + PAIR_STEP, ch]

            # Determina capacità
            low, high, cap = ImageSteganography._range_for_difference(p2 - p1)
            chunk = secret_bits[bit_idx : bit_idx + cap]

            # Embedding
            p1n, p2n, used = ImageSteganography._embed_pair(p1, p2, chunk)
            host[y, x, ch] = p1n
            host[y, x + PAIR_STEP, ch] = p2n
            bit_idx += used
```

**Differenza con binary_operations**:

- Usa `_embed_pair()` che **restituisce il numero di bit effettivamente usati**
- Questo previene desincronizzazione quando il payload finisce a metà di una coppia

#### **Step 4: Conversione e Salvataggio Parametri**

```python
stego = Image.fromarray(host.astype(np.uint8), "RGB")

params = {
    "method": "pvd",
    "width": width,
    "height": height,
    "secret_bits": SECRET_BITS,  # FONDAMENTALE per recovery
    "pair_step": PAIR_STEP,
    "channels": CHANNELS,
    "ranges_type": "quality" if is_quality else "capacity",
}
backup_system.save_backup_data(DataType.IMAGE, params, backup_file)
```

---

### 🔓 Algoritmo PVD `get_image` - Estrazione

#### **Step 1: Caricamento Parametri**

```python
# Carica da backup o cache
if backup_file:
    backup_data = backup_system.load_backup_data(backup_file)
    data = backup_data["params"]
else:
    data = backup_system.get_last_params(DataType.IMAGE)

# Parametri manuali hanno priorità
width = width if width is not None else data["width"]
height = height if height is not None else data["height"]
SECRET_BITS = data.get("secret_bits", 2)
pair_step = data.get("pair_step", PAIR_STEP)
channels = data.get("channels", CHANNELS)
```

#### **Step 2: Estrazione Sincronizzata**

```python
total_bits = width * height * len(channels) * SECRET_BITS

arr = np.array(img, dtype=np.int32)
extracted = []
count = 0

for ch in channels:
    for y in range(h):
        for x in range(0, w - pair_step, 2 * pair_step):
            if count >= total_bits:
                break

            # Estrae bit
            bits = ImageSteganography._extract_pair(
                arr[y, x, ch],
                arr[y, x + pair_step, ch],
            )
            extracted.append(bits)
            count += len(bits)
```

**CRITICAL**: L'estrazione si ferma esattamente a `total_bits` per evitare di estrarre dati casuali.

#### **Step 3: Ricostruzione LOSSY**

```python
bitstream = "".join(extracted)[:total_bits]

# Espande da SECRET_BITS a 8 bit
pixels = []
shift = 8 - SECRET_BITS  # shift = 6 per SECRET_BITS=2
for i in range(0, len(bitstream), SECRET_BITS):
    chunk = bitstream[i : i + SECRET_BITS]
    pixels.append(int(chunk, 2) << shift)  # Shift left per espandere

secret = np.array(pixels[:width * height * 3], dtype=np.uint8)
secret = secret.reshape((height, width, 3))
result = Image.fromarray(secret, "RGB")
```

**Esempio di ricostruzione** con `SECRET_BITS = 2`:

```text
Bit estratti: "10"
Valore decimale: 2
Shift left di 6: 2 << 6 = 128 (10000000 in binario)

Pixel originale era: 185 (10111001)
Pixel recuperato:    128 (10000000)

Differenza: 185 - 128 = 57 (perdita di informazione)
```

**IMPORTANTE**: Questa è una **perdita prevista**. L'immagine recuperata sarà **visivamente simile** ma non identica bit per bit.

---

### 📊 Analisi della Perdita

Con `SECRET_BITS = 2`:

| Pixel Originale | Binario  | Bit Preservati | Pixel Recuperato | Binario  | Errore |
| --------------- | -------- | -------------- | ---------------- | -------- | ------ |
| 185             | 10111001 | 10             | 128              | 10000000 | 57     |
| 64              | 01000000 | 01             | 64               | 01000000 | 0      |
| 255             | 11111111 | 11             | 192              | 11000000 | 63     |
| 0               | 00000000 | 00             | 0                | 00000000 | 0      |

**Errore massimo per canale**: `2^(8-SECRET_BITS) - 1 = 63` (con SECRET_BITS=2)

**Qualità visiva**: PSNR tipicamente > 35 dB (accettabile per immagini naturali)

---

## DWT: Discrete Wavelet Transform per Immagini

### 📍 File: `src/steganografia/dwt/image_operations.py`

### Principio di Funzionamento DWT

Il metodo **DWT** per immagini usa la **Quantization Index Modulation (QIM)** nei coefficienti wavelet per nascondere un'immagine segreta. A differenza di PVD:

- **Più robusto**: resiste a compressione e modifiche
- **Determinismo perfetto**: usa un seed per shuffle riproducibile
- **QIM bin-centered**: quantizza i coefficienti al centro dei bin per massima robustezza

---

### 🔧 Parametri di Configurazione (DWT)

```python
WAVELET: str = "haar"                    # Tipo di wavelet
SEED: int = 42                           # Seed per deterministmo
STEP: float = 12.0                       # Step quantizzazione QIM (8-32)
CHANNEL: int = 0                         # Canale RGB per embedding (0=R)
BITS_SECRET: int = 3                     # Bit MSB dell'immagine segreta (2-4)
BANDS: list[str] = ["cH", "cV"]         # Bande DWT utilizzate
```

#### **Parametri Spiegati**

**STEP (Quantization Step)**:

- `STEP = 8`: bassa robustezza, alta qualità visiva
- `STEP = 12`: bilanciato (default)
- `STEP = 20`: alta robustezza, qualità ridotta
- `STEP = 32`: massima robustezza, distorsione evidente

**BITS_SECRET**:

- `2 bit`: immagine segreta molto degradata ma eccellente qualità host
- `3 bit`: bilanciato (default)
- `4 bit`: buona fedeltà immagine segreta, qualità host accettabile

**BANDS**:

- `["cH"]`: solo dettagli orizzontali → capacità minima
- `["cH", "cV"]`: orizzontali + verticali → capacità media (default)
- `["cH", "cV", "cD"]`: tutte le bande → capacità massima

---

### 📦 Struttura del Payload (DWT)

Come PVD, il payload è diretto senza header:

```text
┌────────────────────────────────────────────────────┐
│        Pixel dell'immagine segreta (ridotti)       │
│          WIDTH × HEIGHT × 3 × BITS_SECRET          │
└────────────────────────────────────────────────────┘
```

---

### 🔍 Algoritmo DWT `hide_image` - Step by Step

#### **Step 1: Riduzione Profondità di Bit**

```python
bits_secret = ImageSteganography.BITS_SECRET  # 3
secret_bits = []
for pixel_value in secret_array:
    shift = 8 - bits_secret  # shift = 5
    msb_value = int(pixel_value) >> shift
    secret_bits.append(format(msb_value, f"0{bits_secret}b"))
secret_binary = "".join(secret_bits)
```

Con `BITS_SECRET = 3`:

```text
Pixel 217: 11011001 → shift 5 → 00000110 (6) → "110"
Pixel 85:  01010101 → shift 5 → 00000010 (2) → "010"
```

#### **Step 2: DWT e Raccolta Coefficienti**

```python
channel_data = host_array[:, :, CHANNEL]  # Canale R
coeffs = pywt.dwt2(channel_data, WAVELET)
cA, (cH, cV, cD) = coeffs

band_map = {"cH": cH, "cV": cV, "cD": cD}
selected_bands = BANDS  # ["cH", "cV"]

all_coeffs = []
for band_name in selected_bands:
    if band_name in band_map:
        coeff_flat = band_map[band_name].flatten()
        # USA TUTTI i coefficienti (nessun filtro)
        for idx in range(len(coeff_flat)):
            all_coeffs.append((band_name, idx, coeff_flat[idx]))
```

**CRITICAL**: **TUTTI** i coefficienti vengono usati, senza filtri di soglia. Questo garantisce **sincronizzazione perfetta** tra hide e get.

#### **Step 3: Shuffle Deterministico**

```python
rng = np.random.default_rng(SEED)  # SEED=42
rng.shuffle(all_coeffs)
selected_coeffs = all_coeffs[:len(secret_binary)]
```

**Benefici del shuffle**:

1. **Distribuzione uniforme**: i bit sono sparsi su tutta l'immagine
2. **Determinismo**: stesso seed → stesso ordine → recupero perfetto
3. **Sicurezza**: randomizzazione rende più difficile l'analisi

#### **Step 4: Embedding QIM Bin-Centered**

```python
for bit_idx, (band_name, flat_idx, original_val) in enumerate(selected_coeffs):
    bit_value = int(secret_binary[bit_idx])
    coeff_value = band_arrays[band_name][flat_idx]

    sign = np.sign(coeff_value)
    if sign == 0:
        sign = 1
    abs_val = abs(coeff_value)

    # QIM: parità del quantized index codifica il bit
    quantized_index = int(abs_val // STEP)

    # Modifica parità se necessario
    if quantized_index % 2 != bit_value:
        quantized_index += 1 if bit_value == 1 else -1

    if quantized_index < 0:
        quantized_index = 0

    # Scrive al CENTRO del bin per robustezza numerica
    new_abs_val = (quantized_index + 0.5) * STEP
    band_arrays[band_name][flat_idx] = sign * new_abs_val
```

#### **QIM Spiegato con Esempio**

Dato:

- `STEP = 12.0`
- Coefficiente originale: `coeff = 35.7`
- Bit da nascondere: `1`

```python
abs_val = 35.7
quantized_index = int(35.7 // 12.0) = int(2.975) = 2

Parità di 2: pari (0)
Bit richiesto: 1 (dispari)

quantized_index += 1  → quantized_index = 3

new_abs_val = (3 + 0.5) * 12.0 = 3.5 * 12.0 = 42.0

Coefficiente modificato: 42.0
```

**Bin Centers**:

```text
Bin 0: [0, 12)   → centro 6.0
Bin 1: [12, 24)  → centro 18.0
Bin 2: [24, 36)  → centro 30.0
Bin 3: [36, 48)  → centro 42.0  ← Qui viene scritto
```

**Vantaggi bin-centered**:

- **Robustezza**: il valore è nel mezzo del bin, resiste a piccole perturbazioni
- **Margine di errore**: can tolerate ±STEP/2 di variazione senza perdere il bit

#### **Step 5: Ricostruzione IDWT**

```python
# Ricostruisce tutte le bande modificate
cH = band_arrays["cH"].reshape(cH.shape)
cV = band_arrays["cV"].reshape(cV.shape)
# cD rimane invariato se non in selected_bands

reconstructed = pywt.idwt2((cA, (cH, cV, cD)), WAVELET)
reconstructed = reconstructed[:channel_data.shape[0], :channel_data.shape[1]]
host_array[:, :, channel_idx] = reconstructed

host_array = np.clip(host_array, 0, 255).astype(np.uint8)
result_img = Image.fromarray(host_array, mode="RGB")
```

---

### 🔓 Algoritmo DWT `get_image` - Estrazione

#### **Step 1: Setup Identico**

```python
# CRITICAL: STESSI parametri dell'hide
step = ImageSteganography.STEP
channel_idx = ImageSteganography.CHANNEL
rng = np.random.default_rng(ImageSteganography.SEED)  # STESSO seed!

channel_data = img_array[:, :, channel_idx]
coeffs = pywt.dwt2(channel_data, WAVELET)
cA, (cH, cV, cD) = coeffs

# Raccoglie TUTTI i coefficienti (STESSA logica)
all_coeffs = []
for band_name in selected_bands:
    if band_name in band_map:
        coeff_flat = band_map[band_name].flatten()
        for idx in range(len(coeff_flat)):
            all_coeffs.append((band_name, idx, coeff_flat[idx]))

# STESSO shuffle
rng.shuffle(all_coeffs)
selected_coeffs = all_coeffs[:total_bits_needed]
```

**CRITICAL**: Ogni passaggio deve essere **identico** all'hide per garantire sincronizzazione.

#### **Step 2: Decodifica QIM**

```python
for band_name, flat_idx, coeff_value in selected_coeffs:
    if len(extracted_bits) >= total_bits_needed:
        break

    abs_val = abs(coeff_value)

    # Decodifica QIM dal centro del bin
    quantized_index = int(round(float(abs_val) / step - 0.5))

    # Legge parità
    bit_value = quantized_index % 2  # 0=pari, 1=dispari
    extracted_bits.append(str(bit_value))
```

**Esempio di decodifica**:

```text
Coefficiente letto: 42.0
quantized_index = int(round(42.0 / 12.0 - 0.5))
                = int(round(3.5 - 0.5))
                = int(round(3.0))
                = 3

Parità di 3: dispari → bit = 1  ✓
```

**Formula spiegata**:

- `abs_val / step`: posizione nel continuum dei bin (es. 3.5)
- `- 0.5`: compensa l'offset del bin center (3.5 - 0.5 = 3.0)
- `round()`: arrotonda all'indice del bin più vicino
- `% 2`: estrae la parità

#### **Step 3: Ricostruzione Immagine**

```python
secret_binary = "".join(extracted_bits[:total_bits_needed])
secret_pixels = []

for i in range(0, len(secret_binary), bits_secret):
    bits = secret_binary[i : i + bits_secret]
    if len(bits) == bits_secret:
        # Espande N MSB a 8 bit
        shift = 8 - bits_secret  # 5 per BITS_SECRET=3
        pixel_value = int(bits, 2) << shift
        secret_pixels.append(pixel_value)

secret_array = np.array(secret_pixels, dtype=np.uint8)
secret_array = secret_array.reshape((height, width, 3))
secret_img = Image.fromarray(secret_array, mode="RGB")
```

Con `BITS_SECRET = 3`:

```text
Bit estratti: "110"
Decimale: 6
Shift left 5: 6 << 5 = 192 (11000000)

Pixel originale era: 217 (11011001)
Pixel recuperato:    192 (11000000)
Errore: 25
```

---

## Confronto tra i Due Metodi

| Caratteristica       | PVD Image             | DWT Image                  |
| -------------------- | --------------------- | -------------------------- |
| **Dominio**          | Spaziale              | Frequenza                  |
| **Capacità Teorica** | ⭐⭐⭐⭐⭐ Molto alta | ⭐⭐⭐ Media               |
| **Robustezza**       | ⭐⭐ Bassa            | ⭐⭐⭐⭐⭐ Alta            |
| **Qualità Host**     | ⭐⭐⭐⭐ Buona        | ⭐⭐⭐⭐⭐ Ottima          |
| **Qualità Secret**   | ⭐⭐⭐ Lossy          | ⭐⭐⭐⭐ Lossy controllato |
| **Determinismo**     | ✅ Sequenziale        | ✅ Shuffle + seed          |
| **Resistenza JPEG**  | ❌ No                 | ✅ Sì (parziale)           |
| **Complessità**      | Bassa                 | Alta                       |
| **Bit Preservati**   | 2-4 MSB               | 2-4 MSB                    |

---

### 📊 Capacità Comparativa

Per un'immagine **host 1920x1080** che nasconde un'immagine **secret 640x480**:

#### **PVD (SECRET_BITS=2, RANGES_QUALITY)**

```text
Bit necessari: 640 × 480 × 3 × 2 = 1,843,200 bit
Coppie disponibili: 1920 × 1080 / 2 = 1,036,800 per canale
Capacità media: ~3 bit/coppia × 3 canali = ~9 bit/coppia totale

Stima capacità: 1,036,800 × 9 = 9,331,200 bit

Fattibilità: ✅ SÌ (1.8M < 9.3M)
```

#### **DWT (BITS_SECRET=3, BANDS=["cH","cV"], CHANNEL=0)**

```text
Bit necessari: 640 × 480 × 3 × 3 = 2,764,800 bit
Coefficienti disponibili: (1920/2) × (1080/2) × 2 bande = 1,036,800
Capacità: 1,036,800 bit

Fattibilità: ❌ NO (2.7M > 1.0M)

Soluzione: ridurre BITS_SECRET a 2 o aumentare dimensione host
```

---

### 🎯 Quando Usare Quale Metodo

#### **Usa PVD per Immagini quando**

- ✅ Hai un'immagine **segreta grande** da nascondere
- ✅ L'host **non sarà compresso** (PNG lossless)
- ✅ Accetti una **perdita moderata** di qualità nell'immagine segreta
- ✅ Priorità: **capacità massima**

#### **Usa DWT per Immagini quando**

- ✅ L'immagine potrebbe subire **compressione JPEG leggera**
- ✅ Vuoi **massima qualità visiva** dell'host
- ✅ L'immagine segreta è **relativamente piccola**
- ✅ Priorità: **robustezza e invisibilità**

---

## 🔬 Dettagli Implementativi Critici

### 1. **Perché SECRET_BITS invece di 8 bit completi?**

**Risposta**: Bilanciamento capacità/qualità:

```python
# Con 8 bit per pixel
payload_size = 640 × 480 × 3 × 8 = 7,372,800 bit  # 7.3 Mbit

# Con 2 bit per pixel
payload_size = 640 × 480 × 3 × 2 = 1,843,200 bit  # 1.8 Mbit (4x meno)
```

Usare meno bit:

- **Riduce payload** → serve meno spazio nell'host
- **Migliora qualità host** → meno modifiche
- **Trade-off**: l'immagine segreta perde dettagli (accettabile per la steganografia)

---

### 2. **PVD: Perché `_embed_pair` restituisce `used`?**

```python
p1n, p2n, used = ImageSteganography._embed_pair(p1, p2, chunk)
bit_idx += used  # NON += len(chunk)
```

**Motivo**: Previene desincronizzazione quando:

- La capacità è maggiore dei bit rimanenti del payload
- Esempio: capacità=4, bit rimanenti=2 → scrive solo 2, non 4

Senza `used`, il decoder si aspetterebbe 4 bit e leggerebbe dati random.

---

### 3. **DWT: Importanza del Bin-Centered QIM**

```python
new_abs_val = (quantized_index + 0.5) * STEP  # +0.5 è CRITICAL
```

**Senza bin-centering** (scrive al bordo):

```text
Bin 3: [36, 48)
Valore scritto: 36.0 (bordo sinistro)

Dopo JPEG compression: 36.0 → 35.5
Decodifica: int(35.5 / 12) = 2 (bin sbagliato!)  ❌
```

**Con bin-centering** (scrive al centro):

```text
Bin 3: [36, 48)
Valore scritto: 42.0 (centro)

Dopo JPEG compression: 42.0 → 40.0
Decodifica: int(round(40.0 / 12 - 0.5)) = int(round(2.83)) = 3  ✓
```

**Margine di errore**: ±6.0 (STEP/2) prima di cambiare bin.

---

### 4. **DWT: Perché Shuffle Deterministico?**

```python
rng = np.random.default_rng(SEED)  # SEED fisso
rng.shuffle(all_coeffs)
```

**Vantaggi**:

1. **Anti-pattern visibili**: senza shuffle, i bit si concentrerebbero in un'area specifica (top-left)
2. **Maggiore sicurezza**: distribuzione pseudo-casuale rende difficile reverse engineering
3. **Determinismo**: stesso seed → stesso ordine → recupero garantito

**Senza seed fisso**: ogni esecuzione produrrebbe un ordine diverso → recupero impossibile!

---

### 5. **Gestione del Segno nei Coefficienti**

```python
sign = np.sign(coeff_value)
if sign == 0:
    sign = 1  # Default per coefficienti nulli
```

I coefficienti wavelet possono essere:

- **Positivi**: rappresentano aumenti di intensità
- **Negativi**: rappresentano diminuzioni di intensità
- **Zero**: nessuna variazione

La QIM modifica la **magnitudine** ma preserva il **segno** per mantenere la coerenza dell'immagine.

---

## 📈 Metriche di Qualità

### **Per l'Immagine Host (Stego)**

```python
metrics = QualityMetrics.calculate_metrics(original_host, stego_host)
```

Tipici risultati:

- **PVD**: PSNR 38-42 dB (buono)
- **DWT**: PSNR 42-50 dB (eccellente)

### **Per l'Immagine Segreta Recuperata**

Non c'è metrica automatica, ma teoricamente:

| SECRET_BITS | PSNR Stimato | Qualità Percepita |
| ----------- | ------------ | ----------------- |
| 2           | ~18 dB       | Riconoscibile     |
| 3           | ~24 dB       | Buona             |
| 4           | ~30 dB       | Molto buona       |

---

## 🧪 Esempio Completo: Workflow PVD

### **Hiding PVD**

```python
host = Image.open("landscape_1920x1080.png")  # RGB
secret = Image.open("logo_320x240.png")       # RGB

ImageSteganography.SECRET_BITS = 2
ImageSteganography.RANGES = ImageSteganography.RANGES_QUALITY
ImageSteganography.PAIR_STEP = 1
ImageSteganography.CHANNELS = [0, 1, 2]

stego, *metrics = ImageSteganography.hide_image(host, secret, "params.json")
stego.save("stego.png", "PNG")  # Usa formato lossless!

# Payload: 320×240×3×2 = 460,800 bit
# Capacità: ~9M bit
# Percentuale: ~5%
```

### **Recovery PVD**

```python
stego = Image.open("stego.png")

recovered = ImageSteganography.get_image(
    stego,
    "recovered.png",
    backup_file="params.json"
)

# recovered è 320x240 RGB con 2 bit di profondità (degradato ma riconoscibile)
```

---

## 🧪 Esempio Completo: Workflow DWT

### **Hiding DWT**

```python
host = Image.open("photo_2560x1440.png")
secret = Image.open("watermark_256x256.png")

ImageSteganography.WAVELET = "haar"
ImageSteganography.SEED = 42
ImageSteganography.STEP = 12.0
ImageSteganography.BITS_SECRET = 3
ImageSteganography.BANDS = ["cH", "cV"]

stego, *metrics = ImageSteganography.hide_image(host, secret, "params_dwt.json")
stego.save("stego_dwt.png", "PNG")

# Payload: 256×256×3×3 = 589,824 bit
# Capacità: (2560/2)×(1440/2)×2 = 3,686,400 bit
# Percentuale: ~16%
```

### **Recovery DWT**

```python
stego = Image.open("stego_dwt.png")

recovered = ImageSteganography.get_image(
    stego,
    "recovered_dwt.png",
    backup_file="params_dwt.json"
)

# Anche dopo leggera compressione JPEG, il watermark è recuperabile!
```

---

## 📝 Conclusioni

### **PVD Image Hiding**

- **Pro**: Alta capacità, implementazione semplice, veloce
- **Contro**: Lossy, non robusto a compressione, qualità secret limitata
- **Caso d'uso**: Nascondere loghi/watermark in immagini che rimarranno PNG

### **DWT Image Hiding**

- **Pro**: Robusto, alta qualità host, controllo preciso tramite parametri
- **Contro**: Capacità limitata, complesso, richiede parametri corretti
- **Caso d'uso**: Watermarking robusto, copyright protection, immagini che subiranno post-processing
