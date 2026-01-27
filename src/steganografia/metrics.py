"""
Metriche di qualità per la steganografia
Calcola SSIM (Structural Similarity Index) e PSNR (Peak Signal-to-Noise Ratio)
"""

import warnings

import numpy as np
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim


class QualityMetrics:
    """Classe per calcolare metriche di qualità delle immagini"""

    @staticmethod
    def calculate_metrics(original_img: Image.Image, modified_img: Image.Image) -> dict:
        """
        Calcola SSIM e PSNR tra immagine originale e modificata

        Args:
            original_img: Immagine originale (host)
            modified_img: Immagine modificata (con steganografia)

        Returns:
            Dizionario con le metriche:
            {
                'ssim': valore SSIM (0-1, 1 = identiche),
                'psnr': valore PSNR in dB (maggiore = migliore)
            }
        """
        # Converte in RGB se necessario
        if original_img.mode != "RGB":
            original_img = original_img.convert("RGB")
        if modified_img.mode != "RGB":
            modified_img = modified_img.convert("RGB")

        # Verifica che le dimensioni siano uguali
        if original_img.size != modified_img.size:
            raise ValueError(
                f"Le immagini devono avere le stesse dimensioni. "
                f"Originale: {original_img.size}, Modificata: {modified_img.size}"
            )

        # Converte in array numpy
        original_array = np.array(original_img)
        modified_array = np.array(modified_img)

        # Calcola SSIM (per immagini multichannel)
        ssim_value = ssim(
            original_array,
            modified_array,
            channel_axis=2,  # RGB ha 3 canali
            data_range=255,  # Range dei valori dei pixel (0-255)
        )

        # Calcola PSNR
        # Se le immagini sono identiche, PSNR è infinito (evita warning di divisione per zero)
        if np.array_equal(original_array, modified_array):
            psnr_value = np.inf
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                psnr_value = psnr(original_array, modified_array, data_range=255)

        return {"ssim": ssim_value, "psnr": psnr_value}

    @staticmethod
    def format_metrics(metrics: dict) -> str:
        """
        Formatta le metriche in una stringa leggibile

        Args:
            metrics: Dizionario con le metriche

        Returns:
            Stringa formattata con le metriche
        """
        ssim_val = metrics["ssim"]
        psnr_val = metrics["psnr"]

        # Interpreta SSIM
        if ssim_val >= 0.99:
            ssim_quality = "Eccellente"
        elif ssim_val >= 0.95:
            ssim_quality = "Ottima"
        elif ssim_val >= 0.90:
            ssim_quality = "Buona"
        elif ssim_val >= 0.80:
            ssim_quality = "Discreta"
        else:
            ssim_quality = "Bassa"

        # Interpreta PSNR
        if np.isinf(psnr_val):
            psnr_quality = "Perfetto (immagini identiche)"
            psnr_str = "∞"
        elif psnr_val >= 50:
            psnr_quality = "Eccellente"
            psnr_str = f"{psnr_val:.2f}"
        elif psnr_val >= 40:
            psnr_quality = "Ottima"
            psnr_str = f"{psnr_val:.2f}"
        elif psnr_val >= 30:
            psnr_quality = "Buona"
            psnr_str = f"{psnr_val:.2f}"
        elif psnr_val >= 20:
            psnr_quality = "Discreta"
            psnr_str = f"{psnr_val:.2f}"
        else:
            psnr_quality = "Bassa"
            psnr_str = f"{psnr_val:.2f}"

        return f"SSIM: {ssim_val:.4f} ({ssim_quality}) | " f"PSNR: {psnr_str} dB ({psnr_quality})"
