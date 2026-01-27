"""
Pagine per nascondere dati nell'interfaccia Streamlit
"""

import io
import os

import streamlit as st
from PIL import Image

from config.constants import CompressionMode, SteganographyMethod

from .components import cleanup_temp_file, create_download_button, save_uploaded_file
from .image_utils import ImageDisplay


class HideDataPages:
    """Gestisce le pagine per nascondere dati"""

    @staticmethod
    def hide_string_page(selected_method):
        """Pagina per nascondere stringhe"""
        from src.steganografia import hide_message

        st.subheader("📝 Nascondere Stringa")

        # Upload dell'immagine host
        host_image = st.file_uploader(
            "🖼️ Carica l'immagine host:",
            type=["png", "jpg", "jpeg"],
            key="hide_string_host_image",
        )

        # Mostra anteprima dell'immagine host
        if host_image:
            ImageDisplay.show_resized_image(host_image, "🖼️ Immagine Host", max_width=400)
            ImageDisplay.show_image_details(host_image, "Dettagli Immagine Host")

        message = st.text_area(
            "🔒 Inserisci il messaggio da nascondere:",
            height=100,
            placeholder="Scrivi qui il tuo messaggio segreto...",
        )

        # Configurazione metodo PVD
        if selected_method == SteganographyMethod.PVD:
            from src.steganografia.pvd.message_operations import (
                MessageSteganography as PVD_Msg,
            )

            preset = st.selectbox(
                "📋 Preconfigurazione PVD:",
                options=[
                    "🎨 Qualità",
                    "📦 Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="pvd_msg_hide_preset",
            )

            if preset == "🎨 Qualità":
                PVD_Msg.RANGES = PVD_Msg.RANGES_QUALITY
                PVD_Msg.PAIR_STEP = 1
                PVD_Msg.CHANNELS = [0, 1, 2]
                st.info("✅ Ranges qualità, step=1, tutti i canali")
            elif preset == "📦 Capacità":
                PVD_Msg.RANGES = PVD_Msg.RANGES_CAPACITY
                PVD_Msg.PAIR_STEP = 1
                PVD_Msg.CHANNELS = [0, 1, 2]
                st.info("📦 Ranges capacità, step=1, tutti i canali")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    use_quality = st.checkbox(
                        "Usa ranges qualità", value=True, key="pvd_msg_hide_quality"
                    )
                    pair_step_msg = st.slider("Sparsità", 1, 4, 1, key="pvd_msg_hide_step")
                with col2:
                    channels_msg = st.multiselect(
                        "Canali",
                        ["R (0)", "G (1)", "B (2)"],
                        default=["R (0)", "G (1)", "B (2)"],
                        key="pvd_msg_hide_channels",
                    )
                    channels_list = (
                        [int(ch.split("(")[1][0]) for ch in channels_msg]
                        if channels_msg
                        else [0, 1, 2]
                    )

                PVD_Msg.RANGES = PVD_Msg.RANGES_QUALITY if use_quality else PVD_Msg.RANGES_CAPACITY
                PVD_Msg.PAIR_STEP = pair_step_msg
                PVD_Msg.CHANNELS = channels_list

        # Configurazione metodo DWT
        elif selected_method == SteganographyMethod.DWT:
            from src.steganografia.dwt.message_operations import (
                MessageSteganography as DWT_Msg,
            )

            preset = st.selectbox(
                "📋 Preconfigurazione DWT:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Qualità",
                    "💪 Robustezza",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="dwt_msg_hide_preset",
                help="Bilanciato: uso generale. Qualità: invisibile. Robustezza: resiste a compressione/rumore."
            )

            if preset == "⚖️ Bilanciato":
                DWT_Msg.WAVELET = "haar"
                DWT_Msg.ALPHA = 0.1
                st.info("⚖️ Wavelet Haar, alpha 0.1 - Compromesso qualità/robustezza")
            elif preset == "🎨 Qualità":
                DWT_Msg.WAVELET = "haar"
                DWT_Msg.ALPHA = 0.05
                st.info("🎨 Wavelet Haar, alpha 0.05 - Minima distorsione, fragile")
            elif preset == "💪 Robustezza":
                DWT_Msg.WAVELET = "db4"
                DWT_Msg.ALPHA = 0.3
                st.info("💪 Wavelet Daubechies 4, alpha 0.3 - Più robusto, resiste meglio a modifiche")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    wavelet = st.selectbox(
                        "Tipo Wavelet",
                        options=["haar", "db2", "db4", "db8", "sym2", "sym4", "coif1"],
                        index=0,
                        help="haar=veloce standard, db/sym=più robuste",
                        key="dwt_msg_hide_wavelet"
                    )
                with col2:
                    alpha = st.slider(
                        "Alpha (forza embedding)",
                        min_value=0.05,
                        max_value=0.5,
                        value=0.1,
                        step=0.05,
                        help="Basso=invisibile ma fragile, Alto=visibile ma robusto",
                        key="dwt_msg_hide_alpha"
                    )

                DWT_Msg.WAVELET = wavelet
                DWT_Msg.ALPHA = alpha

        output_name = st.text_input("📁 Nome file output", value="image_with_message.png")

        if st.button("🔒 Nascondi Messaggio", type="primary"):
            if host_image and message:
                # Pulisci risultati precedenti
                if "hide_string_result" in st.session_state:
                    del st.session_state["hide_string_result"]
                try:
                    # Salva immagine temporaneamente
                    host_path = save_uploaded_file(host_image)
                    if host_path:
                        img = Image.open(host_path)

                        # Nascondi messaggio
                        with st.spinner("Nascondendo messaggio..."):
                            result_img, metrics = hide_message(img, message, method=selected_method)

                        st.success("✅ Messaggio nascosto con successo!")

                        # Salva il risultato per il download
                        img_buffer = io.BytesIO()
                        result_img.save(img_buffer, format="PNG")

                        # Salva in session_state per evitare reload (include anteprima e metriche)
                        st.session_state["hide_string_result"] = {
                            "data": img_buffer.getvalue(),
                            "filename": output_name,
                            "preview_image": result_img,  # Mantieni l'anteprima
                            "metrics": metrics,  # Salva le metriche
                        }

                        # Cleanup
                        cleanup_temp_file(output_name)
                    else:
                        st.error("❌ Errore nel salvare l'immagine")

                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
            else:
                st.warning("⚠️ Carica un'immagine e inserisci un messaggio!")

        # Sezione download se ci sono risultati
        if "hide_string_result" in st.session_state:
            st.markdown("---")
            st.subheader("📥 Download Risultati")

            result_data = st.session_state["hide_string_result"]

            # Mostra metriche se disponibili
            if "metrics" in result_data:

                metrics = result_data["metrics"]
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        label="SSIM (Similarità Strutturale)",
                        value=f"{metrics['ssim']:.4f}",
                        help="1.0 = immagini identiche",
                    )
                with col2:
                    st.metric(
                        label="PSNR (Rapporto Segnale/Rumore)",
                        value=f"{metrics['psnr']:.2f} dB",
                        help="Valori più alti = migliore qualità",
                    )

            # Mostra sempre l'anteprima dell'immagine risultato
            if "preview_image" in result_data:
                st.image(
                    result_data["preview_image"],
                    caption="Anteprima immagine con messaggio nascosto",
                    width=400,
                )

            create_download_button(
                result_data["data"],
                result_data["filename"],
                "image/png",
                "📥 Scarica immagine con messaggio nascosto",
            )

    @staticmethod
    def hide_image_page(selected_method):
        """Pagina per nascondere immagini"""
        from src.steganografia import hide_image

        st.subheader("🖼️ Nascondere Immagine")
        st.info("💡 L'immagine host deve essere più grande di quella da nascondere")

        # Upload dell'immagine host
        host_image = st.file_uploader(
            "🖼️ Carica l'immagine host:",
            type=["png", "jpg", "jpeg"],
            key="hide_image_host_image",
        )

        # Mostra anteprima dell'immagine host
        if host_image:
            ImageDisplay.show_resized_image(host_image, "🖼️ Immagine Host", max_width=300)
            ImageDisplay.show_image_details(host_image, "Dettagli Immagine Host")

        secret_image = st.file_uploader(
            "🔒 Carica l'immagine da nascondere",
            type=["png", "jpg", "jpeg"],
            key="secret_image",
        )

        # Mostra anteprima dell'immagine da nascondere
        if secret_image:
            ImageDisplay.show_resized_image(
                secret_image, "🔒 Immagine da Nascondere", max_width=300
            )
            ImageDisplay.show_image_details(secret_image, "Dettagli Immagine da Nascondere")

        # Controllo compatibilità dimensioni
        if host_image and secret_image:
            host_info = ImageDisplay.get_image_info(host_image)
            secret_info = ImageDisplay.get_image_info(secret_image)

            if host_info and secret_info:
                host_pixels = host_info["size_pixels"]
                secret_pixels = secret_info["size_pixels"]

                if host_pixels < secret_pixels:
                    st.error(
                        f"❌ **Incompatibilità dimensioni**: L'immagine host ({host_pixels:,} pixel) è più piccola dell'immagine da nascondere ({secret_pixels:,} pixel)"
                    )
                    st.info(
                        "💡 L'immagine host deve avere almeno la stessa quantità di pixel dell'immagine da nascondere"
                    )
                elif host_pixels < secret_pixels * 2:
                    st.warning(
                        f"⚠️ **Attenzione**: L'immagine host ({host_pixels:,} pixel) è solo {host_pixels / secret_pixels:.1f}x più grande dell'immagine da nascondere ({secret_pixels:,} pixel)"
                    )
                    st.info("💡 Per migliori risultati, usa un'immagine host almeno 2x più grande")
                else:
                    st.success(
                        f"✅ **Dimensioni compatibili**: L'immagine host ({host_pixels:,} pixel) è {host_pixels / secret_pixels:.1f}x più grande dell'immagine da nascondere ({secret_pixels:,} pixel)"
                    )

        # Parametri
        st.subheader("⚙️ Parametri")

        # Configurazione DWT se selezionato
        if selected_method == SteganographyMethod.DWT:
            # Preconfigurazioni
            preset = st.selectbox(
                "📋 Preconfigurazione:",
                options=[
                    "⚖️ Bilanciato (consigliato)",
                    "🎨 Massima Qualità",
                    "📦 Massima Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                help="Bilanciato: ottimo compromesso qualità/capacità. Qualità: minima distorsione. Capacità: massimo payload.",
            )

            # Importa le costanti DWT
            from src.steganografia.dwt.image_operations import ImageSteganography as DWT

            # Applica preset
            if preset == "⚖️ Bilanciato (consigliato)":
                default_step = 12.0
                default_bits = 3
                default_bands = ["cH", "cV"]
                default_level = 1
                st.info(
                    "⚖️ STEP=12, 3-bit MSB, 2 bande (cH+cV), level 1 - Ottimo compromesso capacità/qualità"
                )
            elif preset == "🎨 Massima Qualità":
                default_step = 24.0
                default_bits = 4
                default_bands = ["cH"]
                default_level = 1
                st.info(
                    "🎨 STEP=24, 4-bit MSB, banda cH, level 1 - Minima distorsione, capacità ridotta"
                )
            elif preset == "📦 Massima Capacità":
                default_step = 8.0
                default_bits = 2
                default_bands = ["cH", "cV", "cD"]
                default_level = 1
                st.info(
                    "📦 STEP=8, 2-bit MSB, 3 bande (tutte), level 1 - Capacità massima, qualità ridotta"
                )
            else:  # Personalizzato
                default_step = DWT.STEP
                default_bits = DWT.BITS_SECRET
                default_bands = DWT.BANDS
                default_level = DWT.LEVEL

            # Parametri personalizzabili (se preset personalizzato)
            if preset == "⚙️ Personalizzato":
                col1, col2 = st.columns(2)
                with col1:
                    step_value = st.slider(
                        "STEP (Quantizzazione QIM)",
                        min_value=8.0,
                        max_value=32.0,
                        value=default_step,
                        step=4.0,
                        help="8=alta capacità, 16=bilanciato, 32=massima qualità",
                        key="dwt_step_slider",
                    )
                    bits_secret = st.slider(
                        "Bit per Pixel (Secret)",
                        min_value=2,
                        max_value=4,
                        value=default_bits,
                        help="2=massima capacità, 4=massima qualità (4 MSB)",
                        key="dwt_bits_slider",
                    )
                with col2:
                    level_value = st.selectbox(
                        "Livello DWT",
                        options=[1, 2],
                        index=0 if default_level == 1 else 1,
                        help="1=veloce standard, 2=più robusto ma meno capacità",
                        key="dwt_level_select",
                    )
                    bands_selection = st.multiselect(
                        "Bande DWT",
                        options=["cH", "cV", "cD"],
                        default=default_bands,
                        help="cH=orizzontale, cV=verticale, cD=diagonale. Più bande = più capacità ma più distorsione",
                        key="dwt_bands_multi",
                    )
                    if not bands_selection:
                        st.error("⚠️ Seleziona almeno una banda!")
                        bands_selection = ["cH"]
            else:
                # Usa valori del preset
                step_value = default_step
                bits_secret = default_bits
                bands_selection = default_bands
                level_value = default_level

            # Applica configurazione a DWT
            DWT.STEP = step_value
            DWT.BITS_SECRET = bits_secret
            DWT.BANDS = bands_selection
            DWT.LEVEL = level_value

            # Calcola capacità DWT teorica (si aggiorna dinamicamente con i parametri)
            if host_image and secret_image:
                host_info = ImageDisplay.get_image_info(host_image)
                secret_info = ImageDisplay.get_image_info(secret_image)
                if host_info and secret_info:
                    # Capacità DWT: usa TUTTI i coefficienti (filtro epsilon, non STEP)
                    # Formula: (W*H/4) * len(bands) coefficienti per livello DWT 1
                    host_w, host_h = host_info["width"], host_info["height"]

                    # Con epsilon filter, praticamente TUTTI i coefficienti sono utilizzabili (~99%)
                    dwt_capacity_bits = int((host_w * host_h / 4) * len(bands_selection) * 0.99)
                    secret_w, secret_h = secret_info["width"], secret_info["height"]
                    secret_bits_needed = secret_w * secret_h * 3 * bits_secret

                    if secret_bits_needed > dwt_capacity_bits:
                        st.error(
                            f"❌ **Capacità insufficiente**: L'immagine segreta richiede {secret_bits_needed:,} bit, "
                            f"ma la capacità DWT è ~{dwt_capacity_bits:,} bit. "
                            f"Riduci dimensione secret, bits/pixel o usa più bande."
                        )
                    else:
                        usage_pct = (secret_bits_needed / dwt_capacity_bits) * 100
                        st.success(
                            f"✅ **Capacità DWT sufficiente**: {secret_bits_needed:,} / ~{dwt_capacity_bits:,} bit ({usage_pct:.1f}% utilizzato)"
                        )
                        st.info(
                            f"ℹ️ {len(bands_selection)} banda/e × {host_w}×{host_h}/4 coefficienti = ~{dwt_capacity_bits:,} bit"
                        )

            # Non mostrare LSB/MSB/DIV per DWT
            lsb = 0
            msb = 8
            div = 0.0

        # Mostra LSB/MSB/DIV solo per il metodo LSB
        elif selected_method == SteganographyMethod.LSB:
            # Preconfigurazioni LSB
            preset = st.selectbox(
                "📋 Preconfigurazione:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Alta Qualità",
                    "📦 Alta Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                help="Bilanciato: LSB=4 MSB=4. Alta Qualità: LSB=1 MSB=8. Alta Capacità: LSB=6 MSB=2. DIV sempre automatico.",
                key="lsb_img_preset",
            )
            
            if preset == "⚖️ Bilanciato":
                lsb = 4
                msb = 4
                div = 0.0
                st.info("⚖️ LSB=4, MSB=4, DIV=auto - Buon compromesso qualità/capacità")
            elif preset == "🎨 Alta Qualità":
                lsb = 1
                msb = 8
                div = 0.0
                st.info("🎨 LSB=1, MSB=8, DIV=auto - Massima qualità visiva")
            elif preset == "📦 Alta Capacità":
                lsb = 6
                msb = 2
                div = 0.0
                st.info("📦 LSB=6, MSB=2, DIV=auto - Massima capacità dati")
            else:  # Personalizzato
                st.markdown("**Parametri Personalizzati:**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    lsb = st.number_input(
                        "LSB (bit da modificare)",
                        min_value=1,
                        max_value=8,
                        value=4,
                        key="lsb_img_lsb",
                    )
                with col2:
                    msb = st.number_input(
                        "MSB (bit da nascondere)",
                        min_value=1,
                        max_value=8,
                        value=4,
                        key="lsb_img_msb",
                    )
                with col3:
                    div = st.number_input(
                        "Divisore",
                        min_value=0.0,
                        value=0.0,
                        help="0.0 = automatico",
                        key="lsb_img_div",
                    )

        elif selected_method == SteganographyMethod.PVD:
            # Configurazione PVD
            from src.steganografia.pvd.image_operations import ImageSteganography as PVD

            preset = st.selectbox(
                "📋 Preconfigurazione:",
                options=[
                    "🎨 Qualità (consigliato)",
                    "📦 Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                help="Qualità: PSNR >40dB, capacità media. Capacità: PSNR ~35-38dB, capacità massima.",
            )

            if preset == "🎨 Qualità (consigliato)":
                PVD.configure_quality_mode()
                st.info("🎨 Ranges ridotti, step=2, canali R+G - Qualità ottimale")
                lsb = msb = div = 0
            elif preset == "📦 Capacità":
                PVD.configure_capacity_mode()
                st.info("📦 Ranges estesi, step=1, tutti i canali - Capacità massima")
                lsb = msb = div = 0
            else:  # Personalizzato
                st.markdown("**Parametri Personalizzati:**")

                col1, col2 = st.columns(2)
                with col1:
                    use_quality_ranges = st.checkbox(
                        "Usa ranges qualità",
                        value=True,
                        help="Ranges ridotti (2-4 bit) vs estesi (3-7 bit)",
                    )
                    pair_step = st.slider(
                        "Sparsità coppie",
                        min_value=1,
                        max_value=4,
                        value=1,
                        help="1=denso, 2=medio, 4=sparso",
                    )

                with col2:
                    channels_options = st.multiselect(
                        "Canali RGB",
                        options=["R (0)", "G (1)", "B (2)"],
                        default=["R (0)", "G (1)", "B (2)"],
                        help="Seleziona quali canali usare per embedding",
                    )
                    channels = [int(ch.split("(")[1][0]) for ch in channels_options]

                # Applica configurazione custom
                PVD.configure_custom(
                    pair_step=pair_step,
                    channels=channels if channels else [0, 1, 2],
                    use_quality_ranges=use_quality_ranges,
                )

                lsb = msb = div = 0

        else:
            # Metodi senza parametri (fallback)
            lsb = 0
            msb = 8
            div = 0.0
            method_name = SteganographyMethod.get_display_names().get(selected_method, "Unknown")
            st.info(f"ℹ️ Il metodo {method_name} non richiede parametri aggiuntivi")

        col1, col2 = st.columns(2)
        with col1:
            output_name = st.text_input(
                "Nome file output",
                value="image_with_hidden_image.png",
                key="img_output",
            )
        with col2:
            save_backup = st.checkbox("Salva parametri su file", key="img_backup_save")
            backup_name = ""
            if save_backup:
                backup_name = st.text_input(
                    "Nome file backup", value="image_backup.dat", key="img_backup_name"
                )

        if st.button("🔒 Nascondi Immagine", type="primary"):
            if host_image and secret_image:
                # Pulisci risultati precedenti
                if "hide_image_results" in st.session_state:
                    del st.session_state["hide_image_results"]
                try:
                    # Salva immagini temporaneamente
                    host_path = save_uploaded_file(host_image)
                    secret_path = save_uploaded_file(secret_image)

                    if host_path and secret_path:
                        img1 = Image.open(host_path)
                        img2 = Image.open(secret_path)

                        # Nascondi immagine
                        backup_file = backup_name if save_backup else None
                        with st.spinner("Nascondendo immagine..."):
                            result = hide_image(
                                img1,
                                img2,
                                lsb,
                                msb,
                                int(div),
                                backup_file,
                                method=selected_method,
                            )

                        if result:  # Controllo successo
                            (
                                result_img,
                                final_lsb,
                                final_msb,
                                final_div,
                                _,
                                _,
                                metrics,
                            ) = result
                            st.success("✅ Immagine nascosta con successo!")

                            # Salva risultati per il download
                            img_buffer = io.BytesIO()
                            result_img.save(img_buffer, format="PNG")

                            downloads = {
                                "image": {
                                    "data": img_buffer.getvalue(),
                                    "filename": output_name,
                                    "mime": "image/png",
                                    "label": "📥 Scarica immagine con immagine nascosta",
                                },
                                "preview_image": result_img,  # Mantieni anteprima
                                "preview_info": f"📊 Parametri utilizzati: LSB={final_lsb}, MSB={final_msb}, DIV={final_div:.2f}",
                                "metrics": metrics,  # Salva le metriche
                            }

                            # Aggiungi backup se richiesto
                            if backup_file and os.path.exists(backup_file):
                                with open(backup_file, "rb") as f:
                                    downloads["backup"] = {
                                        "data": f.read(),
                                        "filename": backup_file,
                                        "mime": "application/octet-stream",
                                        "label": "💾 Scarica file backup parametri",
                                    }
                                cleanup_temp_file(backup_file)

                            st.session_state["hide_image_results"] = downloads

                            # Cleanup
                            cleanup_temp_file(output_name)
                        else:
                            st.error("❌ Errore durante l'occultamento dell'immagine")
                    else:
                        st.error("❌ Errore nel salvare le immagini")

                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
            else:
                st.warning("⚠️ Carica entrambe le immagini!")

        # Sezione download se ci sono risultati
        if "hide_image_results" in st.session_state:
            st.markdown("---")
            st.subheader("📥 Download Risultati")

            downloads = st.session_state["hide_image_results"]

            # Mostra sempre l'anteprima e info
            if "preview_image" in downloads:
                if "preview_info" in downloads:
                    st.info(downloads["preview_info"])
                # Mostra metriche se disponibili
                if "metrics" in downloads:
                    metrics = downloads["metrics"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            label="SSIM (Similarità Strutturale)",
                            value=f"{metrics['ssim']:.4f}",
                            help="1.0 = immagini identiche",
                        )
                    with col2:
                        st.metric(
                            label="PSNR (Rapporto Segnale/Rumore)",
                            value=f"{metrics['psnr']:.2f} dB",
                            help="Valori più alti = migliore qualità",
                        )
                st.image(
                    downloads["preview_image"],
                    caption="Anteprima immagine con immagine nascosta",
                    width=400,
                )

            # Download immagine
            if "image" in downloads:
                img_data = downloads["image"]
                create_download_button(
                    img_data["data"],
                    img_data["filename"],
                    img_data["mime"],
                    img_data["label"],
                )

            # Download backup se presente
            if "backup" in downloads:
                backup_data = downloads["backup"]
                create_download_button(
                    backup_data["data"],
                    backup_data["filename"],
                    backup_data["mime"],
                    backup_data["label"],
                )

    @staticmethod
    def hide_binary_page(selected_method):
        """Pagina per nascondere file binari"""
        from src.steganografia import hide_bin_file

        st.subheader("📁 Nascondere File Binario")
        st.info("💡 La compressione riduce la dimensione del file da nascondere")

        # Upload dell'immagine host
        host_image = st.file_uploader(
            "🖼️ Carica l'immagine host:",
            type=["png", "jpg", "jpeg"],
            key="hide_binary_host_image",
        )

        # Mostra anteprima dell'immagine host
        if host_image:
            ImageDisplay.show_resized_image(host_image, "🖼️ Immagine Host", max_width=400)
            ImageDisplay.show_image_details(host_image, "Dettagli Immagine Host")

        secret_file = st.file_uploader("Carica il file da nascondere", key="secret_file")

        if secret_file:
            st.write(f"**Nome file:** {secret_file.name}")
            st.write(f"**Dimensione:** {len(secret_file.getvalue())} bytes")
            if hasattr(secret_file, "type"):
                st.write(f"**Tipo:** {secret_file.type}")

        # Parametri
        st.subheader("⚙️ Parametri")

        col1, col2, col3 = st.columns(3)

        with col1:
            zip_mode = st.selectbox(
                "Modalità compressione",
                [CompressionMode.NO_ZIP, CompressionMode.FILE, CompressionMode.DIR],
                format_func=lambda x: {
                    CompressionMode.NO_ZIP: "Nessuna",
                    CompressionMode.FILE: "Comprimi file",
                    CompressionMode.DIR: "Comprimi directory",
                }.get(
                    x, "Nessuna"
                ),  # Usa .get() con default per evitare errori
            )

        # Configurazione DWT per file binari
        if selected_method == SteganographyMethod.DWT:
            from src.steganografia.dwt.binary_operations import (
                BinarySteganography as DWT_Binary,
            )

            # Preset selector
            dwt_preset = st.selectbox(
                "Seleziona configurazione",
                options=[
                    "Bilanciato",
                    "Massima Capacità",
                    "Massima Qualità",
                    "Personalizzato",
                ],
                index=0,
                help="Bilanciato: buon compromesso capacità/qualità. Massima Capacità: usa tutte le bande e canali. Massima Qualità: minimal embedding.",
                key="dwt_binary_preset",
            )

            # Imposta valori di default basati sul preset
            if dwt_preset == "Bilanciato":
                default_alpha = 0.1
                default_bands = ["cH"]
                default_multi_channel = False
            elif dwt_preset == "Massima Capacità":
                default_alpha = 0.15
                default_bands = ["cH", "cV", "cD"]
                default_multi_channel = True
            elif dwt_preset == "Massima Qualità":
                default_alpha = 0.05
                default_bands = ["cH"]
                default_multi_channel = False
            else:  # Personalizzato
                default_alpha = 0.1
                default_bands = ["cH"]
                default_multi_channel = False

            # Mostra controlli solo in modalità Personalizzato
            if dwt_preset == "Personalizzato":
                col1, col2 = st.columns(2)
                with col1:
                    alpha_value = st.slider(
                        "ALPHA (forza embedding)",
                        min_value=0.05,
                        max_value=0.3,
                        value=default_alpha,
                        step=0.05,
                        help="Più alto = più robusto ma più visibile. 0.1 = standard",
                        key="dwt_binary_alpha_slider",
                    )
                    multi_channel = st.checkbox(
                        "Usa tutti i canali RGB",
                        value=default_multi_channel,
                        help="Se attivo usa tutti e 3 i canali (3x capacità), altrimenti solo canale R",
                        key="dwt_binary_multi_channel",
                    )
                with col2:
                    bands_selection = st.multiselect(
                        "Bande DWT",
                        options=["cH", "cV", "cD"],
                        default=default_bands,
                        help="cH=orizzontale, cV=verticale, cD=diagonale. Più bande = più capacità",
                        key="dwt_binary_bands_multi",
                    )
                    if not bands_selection:
                        st.error("⚠️ Seleziona almeno una banda!")
                        bands_selection = ["cH"]
            else:
                # Usa valori del preset
                alpha_value = default_alpha
                bands_selection = default_bands
                multi_channel = default_multi_channel

            # Applica configurazione a DWT Binary
            DWT_Binary.ALPHA = alpha_value
            DWT_Binary.BANDS = bands_selection
            DWT_Binary.USE_ALL_CHANNELS = multi_channel
            DWT_Binary.CHANNEL = 0  # Sempre canale R quando multi_channel=False

            # Calcola capacità DWT per binary
            if host_image and secret_file:
                host_info = ImageDisplay.get_image_info(host_image)
                if host_info:
                    host_w, host_h = host_info["width"], host_info["height"]
                    file_size = len(secret_file.getvalue())

                    # Calcolo capacità: coefficienti per banda × numero bande × numero canali
                    coeffs_per_band = (host_w * host_h) // 4  # DWT livello 1
                    num_bands = len(bands_selection)
                    num_channels = 3 if multi_channel else 1

                    # Header overhead: magic(16) + size(32) + terminator(16) = 64 bit
                    overhead_bits = 64
                    capacity_bits = (coeffs_per_band * num_bands * num_channels) - overhead_bits
                    file_bits_needed = file_size * 8

                    if file_bits_needed > capacity_bits:
                        st.error(
                            f"❌ **Capacità insufficiente**: Il file richiede {file_bits_needed:,} bit, "
                            f"ma la capacità DWT è ~{capacity_bits:,} bit. "
                            f"Usa più bande/canali o comprimi il file."
                        )
                    else:
                        usage_pct = (file_bits_needed / capacity_bits) * 100
                        st.success(
                            f"✅ **Capacità DWT sufficiente**: {file_bits_needed:,} / ~{capacity_bits:,} bit ({usage_pct:.1f}% utilizzato)"
                        )
                        st.info(
                            f"ℹ️ {num_channels} canale/i × {num_bands} banda/e × {coeffs_per_band:,} coeff = ~{capacity_bits:,} bit"
                        )

            n = 0
            div = 0.0

        # Mostra N e DIV solo per LSB
        elif selected_method == SteganographyMethod.LSB:
            # Preconfigurazioni LSB
            preset = st.selectbox(
                "📋 Preconfigurazione:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Alta Qualità",
                    "📦 Alta Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                help="Bilanciato: N=4. Alta Qualità: N=1. Alta Capacità: N=6. DIV sempre automatico.",
                key="lsb_bin_preset",
            )
            
            if preset == "⚖️ Bilanciato":
                n = 4
                div = 0.0
                st.info("⚖️ N=4, DIV=auto - Buon compromesso qualità/capacità")
            elif preset == "🎨 Alta Qualità":
                n = 1
                div = 0.0
                st.info("🎨 N=1, DIV=auto - Massima qualità visiva")
            elif preset == "📦 Alta Capacità":
                n = 6
                div = 0.0
                st.info("📦 N=6, DIV=auto - Massima capacità dati")
            else:  # Personalizzato
                st.markdown("**Parametri Personalizzati:**")
                with col2:
                    n = st.number_input(
                        "N (bit da modificare)",
                        min_value=1,
                        max_value=8,
                        value=4,
                        key="lsb_bin_n",
                    )
                with col3:
                    div = st.number_input(
                        "Divisore",
                        min_value=0.0,
                        value=0.0,
                        key="lsb_bin_div",
                        help="0.0 = automatico",
                    )

        elif selected_method == SteganographyMethod.PVD:
            # Configurazione PVD per binary
            from src.steganografia.pvd.binary_operations import (
                BinarySteganography as PVD_Binary,
            )

            preset = st.selectbox(
                "📋 Preconfigurazione PVD:",
                options=[
                    "🎨 Qualità",
                    "📦 Capacità (consigliato)",
                    "⚙️ Personalizzato",
                ],
                index=1,  # Default: Capacità per file binari
                key="pvd_binary_preset",
            )

            if preset == "🎨 Qualità":
                PVD_Binary.RANGES = PVD_Binary.RANGES_QUALITY
                PVD_Binary.PAIR_STEP = 2
                PVD_Binary.CHANNELS = [0, 1]
                st.info("✅ Qualità ottimale (capacità ridotta)")
            elif preset == "📦 Capacità (consigliato)":
                PVD_Binary.RANGES = PVD_Binary.RANGES_CAPACITY
                PVD_Binary.PAIR_STEP = 1
                PVD_Binary.CHANNELS = [0, 1, 2]
                st.info("📦 Capacità massima (per file binari)")
            else:  # Personalizzato
                col_a, col_b = st.columns(2)
                with col_a:
                    use_quality = st.checkbox(
                        "Usa ranges qualità", value=False, key="pvd_bin_quality"
                    )
                    pair_step_bin = st.slider("Sparsità", 1, 4, 1, key="pvd_bin_step")
                with col_b:
                    channels_bin = st.multiselect(
                        "Canali",
                        ["R (0)", "G (1)", "B (2)"],
                        default=["R (0)", "G (1)", "B (2)"],
                        key="pvd_bin_channels",
                    )
                    channels_list = (
                        [int(ch.split("(")[1][0]) for ch in channels_bin]
                        if channels_bin
                        else [0, 1, 2]
                    )

                PVD_Binary.RANGES = (
                    PVD_Binary.RANGES_QUALITY if use_quality else PVD_Binary.RANGES_CAPACITY
                )
                PVD_Binary.PAIR_STEP = pair_step_bin
                PVD_Binary.CHANNELS = channels_list

            n = 0
            div = 0.0

        else:
            # Metodi senza parametri
            n = 0
            div = 0.0
            method_name = SteganographyMethod.get_display_names().get(selected_method, "Unknown")
            with col2:
                st.info(f"ℹ️ Il metodo {method_name} non richiede parametri")
            with col3:
                st.write("")

        col1, col2 = st.columns(2)
        with col1:
            output_name = st.text_input(
                "Nome file output", value="image_with_file.png", key="bin_output"
            )
        with col2:
            save_backup = st.checkbox("Salva parametri su file", key="bin_backup_save")
            backup_name = ""
            if save_backup:
                backup_name = st.text_input(
                    "Nome file backup", value="binary_backup.dat", key="bin_backup_name"
                )

        if st.button("🔒 Nascondi File", type="primary"):
            if host_image and secret_file:
                # Pulisci risultati precedenti
                if "hide_binary_results" in st.session_state:
                    del st.session_state["hide_binary_results"]
                try:
                    # Salva file temporaneamente
                    host_path = save_uploaded_file(host_image)
                    secret_path = save_uploaded_file(secret_file)

                    if host_path and secret_path:
                        img = Image.open(host_path)

                        # Nascondi file
                        backup_file = backup_name if save_backup else None
                        with st.spinner("Nascondendo file..."):
                            result = hide_bin_file(
                                img,
                                secret_path,
                                zip_mode,
                                n,
                                int(div),
                                backup_file,
                                method=selected_method,
                            )

                        if result:  # Controllo successo
                            result_img, final_n, final_div, size, metrics = result
                            st.success("✅ File nascosto con successo!")

                            # Salva risultati per il download
                            img_buffer = io.BytesIO()
                            result_img.save(img_buffer, format="PNG")

                            downloads = {
                                "image": {
                                    "data": img_buffer.getvalue(),
                                    "filename": output_name,
                                    "mime": "image/png",
                                    "label": "📥 Scarica immagine con file nascosto",
                                },
                                "preview_image": result_img,  # Mantieni anteprima
                                "preview_info": f"📊 Parametri utilizzati: N={final_n}, DIV={final_div:.2f}, SIZE={size} bytes",
                                "metrics": metrics,  # Salva le metriche
                            }

                            # Aggiungi backup se richiesto
                            if backup_file and os.path.exists(backup_file):
                                with open(backup_file, "rb") as f:
                                    downloads["backup"] = {
                                        "data": f.read(),
                                        "filename": backup_file,
                                        "mime": "application/octet-stream",
                                        "label": "💾 Scarica file backup parametri",
                                    }
                                cleanup_temp_file(backup_file)

                            st.session_state["hide_binary_results"] = downloads

                            # Cleanup
                            cleanup_temp_file(output_name)
                        else:
                            st.error("❌ Errore durante l'occultamento del file")
                    else:
                        st.error("❌ Errore nel salvare i file")

                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
            else:
                st.warning("⚠️ Carica un'immagine e un file!")

        # Sezione download se ci sono risultati
        if "hide_binary_results" in st.session_state:
            st.markdown("---")
            st.subheader("📥 Download Risultati")

            downloads = st.session_state["hide_binary_results"]

            # Mostra sempre l'anteprima e info
            if "preview_image" in downloads:
                if "preview_info" in downloads:
                    st.info(downloads["preview_info"])
                # Mostra metriche se disponibili
                if "metrics" in downloads:
                    metrics = downloads["metrics"]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            label="SSIM (Similarità Strutturale)",
                            value=f"{metrics['ssim']:.4f}",
                            help="1.0 = immagini identiche",
                        )
                    with col2:
                        st.metric(
                            label="PSNR (Rapporto Segnale/Rumore)",
                            value=f"{metrics['psnr']:.2f} dB",
                            help="Valori più alti = migliore qualità",
                        )
                st.image(
                    downloads["preview_image"],
                    caption="Anteprima immagine con file nascosto",
                    width=400,
                )

            # Download immagine
            if "image" in downloads:
                img_data = downloads["image"]
                create_download_button(
                    img_data["data"],
                    img_data["filename"],
                    img_data["mime"],
                    img_data["label"],
                )

            # Download backup se presente
            if "backup" in downloads:
                backup_data = downloads["backup"]
                create_download_button(
                    backup_data["data"],
                    backup_data["filename"],
                    backup_data["mime"],
                    backup_data["label"],
                )
