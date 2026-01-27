"""
Configurazioni e costanti per l'applicazione di steganografia
"""

# Modalità di compressione
class CompressionMode:
    NO_ZIP = 0
    FILE = 1
    DIR = 2

# Validazione parametri
class ValidationLimits:
    MIN_LSB = 0
    MAX_LSB = 8
    MIN_MSB = 1
    MAX_MSB = 8
    MIN_N = 0
    MAX_N = 8
    MIN_DIV = 0.0

# Configurazioni UI
class UIConfig:
    PAGE_TITLE = "Steganografia App"
    PAGE_ICON = "🔒"
    LAYOUT = "wide"
    MAX_IMAGE_DISPLAY_WIDTH = 400

# Tipi di dati supportati
class DataType:
    STRING = "string"
    IMAGE = "image"
    BINARY = "binary"

# Metodi di steganografia
class SteganographyMethod:
    LSB = "lsb"  # Least Significant Bit (default)
    DWT = "dwt"  # Discrete Wavelet Transform
    PVD = "pvd"  # Pixel Value Differencing
    
    @staticmethod
    def get_all():
        return [SteganographyMethod.LSB, SteganographyMethod.DWT, SteganographyMethod.PVD]
    
    @staticmethod
    def get_display_names():
        return {
            SteganographyMethod.LSB: "LSB (Least Significant Bit)",
            SteganographyMethod.DWT: "DWT (Discrete Wavelet Transform)",
            SteganographyMethod.PVD: "PVD (Pixel Value Differencing)"
        }

# Formati file supportati
class SupportedFormats:
    IMAGE_FORMATS = ['png', 'jpg', 'jpeg']
    BACKUP_FORMATS = ['dat']

# Messaggi di errore
class ErrorMessages:
    IMAGE_TOO_SMALL_MESSAGE = "Immagine troppo piccola per nascondere il messaggio. Messaggio: {msg_len} caratteri, Immagine: {width}x{height}"
    IMAGE_TOO_SMALL_IMAGE = "Immagine host troppo piccola per nascondere l'altra immagine. Host: {host_width}x{host_height}, Da nascondere: {secret_width}x{secret_height}"
    IMAGE_TOO_SMALL_FILE = "Immagine troppo piccola per nascondere il file. File: {file_size} bytes, Immagine: {width}x{height}"
    INVALID_LSB = "Il valore di LSB deve essere compreso tra 1 e 8 oppure 0 per la modalità automatica"
    INVALID_MSB = "Il valore di MSB deve essere compreso tra 1 e 8 oppure 0 per la modalità automatica"
    INVALID_N = "Il valore di N deve essere compreso tra 1 e 8, oppure 0 per la modalità automatica"
    INVALID_ZIP_MODE = "La modalità di compressione deve essere 0 (nessuna), 1 (file) o 2 (directory)"
    LSB_GREATER_MSB = "Il valore di LSB deve essere minore di MSB"
    DIV_EXCESSIVE = "Il valore di DIV ({div}) è eccessivo. Prova con 0 per il calcolo automatico"
    PARAMS_MISSING = "Parametri mancanti per il recupero. Fornisci un file backup (.dat) o inserisci i parametri manualmente"
    NO_MESSAGE_FOUND = "Nessun messaggio valido trovato nell'immagine"
    DECODE_FAILED = "Impossibile decodificare il messaggio dall'immagine. Verifica che contenga davvero un messaggio nascosto"
    IMAGE_RECONSTRUCTION_FAILED = "Impossibile ricostruire l'immagine nascosta. Verifica i parametri di recupero. Errore: {error}"