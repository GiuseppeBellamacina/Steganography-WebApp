"""
Operazioni di steganografia per le immagini
"""

import numpy as np
from PIL import Image

from config.constants import DataType, ErrorMessages

from ..backup import backup_system
from ..bit_operations import set_last_n_bits
from ..metrics import QualityMetrics
from ..validator import ParameterValidator


class ImageSteganography:
    """Classe per operazioni di steganografia su immagini"""

    @staticmethod
    def hide_image(
        host_img: Image.Image,
        secret_img: Image.Image,
        lsb: int = 0,
        msb: int = 8,
        div: float = 0,
        backup_file: str | None = None,
    ) -> tuple[Image.Image, int, int, float, int, int, dict]:
        """
        Nasconde un'immagine in un'altra

        Args:
            host_img: Immagine che nasconde (più grande)
            secret_img: Immagine da nascondere (più piccola)
            lsb: Numero di bit meno significativi di host_img da modificare
            msb: Numero di bit più significativi di secret_img da nascondere
            div: Divisore per la distribuzione
            backup_file: File dove salvare i parametri

        Returns:
            Tupla con (immagine_risultato, lsb_finale, msb_finale, div_finale, width, height, metrics)
            dove metrics è un dizionario con 'ssim' e 'psnr'
        """
        # Validazione parametri
        ParameterValidator.validate_lsb(lsb)
        ParameterValidator.validate_msb(msb)
        ParameterValidator.validate_lsb_msb_relationship(lsb, msb)

        # Determina LSB automatico se necessario
        if lsb == 0:
            lsb = 1
            while (lsb * host_img.width * host_img.height * 3) < (
                msb * secret_img.width * secret_img.height * 3
            ):
                lsb += 1
                if lsb > 8:
                    raise ValueError(
                        ErrorMessages.IMAGE_TOO_SMALL_IMAGE.format(
                            host_width=host_img.width,
                            host_height=host_img.height,
                            secret_width=secret_img.width,
                            secret_height=secret_img.height,
                        )
                    )

        # Verifica dimensioni
        ParameterValidator.validate_image_size_for_image(host_img, secret_img, lsb, msb)

        # Converte immagini in RGB
        if host_img.mode != "RGB":
            host_img = host_img.convert("RGB")
        if secret_img.mode != "RGB":
            secret_img = secret_img.convert("RGB")

        # Inizia a nascondere l'immagine
        print("Nascondendo immagine...")
        arr1 = np.array(host_img).flatten().copy()
        arr2 = np.array(secret_img).flatten().copy()

        if div == 0:
            div = (len(arr1) * lsb) / (len(arr2) * msb)
        else:
            ParameterValidator.validate_div_for_images(
                div, len(arr1), len(arr2), lsb, msb
            )

        # Algoritmo per nascondere l'immagine
        pos_in_img1 = 0.0
        bit_buffer = ""

        for i in range(0, len(arr2), 3):  # Processa ogni pixel di secret_img (RGB)
            if i + 2 >= len(arr2):
                break

            # Estrai i bit più significativi da ogni canale di secret_img
            r_bits = format(arr2[i], "08b")[:msb]
            g_bits = format(arr2[i + 1], "08b")[:msb]
            b_bits = format(arr2[i + 2], "08b")[:msb]

            # Aggiungi tutti i bit al buffer
            bit_buffer += r_bits + g_bits + b_bits

            # Inserisci i bit in host_img quando ne abbiamo abbastanza
            while len(bit_buffer) >= lsb and pos_in_img1 < len(arr1):
                # Prendi lsb bit dal buffer
                bits_to_hide = bit_buffer[:lsb]
                bit_buffer = bit_buffer[lsb:]

                # Nascondili nel pixel corrente di host_img
                pixel_pos = int(pos_in_img1)
                if pixel_pos < len(arr1):
                    arr1[pixel_pos] = set_last_n_bits(
                        arr1[pixel_pos], bits_to_hide, lsb
                    )

                # Avanza nella posizione di host_img
                pos_in_img1 += div

        # Gestisci eventuali bit rimanenti nel buffer
        if bit_buffer and pos_in_img1 < len(arr1):
            # Padda i bit rimanenti con zeri a destra per raggiungere lsb bit
            while len(bit_buffer) < lsb:
                bit_buffer += "0"

            pixel_pos = int(pos_in_img1)
            if pixel_pos < len(arr1):
                arr1[pixel_pos] = set_last_n_bits(
                    arr1[pixel_pos], bit_buffer[:lsb], lsb
                )

        # Crea immagine risultato
        w, h = secret_img.width, secret_img.height
        percentage = format(
            (msb * secret_img.width * secret_img.height * 3)
            / (lsb * host_img.width * host_img.height * 3)
            * 100,
            ".2f",
        )
        print(
            f"TERMINATO - Percentuale di pixel usati con lsb={lsb}, msb={msb} e div={div:.2f}: {percentage}%"
        )

        result_img = Image.fromarray(arr1.reshape(host_img.height, host_img.width, 3))

        # Calcola metriche di qualità (SSIM e PSNR)
        metrics = QualityMetrics.calculate_metrics(host_img, result_img)
        print(
            f"Metriche di qualità - SSIM: {metrics['ssim']:.4f}, PSNR: {metrics['psnr']:.2f} dB"
        )

        # Salva i parametri per il recupero
        params = {
            "lsb": lsb,
            "msb": msb,
            "div": div,
            "width": w,
            "height": h,
            "method": "image",
            "original_img1_size": (host_img.width, host_img.height),
            "original_img2_size": (secret_img.width, secret_img.height),
        }
        backup_system.save_backup_data(DataType.IMAGE, params, backup_file)

        return (result_img, lsb, msb, div, w, h, metrics)

    @staticmethod
    def get_image(
        img: Image.Image,
        output_path: str,
        lsb: int | None = None,
        msb: int | None = None,
        div: float | None = None,
        width: int | None = None,
        height: int | None = None,
        backup_file: str | None = None,
    ) -> Image.Image:
        """
        Recupera un'immagine nascosta da un'altra

        Args:
            img: Immagine che contiene l'immagine nascosta
            output_path: Percorso dove salvare l'immagine recuperata
            lsb, msb, div, width, height: Parametri per il recupero
            backup_file: File di backup dei parametri

        Returns:
            Immagine recuperata
        """
        print("Cercando immagine nascosta...")

        # Recupera parametri automaticamente se non forniti
        if any(param is None for param in [lsb, msb, div, width, height]):
            print("Alcuni parametri mancanti, cercando nei backup...")

            # Controlla se esistono parametri di backup
            backup_data = None
            if backup_file:
                backup_data = backup_system.load_backup_data(backup_file)

            # Se non ci sono backup file, controlla le variabili locali
            if not backup_data:
                recent_params = backup_system.get_last_params(DataType.IMAGE)
                if recent_params:
                    print(
                        "Usando parametri dall'ultima operazione di occultamento immagini"
                    )
                    backup_data = {"type": DataType.IMAGE, "params": recent_params}

            if backup_data and "params" in backup_data:
                params = backup_data["params"]
                lsb = lsb if lsb is not None else params.get("lsb")
                msb = msb if msb is not None else params.get("msb")
                div = div if div is not None else params.get("div")
                width = width if width is not None else params.get("width")
                height = height if height is not None else params.get("height")
                print(
                    f"Parametri recuperati: lsb={lsb}, msb={msb}, div={div:.2f}, size={width}x{height}"
                )
            else:
                raise ValueError(ErrorMessages.PARAMS_MISSING)

        # Verifica che tutti i parametri siano validi
        ParameterValidator.validate_recovery_params(lsb, msb, div, width, height)

        # Assert per il type checker - sappiamo che i parametri non sono None dopo la validazione
        assert lsb is not None and msb is not None and div is not None
        assert width is not None and height is not None

        # Recupera immagine
        size = width * height * 3
        arr = np.array(img).flatten().copy()
        res = np.zeros(size, dtype=np.uint8)

        # Algoritmo per estrarre l'immagine
        pos_in_img1 = 0.0
        bit_buffer = ""
        pixels_written = 0

        while pixels_written < size and pos_in_img1 < len(arr):
            # Estrai lsb bit dal pixel corrente
            pixel_pos = int(pos_in_img1)
            if pixel_pos < len(arr):
                extracted_bits = format(arr[pixel_pos], "08b")[-lsb:]
                bit_buffer += extracted_bits

            # Quando abbiamo abbastanza bit, ricostruisci un pixel
            while len(bit_buffer) >= msb and pixels_written < size:
                # Prendi msb bit dal buffer
                pixel_bits = bit_buffer[:msb]
                bit_buffer = bit_buffer[msb:]

                # Padda a sinistra con zeri per ottenere 8 bit
                while len(pixel_bits) < 8:
                    pixel_bits = pixel_bits + "0"

                # Converte in valore pixel e salva
                res[pixels_written] = int(pixel_bits, 2)
                pixels_written += 1

            # Avanza nella posizione
            pos_in_img1 += div

        # Converte il risultato in immagine
        try:
            res_img = Image.fromarray(res.reshape((height, width, 3)))
            res_img.save(output_path)
            print(f"IMMAGINE TROVATA - Immagine salvata come {output_path}")
            return res_img
        except Exception as e:
            raise ValueError(
                ErrorMessages.IMAGE_RECONSTRUCTION_FAILED.format(error=str(e))
            )
