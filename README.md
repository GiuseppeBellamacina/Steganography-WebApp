# 🔒 Steganografia

## Applicazione per Nascondere Dati nelle Immagini

Un'applicazione completa per la steganografia che permette di nascondere e recuperare diversi tipi di dati (stringhe, immagini, file binari) all'interno di immagini utilizzando tecniche LSB (Least Significant Bit).

## 🌐 Live Demo

Prova l'applicazione online su [Streamlit Cloud](https://steg-app.streamlit.app)

## 📋 Indice

- [Caratteristiche](#caratteristiche)
- [Architettura del Progetto](#architettura-del-progetto)
- [Installazione](#installazione)
- [Utilizzo](#utilizzo)
- [API](#api)
- [Testing](#testing)
- [Struttura del Progetto](#struttura-del-progetto)
- [Contribuire](#contribuire)
- [Licenza](#licenza)

## ✨ Caratteristiche

### Tipi di Dati Supportati

- **Stringhe**: Nasconde testo semplice all'interno delle immagini
- **Immagini**: Nasconde un'immagine all'interno di un'altra
- **File Binari**: Supporta qualsiasi tipo di file binario con opzioni di compressione

### Modalità di Compressione

- **NO_ZIP**: Nessuna compressione
- **FILE**: Compressione di singoli file
- **DIR**: Compressione di intere directory

### Funzionalità Avanzate

- 💾 **Backup Automatico**: Sistema intelligente di recupero parametri
- 🎨 **Interfaccia Intuitiva**: UI Streamlit user-friendly
- 🔄 **Conversioni Automatiche**: Gestione formati RGB/RGBA/Grayscale
- 🧪 **Alta Qualità**: Test coverage >75% per affidabilità garantita
- 🛡️ **Validazione Robusta**: Controlli completi su input e parametri
- 🧹 **Clean Architecture**: Codice modulare e manutenibile

## 🏗️ Architettura del Progetto

Il progetto segue un'architettura modulare con separazione delle responsabilità:

```
├── Frontend (UI)
│   ├── Streamlit App (app.py)
│   └── UI Components (src/ui/)
├── Core Business Logic
│   └── Steganografia Operations (src/steganografia/)
├── Configuration
│   └── Constants & Settings (config/)
└── Testing
    └── Comprehensive Test Suite (tests/)
```

## 🚀 Installazione

### Prerequisiti

- Python 3.7+
- pip (package manager)

### Setup Rapido

1. **Clona il repository:**

```bash
git clone https://github.com/GiuseppeBellamacina/Steganography-WebApp.git
cd Steganografia-QD
```

2. **Installa le dipendenze:**

```bash
pip install -r requirements.txt
```

3. **Avvia l'applicazione:**

```bash
streamlit run app.py
```

### Dipendenze Principali

- `numpy`: Operazioni matematiche su array
- `pillow`: Manipolazione delle immagini
- `streamlit`: Interfaccia web interattiva

## 💻 Utilizzo

### Interfaccia Web (Streamlit)

1. **Avvia l'applicazione:**

```bash
streamlit run app.py
```

2. **Seleziona la modalità:**

   - **Nascondere dati**: Per occultare informazioni
   - **Recuperare dati**: Per estrarre informazioni nascoste

3. **Scegli il tipo di dato:**

   - Stringhe
   - Immagini
   - File binari

4. **Carica l'immagine host** e segui le istruzioni dinamiche

## 📚 API

### Moduli Principali

#### `steganografia.core`

- `hide_message()`: Nasconde stringhe
- `get_message()`: Recupera stringhe
- `hide_image()`: Nasconde immagini
- `get_image()`: Recupera immagini
- `hide_bin_file()`: Nasconde file binari
- `get_bin_file()`: Recupera file binari

#### `src.steganografia.*`

- `StringSteganography`: Operazioni su stringhe
- `ImageSteganography`: Operazioni su immagini
- `BinarySteganography`: Operazioni su file binari
- `backup_system`: Sistema di backup automatico
- `FileValidator`: Validazione input

#### `src.ui.*`

- `AppLayout`: Layout e configurazione UI
- `HideDataPages`: Pagine per nascondere dati
- `RecoverDataPages`: Pagine per recuperare dati
- `DynamicInstructions`: Istruzioni contestuali

## 🧪 Testing

Il progetto include una **suite di test completa e robusta** con coverage **superiore al 78%**.

### Eseguire i Test

```bash
# Esegui tutti i test
pytest

# Test con coverage report
pytest --cov=src/steganografia --cov=config --cov-report=html

# Test con output dettagliato
pytest -v

# Test specifici per modulo
pytest tests/test_string_operations.py
pytest tests/test_image_operations.py
pytest tests/test_binary_operations.py
```

### Test Coverage Dettagliata

Il progetto mantiene un'alta qualità del codice attraverso test completi:

- ✅ **Operazioni su stringhe** - Test di encoding, decoding, compressione
- ✅ **Operazioni su immagini** - Test LSB/MSB, conversioni formato, backup automatico
- ✅ **Operazioni su file binari** - Test compressione, recupero parametri, file di grandi dimensioni
- ✅ **Sistema di backup** - Test salvataggio/recupero parametri automatico
- ✅ **Validazione degli input** - Test controlli formato, dimensioni, integrità
- ✅ **Gestione degli errori** - Test edge cases e condizioni eccezionali
- ✅ **Utility per file** - Test operazioni I/O, conversioni binarie
- ✅ **Operazioni sui bit** - Test manipolazione bit-level

## 📁 Struttura del Progetto

```
Steganografia/
├── 🌐 app.py                    # App Streamlit
├── 📄 requirements.txt          # Dipendenze Python
├── ⚙️ setup.cfg                # Configurazione test
├── 📄 README.md                 # Documentazione
│
├── 📁 src/                      # Codice sorgente principale
│   ├── 📁 steganografia/        # Core business logic
│   │   ├── core.py              # API principale
│   │   ├── string_operations.py
│   │   ├── image_operations.py
│   │   ├── binary_operations.py
│   │   ├── backup.py            # Sistema backup
│   │   ├── validator.py         # Validazione input
│   │   ├── file_utils.py        # Utility file
│   │   └── bit_operations.py    # Operazioni sui bit
│   │
│   └── 📁 ui/                  # Componenti interfaccia utente
│       ├── layout.py            # Layout principale
│       ├── hide_pages.py        # Pagine occultamento
│       ├── recover_pages.py     # Pagine recupero
│       ├── components.py        # Componenti riutilizzabili
│       └── image_utils.py       # Utility immagini
│
├── 📁 config/                   # Configurazione
│   └── constants.py             # Costanti globali
│
├── 📁 tests/                    # Suite di test
|   ├── test_app.py
|   ├── test_ui.py
│   ├── test_string_operations.py
│   ├── test_image_operations.py
│   ├── test_binary_operations.py
│   ├── test_backup.py
│   ├── test_validator.py
│   ├── test_file_utils.py
│   ├── test_bit_operations.py
│   └── test_error_handling.py
│
└── 📁 assets/                  # Risorse statiche
    ├── 📁 img/                 # Immagini di esempio
    ├── 📁 pdf/                 # File PDF di test
    ├── 📁 video/               # Video di esempio
    └── 📁 text/                # File di testo
```

## 🎯 Algoritmi di Steganografia

### LSB (Least Significant Bit)

Il progetto utilizza principalmente la tecnica LSB che modifica i bit meno significativi dei pixel delle immagini per nascondere i dati.

### Parametri Configurabili

- **LSB**: Numero di bit meno significativi da utilizzare
- **MSB**: Numero di bit più significativi
- **DIV**: Fattore di divisione per ottimizzazione
- **Compressione**: Modalità di compressione dei dati

## 📈 Performance e Limiti

- **Capacità**: Dipende dalle dimensioni dell'immagine host
- **Qualità**: Perdita minima di qualità dell'immagine
- **Formati Supportati**: PNG, JPEG, BMP, TIFF
- **Dimensioni**: Ottimizzazione automatica in base alla capacità

## 🤝 Contribuire

1. Fork del progetto
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push del branch (`git push origin feature/AmazingFeature`)
5. Apertura di una Pull Request

### Guidelines per Contribuire

- **Test Coverage**: Mantieni il test coverage sopra il **75%**
- **Naming Conventions**: Segui le convenzioni di naming esistenti
- **Documentazione**: Aggiungi docstring e commenti per nuove funzionalità
- **Code Quality**: Testa il codice prima di fare commit
- **Type Hints**: Utilizza type hints per migliorare la leggibilità
- **Error Handling**: Gestisci correttamente le eccezioni

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 👨‍💻 Autori

**[Giuseppe](https://github.com/GiuseppeBellamacina)**

**[Beatrice](https://github.com/Beatrix04-lo)**

**[Daniele](https://github.com/danii909)**

**[Simone](https://github.com/simone002)**

---

**🔒 Steganografia** - _Nascondere è un'arte, rivelare è una scienza_
