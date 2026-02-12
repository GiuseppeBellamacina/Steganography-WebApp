# Report Tecnico: Analisi delle Funzioni `hide_message` (Text)

## Indice

1. [PVD: Pixel Value Differencing per Messaggi](#pvd-pixel-value-differencing-per-messaggi)
2. [DWT: Discrete Wavelet Transform per Messaggi](#dwt-discrete-wavelet-transform-per-messaggi)
3. [Confronto tra i Due Metodi](#confronto-tra-i-due-metodi)

---

## PVD: Pixel Value Differencing per Messaggi

### 📍 File: `src/steganografia/pvd/message_operations.py`

### Principio di Funzionamento PVD

Il metodo **PVD** per messaggi di testo nasconde **stringhe** utilizzando la tecnica di **differenza adattiva tra coppie di pixel**. A differenza del nascondimento di file binari:

- Usa un **header completo** con magic number, lunghezza e checksum
- Include **verifica di integrità** tramite XOR checksum
- **Non comprime** il messaggio (ogni carattere = 8 bit ASCII/UTF-8)
- È **lossless** per il messaggio (recupero preciso bit-per-bit)

---

### 🔧 Parametri di Configurazione

```python
# Ranges (identici a binary e image operations)
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
```

---

### 📦 Struttura del Payload (PVD)

Il payload completo per messaggi è:

```text
┌─────────────┬──────────────┬──────────────┬─────────────┬────────────────┐
│ Magic Header│ Msg Length   │   Checksum   │  Message    │   Terminator   │
│   16 bit    │   32 bit     │   16 bit     │  variable   │    16 bit      │
└─────────────┴──────────────┴──────────────┴─────────────┴────────────────┘
```

**Componenti**:

1. **Magic Header**: `1010101011110000` (16 bit) - Identifica presenza messaggio
2. **Message Length**: lunghezza in caratteri (32 bit, max 4 miliardi caratteri)
3. **Checksum**: XOR di tutti i caratteri (16 bit) - verifica integrità
4. **Message Data**: contenuto del testo convertito in binario (8 bit/char)
5. **Terminator**: `1111000011110000` (16 bit) - marca fine messaggio

---

### 🔍 Algoritmo PVD `hide_message` - Step by Step

#### **Step 1: Validazione**

```python
ParameterValidator.validate_image_size_for_message(img, message)
```

Verifica che l'immagine sia abbastanza grande per contenere il messaggio. Calcola:

```text
bit_necessari = 16 (header) + 32 (length) + 16 (checksum) + len(message)*8 + 16 (term)
              = 80 + len(message) * 8
```

#### **Step 2: Preparazione del Payload**

```python
# Converte messaggio in binario
msg_binary = binary_convert(message)  # "Hello" → "0100100001100101011011000110110001101111"

# Costruisce header
magic_header = "1010101011110000"
msg_length = format(len(message), "032b")  # len=5 → "00000000000000000000000000000101"

# Calcola checksum XOR
checksum = 0
for char in message:
    checksum ^= ord(char)  # XOR cumulativo
checksum_binary = format(checksum, "016b")

terminator = "1111000011110000"

full_payload = magic_header + msg_length + checksum_binary + msg_binary + terminator
```

**Esempio con "Hi"**:

```text
Messaggio: "Hi"
Binario: "0100100001101001" (H=72, i=105)

Magic:    1010101011110000 (16 bit)
Length:   00000000000000000000000000000010 (32 bit, valore 2)
Checksum: 72 XOR 105 = 33 (00100001) → 0000000000100001 (16 bit)
Message:  0100100001101001 (16 bit)
Term:     1111000011110000 (16 bit)

Total:    96 bit di overhead + 16 bit dati = 112 bit
```

#### **Step 3: Embedding Loop**

```python
bit_index = 0
height, width, _ = img_array.shape

for channel in MessageSteganography.CHANNELS:  # [0, 1, 2]
    for row in range(height):
        for col in range(0, width - PAIR_STEP, 2 * PAIR_STEP):
            if bit_index >= len(full_payload):
                break

            pixel1 = int(img_array[row, col, channel])
            pixel2 = int(img_array[row, col + PAIR_STEP, channel])

            # Determina capacità
            _, _, capacity = MessageSteganography._get_range_capacity(pixel2 - pixel1)
            bits_to_embed = full_payload[bit_index : bit_index + capacity]

            if bits_to_embed:
                new_p1, new_p2 = MessageSteganography._embed_in_pair(
                    pixel1, pixel2, bits_to_embed
                )
                img_array[row, col, channel] = new_p1
                img_array[row, col + PAIR_STEP, channel] = new_p2

                # FIX CRITICAL: incrementa di len(bits_to_embed) non capacity
                bit_index += len(bits_to_embed)
```

**Differenza chiave con binary_operations**:

```python
bit_index += len(bits_to_embed)  # message_operations
# vs
bit_index += capacity             # binary_operations
```

**Perché?**

- In `binary_operations`, `_embed_in_pair` usa `ljust()` che aggiunge sempre padding → scrive sempre `capacity` bit
- In `message_operations`, quando il payload finisce a metà coppia, scrive solo i bit rimanenti
- Usare `capacity` causerebbe desincronizzazione durante l'estrazione

#### **Step 4: Verifica Completamento**

```python
if bit_index < len(full_payload):
    raise ValueError(
        f"Immagine troppo piccola per nascondere il messaggio. "
        f"Nascosti {bit_index}/{len(full_payload)} bit"
    )
```

#### **Step 5: Salvataggio Parametri**

```python
params = {
    "method": "pvd",
    "msg_length": len(message),
    "pair_step": MessageSteganography.PAIR_STEP,
    "channels": MessageSteganography.CHANNELS,
    "ranges_type": "quality" if is_quality else "capacity",
}
backup_system.save_backup_data(DataType.STRING, params, backup_file)
```

---

### 🔓 Algoritmo PVD `get_message` - Estrazione

#### **Step 1: Caricamento Parametri**

```python
pair_step = MessageSteganography.PAIR_STEP
channels = MessageSteganography.CHANNELS

if backup_file:
    backup_data = backup_system.load_backup_data(backup_file)
    if backup_data and "params" in backup_data:
        pair_step = backup_data["params"].get("pair_step", pair_step)
        channels = backup_data["params"].get("channels", channels)
        # CRITICAL: carica RANGES
        ranges_type = backup_data["params"].get("ranges_type", "quality")
        MessageSteganography.RANGES = (
            MessageSteganography.RANGES_QUALITY if ranges_type == "quality"
            else MessageSteganography.RANGES_CAPACITY
        )
```

**CRITICAL**: I parametri devono corrispondere esattamente a quelli dell'hide, specialmente `RANGES`.

#### **Step 2: Estrazione Bit**

```python
extracted_bits = []
height, width, _ = img_array.shape

for channel in channels:
    for row in range(height):
        for col in range(0, width - pair_step, 2 * pair_step):
            pixel1 = int(img_array[row, col, channel])
            pixel2 = int(img_array[row, col + pair_step, channel])

            bits = MessageSteganography._extract_from_pair(pixel1, pixel2)
            extracted_bits.append(bits)

full_binary = "".join(extracted_bits)
```

**IMPORTANTE**: Estrae **TUTTI** i bit possibili, non si ferma a una lunghezza prestabilita (a differenza del binary).

#### **Step 3: Ricerca Header**

```python
magic_header = "1010101011110000"
header_pos = full_binary.find(magic_header)

if header_pos == -1:
    raise ValueError(
        "Nessun messaggio trovato nell'immagine (header magic mancante)"
    )
```

Usa `find()` perché il messaggio potrebbe **non** iniziare al primo bit (a differenza del DWT che richiede header all'inizio).

#### **Step 4: Decodifica Header**

```python
# Legge lunghezza
length_start = header_pos + 16
length_end = length_start + 32
msg_length_binary = full_binary[length_start:length_end]
msg_length = int(msg_length_binary, 2)

# Legge checksum
checksum_start = length_end
checksum_end = checksum_start + 16
expected_checksum = int(full_binary[checksum_start:checksum_end], 2)

# Legge messaggio
msg_start = checksum_end
msg_end = msg_start + (msg_length * 8)
msg_binary = full_binary[msg_start:msg_end]
```

#### **Step 5: Decodifica e Verifica**

```python
# Converte binario → stringa
message = binary_convert_back(msg_binary)

# Verifica checksum
actual_checksum = 0
for char in message:
    actual_checksum ^= ord(char)

if actual_checksum != expected_checksum:
    print("Warning: Checksum non corrisponde. Messaggio potrebbe essere corrotto.")

return message
```

**XOR Checksum spiegato**:

```text
Messaggio: "Hi"
H = 72 (01001000)
i = 105 (01101001)

Checksum = 72 XOR 105
         = 01001000
         XOR 01101001
         = 00100001 (33)

Durante verifica:
Checksum da header: 33
Checksum calcolato: 72 XOR 105 = 33  ✓
```

---

## DWT: Discrete Wavelet Transform per Messaggi

### 📍 File: `src/steganografia/dwt/message_operations.py`

### Principio di Funzionamento DWT

Il metodo **DWT** per messaggi nasconde testo usando la **modifica del segno dei coefficienti wavelet** in bande ad alta frequenza. Caratteristiche:

- **Header robusto a 64 bit** (invece di 16) per ridurre falsi positivi
- **Checksum a 32 bit** (invece di 16) per migliore rilevamento errori
- **Sign-based embedding**: bit=1 → positivo, bit=0 → negativo
- **Estrazione bifase**: prima header/size, poi payload

---

### 🔧 Parametri di Configurazione (DWT)

```python
WAVELET: str = "haar"               # Tipo di wavelet
ALPHA: float = 0.1                  # Fattore di embedding (strength = 50/ALPHA)
BANDS: list[str] = ["cH"]          # Bande DWT utilizzate
CHANNEL: int = 0                    # Canale principale (0=R)
USE_ALL_CHANNELS: bool = True       # Se True usa RGB (3x capacità)
```

**ALPHA e Strength**:

```python
delta = ALPHA * 50.0  # Forza della modifica
```

| ALPHA | Delta | Robustezza | Qualità Host |
| ----- | ----- | ---------- | ------------ |
| 0.2   | 10.0  | Bassa      | Ottima       |
| 0.1   | 5.0   | Media      | Buona        |
| 0.05  | 2.5   | Alta       | Accettabile  |

**USE_ALL_CHANNELS**:

- `False`: usa solo `CHANNEL` (es. R) → capacità 1x
- `True`: usa R, G, B → capacità 3x (consigliato per messaggi lunghi)

---

### 📦 Struttura del Payload (DWT)

```text
┌─────────────┬──────────────┬──────────────┬─────────────┬────────────────┐
│ Magic Header│ Msg Length   │   Checksum   │  Message    │   Terminator   │
│   64 bit    │   32 bit     │   32 bit     │  variable   │    16 bit      │
└─────────────┴──────────────┴──────────────┴─────────────┴────────────────┘
```

**Differenze con PVD**:

- Header: **64 bit** invece di 16 (codice più complesso, meno falsi positivi)
- Checksum: **32 bit** invece di 16 (migliore rilevamento errori)

```python
magic_header = "1100100100001111010110010100110011010101010011110000101011001101"  # 64 bit
checksum_binary = format(checksum, "032b")  # 32 bit
```

### 🔍 Algoritmo DWT `hide_message` - Step by Step

#### **Step 1: Preparazione Payload**

```python
msg_binary = binary_convert(message)

magic_header = "1100100100001111010110010100110011010101010011110000101011001101"  # 64 bit
msg_length = format(len(message), "032b")

# Checksum XOR a 32 bit
checksum = 0
for char in message:
    checksum ^= ord(char)
checksum_binary = format(checksum, "032b")

terminator = "1111000011110000"

full_payload = magic_header + msg_length + checksum_binary + msg_binary + terminator
```

**Overhead totale**: 64 + 32 + 32 + 16 = **144 bit** (vs 80 bit PVD)

#### **Step 2: Verifica Capacità**

```python
max_capacity = img.width * img.height * 3 // 4  # Approssimazione conservativa
if len(full_payload) > max_capacity:
    raise ValueError(f"Messaggio troppo lungo per questa immagine. ...")
```

- Usa solo alcune bande (cH, cV, cD)
- Applica soglie sui coefficienti utilizzabili

#### **Step 3: DWT e Selezione Coefficienti**

```python
channels_to_use = [0, 1, 2] if USE_ALL_CHANNELS else [CHANNEL]

bit_index = 0
for channel in channels_to_use:
    channel_data = img_array[:, :, channel]

    # Applica DWT
    coeffs = pywt.dwt2(channel_data, WAVELET)
    cA, (cH, cV, cD) = coeffs

    band_map = {"cH": cH, "cV": cV, "cD": cD}
    selected_bands = BANDS  # ["cH"]

    for band_name in selected_bands:
        band_coeffs = band_map[band_name]
        band_flat = band_coeffs.flatten()

        # Usa solo coefficienti significativi (soglia)
        threshold = 1.0
        usable_indices = [i for i, c in enumerate(band_flat) if abs(c) > threshold]
```

**CRITICAL**: Solo i coefficienti con `|coeff| > threshold` vengono usati. Questo:

- **Evita coefficienti rumorosi**: valori piccoli sono instabili
- **Migliora robustezza**: grandi coefficienti resistono meglio a modifiche
- **Riduce capacità**: meno coefficienti disponibili

#### **Step 4: Sign-Based Embedding**

```python
for i in usable_indices:
    if bit_index >= len(full_payload):
        break

    bit = int(full_payload[bit_index])

    # Delta scalato da ALPHA
    delta = MessageSteganography.ALPHA * 50.0

    if bit == 1:
        # Assicura che sia POSITIVO
        band_flat[i] = abs(band_flat[i]) + delta
    else:
        # Assicura che sia NEGATIVO
        band_flat[i] = -abs(band_flat[i]) - delta

    bit_index += 1
```

**Esempio pratico**:

```text
Coefficiente originale: 5.3
Bit da nascondere: 1 (positivo)
Delta = 0.1 * 50.0 = 5.0

Nuovo coefficiente = |5.3| + 5.0 = 5.3 + 5.0 = 10.3  (positivo)


Coefficiente originale: -8.2
Bit da nascondere: 0 (negativo)
Delta = 5.0

Nuovo coefficiente = -|(-8.2)| - 5.0 = -8.2 - 5.0 = -13.2  (negativo)
```

**Perché aggiungere delta a abs()?**

- Aumenta la **magnitudine** del coefficiente
- **Rinforza il segnale** per sopravvivere a clipping/compressione
- Mantiene il **segno** intatto per codificare il bit

#### **Step 5: Ricostruzione IDWT**

```python
# Aggiorna banda modificata
band_map[band_name] = band_flat.reshape(band_coeffs.shape)

# Ricostruisce canale
cH = band_map["cH"]
cV = band_map["cV"]
cD = band_map["cD"]
reconstructed = pywt.idwt2((cA, (cH, cV, cD)), WAVELET)
reconstructed = reconstructed[:channel_data.shape[0], :channel_data.shape[1]]
img_array[:, :, channel] = reconstructed

# Clipping finale
img_array = np.clip(img_array, 0, 255).astype(np.uint8)
result_img = Image.fromarray(img_array, mode="RGB")
```

---

### 🔓 Algoritmo `get_message` - Estrazione Bifase

#### **FASE 1: Estrazione Header (128 bit)**

```python
HEADER_BITS = 64
LENGTH_BITS = 32
CHECKSUM_BITS = 32

bits_needed = HEADER_BITS + LENGTH_BITS + CHECKSUM_BITS  # 128
extracted_bits = []
threshold = 1.0

for channel in channels_to_use:
    if len(extracted_bits) >= bits_needed:
        break

    channel_data = img_array[:, :, channel]
    coeffs = pywt.dwt2(channel_data, WAVELET)
    cA, (cH, cV, cD) = coeffs

    band_map = {"cH": cH, "cV": cV, "cD": cD}
    selected_bands = BANDS

    for band_name in selected_bands:
        band_flat = band_map[band_name].flatten()

        # STESSA soglia dell'hide
        usable_indices = [i for i, c in enumerate(band_flat) if abs(c) > threshold]

        for i in usable_indices:
            if len(extracted_bits) >= bits_needed:
                break

            # Estrazione basata su segno
            if band_flat[i] > 0:
                extracted_bits.append("1")
            else:
                extracted_bits.append("0")
```

**Perché FASE 1?**

- Evita di estrarre l'intera immagine inutilmente
- Conosce la lunghezza del messaggio prima di continuare
- Ottimizzazione: per messaggi brevi, estrae solo pochi coefficienti

#### **Verifica Header**

```python
bitstream = "".join(extracted_bits)

# Header DEVE essere all'inizio (no find!)
if bitstream[:HEADER_BITS] != magic_header:
    raise ValueError(
        "Header non valido: nessun messaggio DWT trovato. "
        "Possibili cause: (1) Metodo sbagliato, (2) Immagine corrotta, "
        "(3) Parametri errati (WAVELET/BANDS/CHANNELS/USE_ALL_CHANNELS diversi)"
    )
```

**Differenza critica con PVD**: DWT **NON** usa `find()`, richiede header **esattamente** all'inizio. Questo:

- Riduce falsi positivi (pattern casuali sembrano header)
- Richiede sincronizzazione perfetta hide/get
- Se header non corrisponde → parametri sbagliati o immagine corrotta

#### **Decodifica Lunghezza**

```python
msg_length_binary = bitstream[HEADER_BITS : HEADER_BITS + LENGTH_BITS]
msg_length = int(msg_length_binary, 2)

checksum_start = HEADER_BITS + LENGTH_BITS
expected_checksum = int(bitstream[checksum_start : checksum_start + CHECKSUM_BITS], 2)
```

#### **FASE 2: Estrazione Payload Rimanente**

```python
total_bits_needed = HEADER_BITS + LENGTH_BITS + CHECKSUM_BITS + (msg_length * 8) + TERMINATOR_BITS

if len(extracted_bits) < total_bits_needed:
    bits_read = len(extracted_bits)
    current_bit_index = 0

    # Riprende estrazione dove si era fermata
    for channel in channels_to_use:
        for band_name in selected_bands:
            usable_indices = [...]

            for i in usable_indices:
                # Salta bit già estratti nella FASE 1
                if current_bit_index < bits_read:
                    current_bit_index += 1
                    continue

                if len(extracted_bits) >= total_bits_needed:
                    break

                if band_flat[i] > 0:
                    extracted_bits.append("1")
                else:
                    extracted_bits.append("0")
                current_bit_index += 1
```

**CRITICAL**: Traccia `current_bit_index` per **saltare** i bit già estratti nella FASE 1, evitando duplicazioni.

#### **Decodifica e Verifica**

```python
bitstream = "".join(extracted_bits)

msg_start = HEADER_BITS + LENGTH_BITS + CHECKSUM_BITS
msg_end = msg_start + (msg_length * 8)
msg_binary = bitstream[msg_start:msg_end]

# Decodifica
message = binary_convert_back(msg_binary)

# Verifica checksum a 32 bit
actual_checksum = 0
for char in message:
    actual_checksum ^= ord(char)

if actual_checksum != expected_checksum:
    print("Warning: Checksum non corrisponde. Messaggio potrebbe essere corrotto.")
```

---

## Confronto tra i Due Metodi

| Caratteristica      | PVD Message           | DWT Message            |
| ------------------- | --------------------- | ---------------------- |
| **Dominio**         | Spaziale              | Frequenza              |
| **Capacità**        | ⭐⭐⭐⭐⭐ Molto alta | ⭐⭐⭐ Media           |
| **Robustezza**      | ⭐⭐ Bassa            | ⭐⭐⭐⭐⭐ Alta        |
| **Qualità Host**    | ⭐⭐⭐⭐ Buona        | ⭐⭐⭐⭐⭐ Ottima      |
| **Overhead**        | 80 bit                | 144 bit                |
| **Header Size**     | 16 bit                | 64 bit                 |
| **Checksum**        | 16 bit (XOR)          | 32 bit (XOR)           |
| **Ricerca Header**  | `find()` (flessibile) | Inizio esatto (rigido) |
| **Resistenza JPEG** | ❌ No                 | ✅ Parziale            |
| **Complessità**     | Bassa                 | Alta                   |
| **Estrazione**      | Monofase              | Bifase                 |

---

### 📊 Capacità Teorica

Per un'immagine **800x600 RGB**:

#### **PVD (RANGES_QUALITY, PAIR_STEP=1, CHANNELS=[0,1,2])**

```text
Coppie pixel: 800 × 600 / 2 = 240,000 coppie/canale
Capacità media: ~3 bit/coppia
Canali: 3

Capacità totale ≈ 240,000 × 3 × 3 = 2,160,000 bit
                ≈ 270,000 byte
                ≈ 270 KB di testo

Overhead: 80 bit
Messaggio max: ~270 KB - 10 byte ≈ 270 KB  ✓ (trascurabile)
```

**Esempio pratico**:

- Libro completo (~500 KB) → **NON** entra
- Articolo lungo (~50 KB, ~50,000 caratteri) → **SÌ** ✓
- Email (~2 KB, ~2,000 caratteri) → **SÌ** ✓✓

#### **DWT (BANDS=["cH"], USE_ALL_CHANNELS=True, ALPHA=0.1)**

```text
Dimensione banda cH: (800/2) × (600/2) = 120,000 coefficienti
Coefficienti utilizzabili (|c| > 1.0): ~60% = 72,000
Canali: 3 (USE_ALL_CHANNELS=True)

Capacità totale: 72,000 × 3 = 216,000 bit
                ≈ 27,000 byte
                ≈ 27 KB

Overhead: 144 bit
Messaggio max: ~27 KB - 18 byte ≈ 27 KB  ✓
```

**Esempio pratico**:

- Articolo lungo (~50 KB) → **NON** entra
- Email (~2 KB) → **SÌ** ✓
- Tweet (280 caratteri = ~280 byte) → **SÌ** ✓✓

---

### 🎯 Quando Usare Quale Metodo

#### **Usa PVD per Messaggi quando**

- ✅ Il messaggio è **relativamente lungo** (>10 KB)
- ✅ L'immagine **non sarà compressa** (PNG, BMP)
- ✅ Priorità: **capacità massima**
- ✅ **Velocità** di esecuzione importante

#### **Usa DWT per Messaggi quando**

- ✅ Il messaggio è **breve/medio** (<20 KB)
- ✅ L'immagine potrebbe subire **compressione JPEG leggera**
- ✅ Priorità: **robustezza e invisibilità**
- ✅ **Sicurezza**: header complesso riduce rilevamento

---

## 🔬 Dettagli Implementativi Critici

### 1. **XOR Checksum: Perché e Come funziona**

```python
checksum = 0
for char in message:
    checksum ^= ord(char)
```

**Esempio**:

```text
Messaggio: "Cat"
C = 67  (01000011)
a = 97  (01100001)
t = 116 (01110100)

Checksum = 67 XOR 97 XOR 116
         = (67 XOR 97) XOR 116
         = 34 XOR 116
         = 00100010 XOR 01110100
         = 01010110 (86)
```

**Vantaggi**:

- **Veloce**: operazione O(n)
- **Simmetrico**: stesso algoritmo encode/decode
- **Rileva errori**: singolo bit errato cambia checksum

**Limitazioni**:

- Non rileva **scambi di caratteri** (es. "Cat" vs "aCt" → stesso checksum)
- Non rileva **doppie modifiche** compensative

Per questo è considerato un **controllo base**, non crittograficamente sicuro.

---

### 2. **PVD: find() vs Inizio Esatto**

**PVD usa find()**:

```python
header_pos = full_binary.find(magic_header)
if header_pos == -1:
    raise ValueError(...)
```

**Vantaggi**:

- **Tollerante**: il messaggio può iniziare ovunque nel bitstream
- **Flessibile**: utile se l'immagine ha pixel random all'inizio

**Svantaggi**:

- **Falsi positivi**: pattern casuali potrebbero sembrare header (bassa probabilità con 16 bit: 1/65,536)

**DWT richiede inizio esatto**:

```python
if bitstream[:HEADER_BITS] != magic_header:
    raise ValueError(...)
```

**Vantaggi**:

- **Sicurezza**: header lungo 64 bit → probabilità falso positivo 1/18,446,744,073,709,551,616 (trascurabile)
- **Validazione**: se non corrisponde → parametri sicuramente sbagliati

**Svantaggi**:

- **Rigidità**: richiede sincronizzazione perfetta hide/get

---

### 3. **DWT: Importanza della Threshold**

```python
threshold = 1.0
usable_indices = [i for i, c in enumerate(band_flat) if abs(c) > threshold]
```

**Perché è necessaria?**

Coefficienti piccoli (|c| < 1.0):

- Sono **rumorosamente instabili** after IDWT
- Possono **cambiare segno** durante clip/uint8 conversion
- **Riducono affidabilità** del recupero

**Esempio problematico senza threshold**:

```text
Coefficiente originale: 0.3
Bit nascosto: 1 (positivo)
Delta = 5.0

Nuovo coefficiente = |0.3| + 5.0 = 5.3

Dopo IDWT e clip(0,255):
Pixel risultante potrebbe introdurre artefatti che, in una successiva DWT,
producono coefficiente = -0.8  (cambio segno imprevisto!)

Estrazione: -0.8 < 0 → bit = 0  ❌ (doveva essere 1)
```

**Con threshold**:

```text
Coefficiente originale: 5.2 (> 1.0, OK)
Bit nascosto: 1
Nuovo: 10.2

Dopo modifiche: rimane 9.5 (comunque > 0)
Estrazione: bit = 1  ✓
```

---

### 4. **Gestione Overflow in Incremento bit_index**

**PVD message_operations**:

```python
bit_index += len(bits_to_embed)  # Incremento variabile
```

**PVD binary_operations**:

```python
bit_index += capacity  # Incremento fisso
```

**Perché la differenza?**

In `message_operations`, quando il payload finisce:

```python
full_payload = "10110101101" (11 bit totali)
bit_index = 9
capacity = 4

bits_to_embed = full_payload[9:9+4] = "101" (solo 2 bit rimanenti)

_embed_in_pair(..., "101") NON aggiunge padding
→ scrive solo 2 bit

bit_index += len("101") = bit_index + 2  ✓ (corretto)

Se usasse bit_index += capacity:
bit_index += 4 → bit_index = 13 > 11  ❌ (sorpassa il payload)
```

In `binary_operations`, `ljust()` garantisce sempre `capacity` bit:

```python
bits = "101".ljust(4, "0") = "1010"  (4 bit)
→ scrive sempre 4 bit
→ bit_index += 4  ✓ (corretto)
```

---

### 5. **DWT: Estrazione Bifase - Ottimizzazione**

**Senza bifase** (estrazione naive):

```python
# Estrae TUTTO il bitstream
for tutti_i_coefficienti:
    extracted_bits.append(...)

# Poi cerca header e legge messaggio
```

**Problema**: Per un'immagine 1920x1080, estrae >500,000 bit anche per un messaggio di 10 caratteri (80 bit)!

**Con bifase**:

```text
FASE 1: Estrae 128 bit → legge msg_length (es. 10 caratteri)
FASE 2: Estrae solo i rimanenti 80 + 16 = 96 bit necessari

Totale estratto: 128 + 96 = 224 bit invece di 500,000+  ✓
```

**Velocità**: ~2000x più veloce per messaggi brevi!

---

## 📈 Metriche di Qualità

### **Qualità Immagine Host**

Tipici risultati:

| Metodo           | PSNR Tipico | SSIM Tipico | Qualità Percepita |
| ---------------- | ----------- | ----------- | ----------------- |
| PVD (QUALITY)    | 38-42 dB    | 0.98-0.99   | Eccellente        |
| PVD (CAPACITY)   | 34-38 dB    | 0.95-0.98   | Buona             |
| DWT (ALPHA=0.1)  | 42-48 dB    | 0.99+       | Impercettibile    |
| DWT (ALPHA=0.05) | 45-52 dB    | 0.99+       | Perfetto          |

### **Capacità vs Lunghezza Messaggio**

| Lunghezza    | PVD 800x600 | DWT 800x600 | Note                     |
| ------------ | ----------- | ----------- | ------------------------ |
| 100 char     | ✅ 0.3%     | ✅ 3.7%     | Entrambi OK              |
| 1,000 char   | ✅ 3.0%     | ✅ 37%      | DWT al limite            |
| 10,000 char  | ✅ 30%      | ❌ 370%     | Solo PVD                 |
| 100,000 char | ✅ 300%     | ❌ 3700%    | Richiede immagine enorme |

---

## 🧪 Esempio Completo: Workflow PVD

### **Hiding PVD**

```python
img = Image.open("photo_1024x768.png")
message = """
Questo è un messaggio segreto molto lungo che contiene informazioni
importanti. Il testo può includere multiple righe, punteggiatura,
numeri (123) e simboli speciali (!@#$%).
"""

MessageSteganography.RANGES = MessageSteganography.RANGES_QUALITY
MessageSteganography.PAIR_STEP = 1
MessageSteganography.CHANNELS = [0, 1, 2]

stego, metrics, percentage = MessageSteganography.hide_message(
    img,
    message,
    "message_params.json"
)
stego.save("stego_message.png", "PNG")  # PNG lossless!

print(f"Messaggio nascosto: {len(message)} caratteri")
print(f"Percentuale usata: {percentage}%")
print(f"PSNR: {metrics['psnr']:.2f} dB")
```

**Output tipico**:

```text
Nascondendo messaggio con PVD...
TERMINATO - Percentuale di pixel usati con PVD: 5.2% (...)
Messaggio nascosto: 183 caratteri
Percentuale usata: 5.2%
PSNR: 40.15 dB
```

### **Recovery**

```python
stego = Image.open("stego_message.png")

recovered_message = MessageSteganography.get_message(
    stego,
    backup_file="message_params.json"
)

print(f"Recovered: {recovered_message}")

# Verifica identità
assert recovered_message == message  ✓
```

---

## 🧪 Esempio Completo: Workflow DWT

### **Hiding DWT**

```python
img = Image.open("landscape_1920x1080.png")
message = "Secret coordinates: 40.7128°N, 74.0060°W"

MessageSteganography.WAVELET = "haar"
MessageSteganography.ALPHA = 0.1
MessageSteganography.BANDS = ["cH", "cV"]
MessageSteganography.USE_ALL_CHANNELS = True

stego, metrics, percentage = MessageSteganography.hide_message(
    img,
    message,
    "dwt_message_params.json"
)
stego.save("stego_dwt_message.png", "PNG")

# Test robustezza: salva come JPEG
stego.save("stego_dwt_message.jpg", "JPEG", quality=90)
```

### **Recovery (anche dopo JPEG!)**

```python
# Carica da JPEG compresso
stego_jpeg = Image.open("stego_dwt_message.jpg")

recovered = MessageSteganography.get_message(
    stego_jpeg,
    backup_file="dwt_message_params.json"
)

print(f"Recovered from JPEG: {recovered}")

# Probabile successo anche con quality=90
# (con quality < 80 può fallire)
```

---

## 📝 Conclusioni

### **PVD Message Hiding**

- **Pro**: Alta capacità, semplice, veloce, perfetto per messaggi lunghi
- **Contro**: Non robusto, richiede PNG lossless
- **Caso d'uso ideale**: Nascondere documenti, email, comunicazioni private in immagini non modificate

### **DWT Message Hiding**

- **Pro**: Robusto, alta qualità, resiste a compressione leggera, header sicuro
- **Contro**: Capacità limitata, complesso, richiede parametri corretti
- **Caso d'uso ideale**: Watermarking testuale, comunicazioni brevi resistenti, metadati protetti

### **Raccomandazione Generale**

- **Chat/Messaggistica**: PVD (alta capacità, invia PNG)
- **Social Media**: DWT (resiste a processamento JPEG)
- **Steganografia professionale**: DWT (sicurezza e robustezza)
- **Grandi volumi di testo**: PVD (capacità superiore)
