# 🔒 Steganography WebApp

## Advanced Steganography Application with Multiple Algorithms

A comprehensive web application for steganography that allows hiding and recovering different types of data (text, images, binary files) within images using three advanced techniques: LSB (Least Significant Bit), DWT (Discrete Wavelet Transform), and PVD (Pixel Value Differencing).

## 🌐 Live Demo

Prova l'applicazione online su [Streamlit Cloud](https://steg-app.streamlit.app)

## 📋 Indice

- [Caratteristiche](#caratteristiche)
- [Architettura del Progetto](#architettura-del-progetto)
- [Installazione](#installazione)
- [Setup Git Hooks](#setup-git-hooks)
- [Utilizzo](#utilizzo)
- [Struttura del Progetto](#struttura-del-progetto)
- [Algoritmi di Steganografia](#algoritmi-di-steganografia)
- [Contribuire](#contribuire)
- [Licenza](#licenza)

## ✨ Caratteristiche

### Algoritmi di Steganografia

- **LSB (Least Significant Bit)**: Modifica i bit meno significativi dei pixel per nascondere dati
- **DWT (Discrete Wavelet Transform)**: Utilizza trasformate wavelet per una maggiore robustezza
- **PVD (Pixel Value Differencing)**: Sfrutta le differenze tra pixel adiacenti per capacità variabile

### Tipi di Dati Supportati

- **Stringhe**: Nasconde testo semplice all'interno delle immagini
- **Immagini**: Nasconde un'immagine all'interno di un'altra
- **File Binari**: Supporta qualsiasi tipo di file binario

### Funzionalità Avanzate

- 💾 **Backup Automatico**: Sistema intelligente di recupero parametri
- 🎨 **Interfaccia Intuitiva**: UI Streamlit user-friendly con selezione visuale
- 🔄 **Conversioni Automatiche**: Gestione formati RGB/RGBA/Grayscale
- 📊 **Metriche di Qualità**: Calcolo PSNR e SSIM
- 🛡️ **Validazione Robusta**: Controlli completi su input e parametri
- 🧹 **Clean Architecture**: Codice modulare e manutenibile

## 🏗️ Architettura del Progetto

Il progetto segue un'architettura modulare con separazione delle responsabilità:

```
├── Frontend (UI)
│   ├── Streamlit App (app.py)
│   └── UI Components (src/ui/)
├── Core Business Logic
│   ├── LSB Algorithm (src/steganografia/lsb/)
│   ├── DWT Algorithm (src/steganografia/dwt/)
│   ├── PVD Algorithm (src/steganografia/pvd/)
│   └── Shared Utilities (src/steganografia/)
└── Configuration
    └── Constants & Settings (config/)
```

## 🚀 Installazione

### Prerequisiti

- Python 3.8+
- pip (package manager)

### Setup Rapido

1. **Clona il repository:**

```bash
git clone https://github.com/GiuseppeBellamacina/Steganography-WebApp.git
cd Steganograpgy-WebApp
```

2. **Installa le dipendenze:**

```bash
uv sync [--all-extras]
```

3. **Avvia l'applicazione:**

```bash
streamlit run app.py
```

## ⚙️ Setup Git Hooks

Dopo aver clonato il repository, configura i git hooks per la formattazione automatica del codice:

```bash
# Su Linux/Mac
chmod +x setup-hooks.sh
./setup-hooks.sh

# Su Windows (Git Bash)
bash setup-hooks.sh
```

Questo abiliterà il pre-commit hook che esegue automaticamente:

- `ruff check . --fix` - Linting e fix automatici
- `isort .` - Ordinamento degli import
- `black .` - Formattazione del codice

I file modificati vengono ri-aggiunti allo stage automaticamente prima del commit.

### Dipendenze Principali

- `streamlit`: Interfaccia web interattiva
- `numpy`: Operazioni matematiche su array
- `opencv-python`: Elaborazione avanzata delle immagini
- `Pillow`: Manipolazione delle immagini
- `PyWavelets`: Trasformate wavelet per DWT
- `scikit-image`: Metriche di qualità e analisi immagini

## 💻 Utilizzo

### Interfaccia Web (Streamlit)

1. **Avvia l'applicazione:**

```bash
streamlit run app.py
```

2. **Seleziona il metodo di steganografia:**
   - **LSB**: Per nascondere rapidamente dati
   - **DWT**: Per maggiore robustezza
   - **PVD**: Per capacità adattiva

3. **Scegli il tipo di dato:**
   - Stringhe
   - Immagini
   - File binari

4. **Seleziona l'operazione:**
   - **Hide**: Nascondere dati
   - **Recover**: Recuperare dati

5. **Carica l'immagine** e segui le istruzioni interattive

## ⚙️ Strumenti di Sviluppo

### Formattazione del Codice

Il progetto utilizza **Black** e **isort** per mantenere uno stile di codice consistente.

```bash
# Formatta il codice con Black
black src/ config/

# Ordina gli import con isort
isort src/ config/

# Controlla la formattazione (senza modificare)
black src/ config/ --check
isort src/ config/ --check-only
```

## 📁 Struttura del Progetto

```
Steganography-WebApp/
├── 🌐 app.py                    # Streamlit application
├── ⚙️ pyproject.toml            # Project configuration
├── 📄 README.md                 # Documentation
│
├── 📁 src/                      # Source code
│   ├── 📁 steganografia/        # Core steganography algorithms
│   │   ├── backup.py            # Backup system
│   │   ├── bit_operations.py    # Bit manipulation
│   │   ├── core.py              # Core functions
│   │   ├── file_utils.py        # File utilities
│   │   ├── metrics.py           # Quality metrics (PSNR, SSIM)
│   │   ├── validator.py         # Input validation
│   │   │
│   │   ├── 📁 lsb/              # LSB algorithm
│   │   │   ├── binary_operations.py
│   │   │   ├── image_operations.py
│   │   │   └── message_operations.py
│   │   │
│   │   ├── 📁 dwt/              # DWT algorithm
│   │   │   ├── binary_operations.py
│   │   │   ├── image_operations.py
│   │   │   └── message_operations.py
│   │   │
│   │   └── 📁 pvd/              # PVD algorithm
│   │       ├── binary_operations.py
│   │       ├── image_operations.py
│   │       └── message_operations.py
│   │
│   └── 📁 ui/                   # User interface components
│       ├── components.py        # Reusable components
│       ├── hide_pages.py        # Hide data pages
│       ├── image_utils.py       # Image utilities
│       ├── layout.py            # Main layout
│       ├── recover_pages.py     # Recover data pages
│       └── styles.py            # CSS styles
│
├── 📁 config/                   # Configuration
│   └── constants.py             # Global constants
│
└── 📁 assets/                   # Static resources
    ├── 📁 img/                  # Sample images
    ├── 📁 pdf/                  # PDF files
    ├── 📁 text/                 # Text files
    └── 📁 video/                # Video files
```

## 🎯 Algoritmi di Steganografia

### ⚡ LSB (Least Significant Bit)

Modifica i bit meno significativi dei pixel per nascondere i dati. Semplice e veloce, ideale per la maggior parte delle applicazioni.

**Vantaggi**: Elevata capacità, veloce
**Svantaggi**: Vulnerabile a compressione e modifiche dell'immagine

### 🧪 DWT (Discrete Wavelet Transform)

Utilizza trasformate wavelet per incorporare i dati nei coefficienti di frequenza dell'immagine. Più robusto rispetto a LSB.

**Vantaggi**: Resistente a compressione JPEG, più sicuro
**Svantaggi**: Capacità inferiore, più lento

### 🔀 PVD (Pixel Value Differencing)

Sfrutta le differenze tra pixel adiacenti per nascondere quantità variabili di dati in base alle caratteristiche locali dell'immagine.

**Vantaggi**: Adattivo, buon compromesso capacità/qualità
**Svantaggi**: Più complesso, velocità media

## 📈 Performance e Limiti

- **Capacità**: Varia in base all'algoritmo e alle dimensioni dell'immagine host
- **Qualità**: Perdita minima di qualità (misurabile con PSNR)
- **Formati Supportati**: PNG, JPEG, BMP, TIFF e altri formati comuni
- **Metriche**: Calcolo automatico di PSNR, SSIM per valutare la qualità

## 🤝 Contribuire

1. Fork del progetto
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push del branch (`git push origin feature/AmazingFeature`)
5. Apertura di una Pull Request

### Guidelines per Contribuire

- **Formattazione**: Esegui `black src/ config/` e `isort src/ config/` prima di committare
- **Naming Conventions**: Segui le convenzioni di naming esistenti
- **Documentazione**: Aggiungi docstring e commenti per nuove funzionalità
- **Code Quality**: Il codice deve passare tutti i controlli CI (Black, isort)
- **Type Hints**: Utilizza type hints per migliorare la leggibilità
- **Error Handling**: Gestisci correttamente le eccezioni

## 📄 Licenza

Questo progetto è distribuito sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

---

**🔒 Steganography WebApp** - _Hiding is an art, revealing is a science_
