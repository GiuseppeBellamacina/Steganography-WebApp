"""
Pagine per recuperare dati dall'interfaccia Streamlit
"""

import io
import os

import streamlit as st
from PIL import Image

from config.constants import CompressionMode, SteganographyMethod

from .components import (
    cleanup_temp_file,
    create_download_button,
    display_backup_options,
    save_uploaded_file,
)
from .image_utils import ImageDisplay


class RecoverDataPages:
    """Gestisce le pagine per recuperare dati"""

    @staticmethod
    def recover_string_page(selected_method):
        """Pagina per recuperare stringhe"""
        from src.steganografia import get_message

        st.subheader("📝 Recuperare Stringa")

        # Upload dell'immagine con dati nascosti
        hidden_image = st.file_uploader(
            "🖼️ Carica l'immagine con messaggio nascosto:",
            type=["png", "jpg", "jpeg"],
            key="recover_string_hidden_image",
        )

        # Mostra anteprima dell'immagine
        if hidden_image:
            ImageDisplay.show_resized_image(
                hidden_image, "🔒 Immagine con Messaggio", max_width=400
            )

        # Configurazione metodo
        if selected_method == SteganographyMethod.PVD:
            st.info(
                "💡 Se non hai il backup, configura i parametri usati durante l'occultamento"
            )

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
                key="pvd_msg_recover_preset",
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
                        "Usa ranges qualità", value=True, key="pvd_msg_rec_quality"
                    )
                    pair_step_msg = st.slider(
                        "Sparsità", 1, 4, 1, key="pvd_msg_rec_step"
                    )
                with col2:
                    channels_msg = st.multiselect(
                        "Canali",
                        ["R (0)", "G (1)", "B (2)"],
                        default=["R (0)", "G (1)", "B (2)"],
                        key="pvd_msg_rec_channels",
                    )
                    channels_list = (
                        [int(ch.split("(")[1][0]) for ch in channels_msg]
                        if channels_msg
                        else [0, 1, 2]
                    )

                PVD_Msg.RANGES = (
                    PVD_Msg.RANGES_QUALITY if use_quality else PVD_Msg.RANGES_CAPACITY
                )
                PVD_Msg.PAIR_STEP = pair_step_msg
                PVD_Msg.CHANNELS = channels_list

        # Configurazione metodo DWT
        elif selected_method == SteganographyMethod.DWT:
            st.info(
                "💡 Se non hai il backup, configura i parametri usati durante l'occultamento"
            )

            from src.steganografia.dwt.message_operations import (
                MessageSteganography as DWT_Msg,
            )

            preset = st.selectbox(
                "📋 Preconfigurazione DWT:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Qualità",
                    "💪 Robustezza",
                    "📦 Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="dwt_msg_recover_preset",
                help="Usa la stessa configurazione dell'occultamento!",
            )

            if preset == "⚖️ Bilanciato":
                DWT_Msg.WAVELET = "haar"
                DWT_Msg.ALPHA = 0.1
                DWT_Msg.BANDS = ["cH"]

                DWT_Msg.USE_ALL_CHANNELS = True
                st.info("⚖️ Wavelet Haar, alpha 0.1, banda cH, tutti i canali")
            elif preset == "🎨 Qualità":
                DWT_Msg.WAVELET = "haar"
                DWT_Msg.ALPHA = 0.05
                DWT_Msg.BANDS = ["cH"]
                DWT_Msg.USE_ALL_CHANNELS = True
                st.info("🎨 Wavelet Haar, alpha 0.05, banda cH, tutti i canali")
            elif preset == "💪 Robustezza":
                DWT_Msg.WAVELET = "db4"
                DWT_Msg.ALPHA = 0.3
                DWT_Msg.BANDS = ["cH", "cV"]
                DWT_Msg.USE_ALL_CHANNELS = True
                st.info("💪 Wavelet Daubechies 4, alpha 0.3, 2 bande, tutti i canali")
            elif preset == "📦 Capacità":
                DWT_Msg.WAVELET = "haar"
                DWT_Msg.ALPHA = 0.15
                DWT_Msg.BANDS = ["cH", "cV", "cD"]
                DWT_Msg.USE_ALL_CHANNELS = True
                st.info("📦 Alpha 0.15, 3 bande (tutte), tutti i canali")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    wavelet = st.selectbox(
                        "Tipo Wavelet",
                        options=["haar", "db2", "db4", "db8", "sym2", "sym4", "coif1"],
                        index=0,
                        key="dwt_msg_recover_wavelet",
                    )
                    alpha = st.slider(
                        "Alpha (forza embedding)",
                        min_value=0.05,
                        max_value=0.5,
                        value=0.1,
                        step=0.05,
                        key="dwt_msg_recover_alpha",
                    )
                with col2:
                    bands_selection = st.multiselect(
                        "Bande DWT",
                        options=["cH", "cV", "cD"],
                        default=["cH"],
                        key="dwt_msg_recover_bands",
                    )
                    if not bands_selection:
                        st.error("⚠️ Seleziona almeno una banda!")
                        bands_selection = ["cH"]
                    use_all_channels = st.checkbox(
                        "Usa tutti i canali RGB",
                        value=True,
                        help="Deve corrispondere all'impostazione usata durante l'hide!",
                        key="dwt_msg_recover_all_channels",
                    )

                DWT_Msg.WAVELET = wavelet
                DWT_Msg.ALPHA = alpha
                DWT_Msg.BANDS = bands_selection
                DWT_Msg.USE_ALL_CHANNELS = use_all_channels
                DWT_Msg.CHANNEL = 0  # Sempre R quando single-channel

        # Per le stringhe LSB non servono parametri particolari
        elif selected_method == SteganographyMethod.LSB:
            st.info(
                "💡 Le stringhe LSB non richiedono parametri speciali - il recupero è automatico!"
            )

        if st.button("🔓 Recupera Messaggio", type="primary"):
            if hidden_image:
                # Pulisci risultati precedenti
                if "recover_string_result" in st.session_state:
                    del st.session_state["recover_string_result"]
                try:
                    # Salva immagine temporaneamente
                    hidden_path = save_uploaded_file(hidden_image)
                    if hidden_path:
                        img = Image.open(hidden_path)

                        # Recupera messaggio
                        with st.spinner("Recuperando messaggio..."):
                            message = get_message(img, method=selected_method)

                        if message and message.strip():
                            st.success("✅ Messaggio recuperato!")

                            # Mostra informazioni sul messaggio

                            # Salva il messaggio per il download
                            st.session_state["recover_string_result"] = {
                                "data": message.encode("utf-8"),
                                "filename": "messaggio_recuperato.txt",
                                "message_text": message,  # Mantieni il testo per l'anteprima
                                "message_length": len(message.encode("utf-8")),
                            }
                        else:
                            st.error("❌ Nessun messaggio valido trovato nell'immagine")
                            st.info("💡 Possibili cause:")
                            st.write("• L'immagine non contiene un messaggio nascosto")
                            st.write("• L'immagine è stata modificata o compressa")
                            st.write("• Il messaggio è corrotto o non leggibile")
                    else:
                        st.error("❌ Errore nel salvare l'immagine")

                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
            else:
                st.warning("⚠️ Carica un'immagine!")

        # Sezione download se ci sono risultati
        if "recover_string_result" in st.session_state:
            st.markdown("---")
            st.subheader("📥 Download Risultati")

            result_data = st.session_state["recover_string_result"]

            # Mostra sempre il messaggio recuperato
            if "message_text" in result_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Caratteri", len(result_data["message_text"]))
                with col2:
                    st.metric(
                        "Dimensione in byte", f"{result_data['message_length']} byte"
                    )

                st.text_area(
                    "Messaggio nascosto:", value=result_data["message_text"], height=100
                )

            create_download_button(
                result_data["data"],
                result_data["filename"],
                "text/plain",
                "📥 Scarica messaggio come file di testo",
            )

    @staticmethod
    def recover_image_page(selected_method):
        """Pagina per recuperare immagini"""
        from src.steganografia import get_image

        st.subheader("🖼️ Recuperare Immagine")

        # Upload dell'immagine con dati nascosti
        hidden_image = st.file_uploader(
            "🖼️ Carica l'immagine con immagine nascosta:",
            type=["png", "jpg", "jpeg"],
            key="recover_image_hidden_image",
        )

        # Mostra anteprima dell'immagine
        if hidden_image:
            ImageDisplay.show_resized_image(
                hidden_image, "🔒 Immagine con Dati Nascosti", max_width=400
            )

        # Opzioni parametri
        backup_file_path, use_recent, manual_params = display_backup_options(
            "image_get", show_manual=True
        )

        # Inizializza tutte le variabili a None per evitare errori di variabili non inizializzate
        lsb = msb = div = width = height = None

        # Configurazione metodo SOLO se parametri manuali
        if manual_params and selected_method == SteganographyMethod.DWT:
            st.info("💡 Configura i parametri DWT usati durante l'occultamento")

            from src.steganografia.dwt.image_operations import ImageSteganography as DWT

            preset = st.selectbox(
                "📋 Preconfigurazione DWT:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Qualità",
                    "📦 Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="dwt_img_recover_preset",
            )

            if preset == "⚖️ Bilanciato":
                DWT.WAVELET = "haar"
                DWT.STEP = 12.0
                DWT.BITS_SECRET = 3
                DWT.BANDS = ["cH", "cV"]
                st.info("✅ Wavelet Haar, STEP=12, 3-bit, cH+cV")
            elif preset == "🎨 Qualità":
                DWT.WAVELET = "haar"
                DWT.STEP = 24.0
                DWT.BITS_SECRET = 4
                DWT.BANDS = ["cH"]
                st.info("🎨 STEP=24, 4-bit, cH")
            elif preset == "📦 Capacità":
                DWT.WAVELET = "haar"
                DWT.STEP = 8.0
                DWT.BITS_SECRET = 2
                DWT.BANDS = ["cH", "cV", "cD"]
                st.info("📦 STEP=8, 2-bit, tutte bande")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    wavelet_val = st.selectbox(
                        "Tipo Wavelet",
                        options=["haar", "db2", "db4", "db8", "sym2", "sym4", "coif1"],
                        index=0,
                        key="dwt_img_rec_wavelet",
                    )
                    step_val = st.slider(
                        "STEP", 8.0, 32.0, 12.0, 4.0, key="dwt_img_rec_step"
                    )
                    bits_val = st.slider("Bit Secret", 2, 4, 3, key="dwt_img_rec_bits")
                with col2:
                    bands_val = st.multiselect(
                        "Bande",
                        ["cH", "cV", "cD"],
                        default=["cH", "cV"],
                        key="dwt_img_rec_bands",
                    )
                    if not bands_val:
                        st.error("⚠️ Seleziona almeno una banda!")
                        bands_val = ["cH"]

                DWT.WAVELET = wavelet_val
                DWT.STEP = step_val
                DWT.BITS_SECRET = bits_val
                DWT.BANDS = bands_val

        elif manual_params and selected_method == SteganographyMethod.PVD:
            st.info("💡 Configura i parametri PVD usati durante l'occultamento")

            from src.steganografia.pvd.image_operations import ImageSteganography as PVD

            preset = st.selectbox(
                "📋 Preconfigurazione PVD:",
                options=[
                    "🎨 Qualità",
                    "📦 Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="pvd_img_recover_preset",
            )

            if preset == "🎨 Qualità":
                PVD.configure_quality_mode()
                st.info("✅ Ranges qualità, step=2, canali R+G")
            elif preset == "📦 Capacità":
                PVD.configure_capacity_mode()
                st.info("📦 Ranges capacità, step=1, tutti i canali")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    use_quality = st.checkbox(
                        "Usa ranges qualità", value=True, key="pvd_img_rec_quality"
                    )
                    pair_step_val = st.slider(
                        "Sparsità", 1, 4, 1, key="pvd_img_rec_step"
                    )
                with col2:
                    channels_val = st.multiselect(
                        "Canali",
                        ["R (0)", "G (1)", "B (2)"],
                        default=["R (0)", "G (1)", "B (2)"],
                        key="pvd_img_rec_channels",
                    )
                    channels_list = (
                        [int(ch.split("(")[1][0]) for ch in channels_val]
                        if channels_val
                        else [0, 1, 2]
                    )

                PVD.configure_custom(
                    pair_step=pair_step_val,
                    channels=channels_list,
                    use_quality_ranges=use_quality,
                )

        elif manual_params and selected_method == SteganographyMethod.LSB:
            st.info("💡 Configura i parametri LSB usati durante l'occultamento")

            preset = st.selectbox(
                "📋 Preconfigurazione LSB:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Alta Qualità",
                    "📦 Alta Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="lsb_img_recover_preset",
            )

            if preset == "⚖️ Bilanciato":
                lsb = 4
                msb = 4
                st.info("⚖️ LSB=4, MSB=4")
            elif preset == "🎨 Alta Qualità":
                lsb = 1
                msb = 8
                st.info("🎨 LSB=1, MSB=8")
            elif preset == "📦 Alta Capacità":
                lsb = 6
                msb = 2
                st.info("📦 LSB=6, MSB=2")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    lsb = st.number_input("LSB", 1, 8, 4, key="lsb_img_rec_lsb")
                with col2:
                    msb = st.number_input("MSB", 1, 8, 4, key="lsb_img_rec_msb")

            # DIV sempre modificabile manualmente
            div = st.number_input(
                "DIV (Divisore)",
                min_value=0.0,
                value=0.0,
                help="0.0 = automatico. Inserisci un valore specifico se conosci quello usato durante l'occultamento.",
                key="lsb_img_rec_div",
            )

        if manual_params:
            st.subheader("📐 Dimensioni Immagine")
            col1, col2 = st.columns(2)
            with col1:
                width = st.number_input(
                    "Larghezza", min_value=1, value=100, key="manual_width"
                )
            with col2:
                height = st.number_input(
                    "Altezza", min_value=1, value=100, key="manual_height"
                )

        output_name = st.text_input(
            "Nome file output", value="recovered_image.png", key="img_recover_output"
        )

        if st.button("🔓 Recupera Immagine", type="primary"):
            if hidden_image:
                # Pulisci risultati precedenti
                if "recover_image_result" in st.session_state:
                    del st.session_state["recover_image_result"]
                try:
                    # Salva immagine temporaneamente
                    hidden_path = save_uploaded_file(hidden_image)
                    if hidden_path:
                        img = Image.open(hidden_path)

                        # Recupera immagine
                        with st.spinner("Recuperando immagine..."):
                            recovered_img = get_image(
                                img,
                                output_name,
                                lsb,
                                msb,
                                div,
                                width,
                                height,
                                backup_file_path,
                                method=selected_method,
                            )

                        if recovered_img:
                            st.success("✅ Immagine recuperata!")

                            # Salva per il download
                            img_buffer = io.BytesIO()
                            recovered_img.save(img_buffer, format="PNG")

                            st.session_state["recover_image_result"] = {
                                "data": img_buffer.getvalue(),
                                "filename": output_name,
                                "preview_image": recovered_img,  # Mantieni anteprima
                                "image_info": {
                                    "width": recovered_img.width,
                                    "height": recovered_img.height,
                                    "mode": recovered_img.mode,
                                },
                            }

                            # Cleanup
                            cleanup_temp_file(output_name)
                        else:
                            st.error("❌ Impossibile recuperare l'immagine")
                    else:
                        st.error("❌ Errore nel salvare l'immagine")

                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
            else:
                st.warning("⚠️ Carica un'immagine!")

        # Sezione download se ci sono risultati
        if "recover_image_result" in st.session_state:
            st.markdown("---")
            st.subheader("📥 Download Risultati")

            result_data = st.session_state["recover_image_result"]

            # Mostra sempre l'immagine recuperata
            if "preview_image" in result_data and "image_info" in result_data:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(
                        result_data["preview_image"],
                        caption="Immagine recuperata",
                        width=400,
                    )
                with col2:
                    info = result_data["image_info"]
                    st.write(f"**Dimensioni:** {info['width']} x {info['height']}")
                    st.write(f"**Modalità:** {info['mode']}")

            create_download_button(
                result_data["data"],
                result_data["filename"],
                "image/png",
                "📥 Scarica immagine recuperata",
            )

    @staticmethod
    def recover_binary_page(selected_method):
        """Pagina per recuperare file binari"""
        from src.steganografia import get_bin_file

        st.subheader("📁 Recuperare File Binario")

        # Upload dell'immagine con dati nascosti
        hidden_image = st.file_uploader(
            "🖼️ Carica l'immagine con file nascosto:",
            type=["png", "jpg", "jpeg"],
            key="recover_binary_hidden_image",
        )

        # Mostra anteprima dell'immagine
        if hidden_image:
            ImageDisplay.show_resized_image(
                hidden_image, "🔒 Immagine con File Nascosto", max_width=400
            )
            ImageDisplay.show_image_details(hidden_image, "Dettagli Immagine")

        # Opzioni parametri
        backup_file_path, use_recent, manual_params = display_backup_options(
            "binary_get", show_manual=True
        )

        # Se l'utente sceglie parametri manuali, ignora il backup
        if manual_params:
            backup_file_path = None

        # Configurazione metodo SOLO se parametri manuali
        dwt_alpha = dwt_bands = dwt_use_all_channels = None
        pvd_ranges_type = pvd_pair_step = pvd_channels = None
        zip_mode = n = div = size = None

        if (
            manual_params
            and manual_params
            and selected_method == SteganographyMethod.DWT
        ):

            st.info("💡 Configura i parametri DWT usati durante l'occultamento")

            from src.steganografia.dwt.binary_operations import (
                BinarySteganography as DWT_Binary,
            )

            preset = st.selectbox(
                "📋 Preconfigurazione DWT:",
                options=[
                    "⚖️ Bilanciato",
                    "📦 Massima Capacità",
                    "🎨 Massima Qualità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="dwt_bin_recover_preset",
            )

            if preset == "⚖️ Bilanciato":
                DWT_Binary.WAVELET = "haar"
                DWT_Binary.ALPHA = 0.1

                DWT_Binary.BANDS = ["cH"]
                DWT_Binary.USE_ALL_CHANNELS = False
                st.info("⚖️ Wavelet Haar, ALPHA=0.1, banda cH, canale R")
            elif preset == "📦 Massima Capacità":
                DWT_Binary.WAVELET = "haar"
                DWT_Binary.ALPHA = 0.15
                DWT_Binary.BANDS = ["cH", "cV", "cD"]
                DWT_Binary.USE_ALL_CHANNELS = True
                st.info("📦 ALPHA=0.15, tutte le bande, tutti i canali")
            elif preset == "🎨 Massima Qualità":
                DWT_Binary.WAVELET = "haar"
                DWT_Binary.ALPHA = 0.05
                DWT_Binary.BANDS = ["cH"]
                DWT_Binary.USE_ALL_CHANNELS = False
                st.info("🎨 ALPHA=0.05, banda cH, canale R")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    wavelet_val = st.selectbox(
                        "Tipo Wavelet",
                        options=["haar", "db2", "db4", "db8", "sym2", "sym4", "coif1"],
                        index=0,
                        key="dwt_bin_rec_wavelet",
                    )
                    alpha_val = st.slider(
                        "ALPHA", 0.05, 0.3, 0.1, 0.05, key="dwt_bin_rec_alpha"
                    )
                    multi_ch = st.checkbox(
                        "Tutti i canali", value=False, key="dwt_bin_rec_multi"
                    )
                with col2:
                    bands_val = st.multiselect(
                        "Bande",
                        ["cH", "cV", "cD"],
                        default=["cH"],
                        key="dwt_bin_rec_bands",
                    )
                    if not bands_val:
                        st.error("⚠️ Seleziona almeno una banda!")
                        bands_val = ["cH"]

                DWT_Binary.WAVELET = wavelet_val
                DWT_Binary.ALPHA = alpha_val
                DWT_Binary.BANDS = bands_val
                DWT_Binary.USE_ALL_CHANNELS = multi_ch

        elif (
            manual_params
            and manual_params
            and selected_method == SteganographyMethod.PVD
        ):

            st.info("💡 Configura i parametri PVD usati durante l'occultamento")

            preset = st.selectbox(
                "📋 Preconfigurazione PVD:",
                options=[
                    "📦 Capacità (consigliato)",
                    "🎨 Qualità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="pvd_bin_recover_preset",
            )

            if preset == "📦 Capacità (consigliato)":
                pvd_ranges_type = "capacity"
                pvd_pair_step = 1
                pvd_channels = [0, 1, 2]
                st.info("📦 Ranges capacità, step=1, tutti i canali")
            elif preset == "🎨 Qualità":
                pvd_ranges_type = "quality"
                pvd_pair_step = 2
                pvd_channels = [0, 1]
                st.info("🎨 Ranges qualità, step=2, canali R+G")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    use_quality = st.checkbox(
                        "Usa ranges qualità", value=False, key="pvd_bin_rec_quality"
                    )
                    pair_step_bin = st.slider(
                        "Sparsità", 1, 4, 1, key="pvd_bin_rec_step"
                    )
                with col2:
                    channels_bin = st.multiselect(
                        "Canali",
                        ["R (0)", "G (1)", "B (2)"],
                        default=["R (0)", "G (1)", "B (2)"],
                        key="pvd_bin_rec_channels",
                    )
                    channels_list = (
                        [int(ch.split("(")[1][0]) for ch in channels_bin]
                        if channels_bin
                        else [0, 1, 2]
                    )

                pvd_ranges_type = "quality" if use_quality else "capacity"
                pvd_pair_step = pair_step_bin
                pvd_channels = channels_list

        elif manual_params and selected_method == SteganographyMethod.LSB:
            st.info("💡 Configura i parametri LSB usati durante l'occultamento")

            preset = st.selectbox(
                "📋 Preconfigurazione LSB:",
                options=[
                    "⚖️ Bilanciato",
                    "🎨 Alta Qualità",
                    "📦 Alta Capacità",
                    "⚙️ Personalizzato",
                ],
                index=0,
                key="lsb_bin_recover_preset",
            )

            if preset == "⚖️ Bilanciato":
                n = 4
                st.info("⚖️ N=4")
            elif preset == "🎨 Alta Qualità":
                n = 1
                st.info("🎨 N=1")
            elif preset == "📦 Alta Capacità":
                n = 6
                st.info("📦 N=6")
            else:
                n = st.number_input("N", 1, 8, 4, key="lsb_bin_rec_n")

            # DIV sempre modificabile manualmente
            div = st.number_input(
                "DIV (Divisore)",
                min_value=0.0,
                value=0.0,
                help="0.0 = automatico. Inserisci un valore specifico se conosci quello usato durante l'occultamento.",
                key="lsb_bin_rec_div",
            )

        if manual_params:
            st.subheader("📎 Parametri File")

            # Per LSB, chiedi sia zip_mode che size
            if selected_method == SteganographyMethod.LSB:
                col1, col2 = st.columns(2)
                with col1:
                    zip_mode = st.selectbox(
                        "Modalità Compressione",
                        [
                            CompressionMode.NO_ZIP,
                            CompressionMode.FILE,
                            CompressionMode.DIR,
                        ],
                        format_func=lambda x: {
                            CompressionMode.NO_ZIP: "❌ Nessuna",
                            CompressionMode.FILE: "🗄️ File",
                            CompressionMode.DIR: "📁 Directory",
                        }.get(x, "❌ Nessuna"),
                        key="manual_zipmode",
                    )
                with col2:
                    size = st.number_input(
                        "Dimensione file (bytes)",
                        min_value=1,
                        value=1000,
                        key="manual_size",
                    )
            # Per DWT e PVD, solo zip_mode (size viene letto dall'header)
            else:
                st.info(
                    "ℹ️ La dimensione del file viene letta automaticamente dall'header nascosto"
                )
                zip_mode = st.selectbox(
                    "Modalità Compressione",
                    [
                        CompressionMode.NO_ZIP,
                        CompressionMode.FILE,
                        CompressionMode.DIR,
                    ],
                    format_func=lambda x: {
                        CompressionMode.NO_ZIP: "❌ Nessuna",
                        CompressionMode.FILE: "🗄️ File",
                        CompressionMode.DIR: "📁 Directory",
                    }.get(x, "❌ Nessuna"),
                    key="manual_zipmode",
                )
        elif manual_params:
            # Per DWT e PVD, solo zip_mode senza size (che viene letto dall'header)
            st.subheader("📎 Parametri File")
            st.info(
                "ℹ️ La dimensione del file viene letta automaticamente dall'header nascosto"
            )
            zip_mode = st.selectbox(
                "Modalità Compressione",
                [
                    CompressionMode.NO_ZIP,
                    CompressionMode.FILE,
                    CompressionMode.DIR,
                ],
                format_func=lambda x: {
                    CompressionMode.NO_ZIP: "❌ Nessuna",
                    CompressionMode.FILE: "🗄️ File",
                    CompressionMode.DIR: "📁 Directory",
                }.get(x, "❌ Nessuna"),
                key="manual_zipmode",
            )

        output_name = st.text_input(
            "Nome file output", value="recovered_file.bin", key="bin_recover_output"
        )

        if st.button("🔓 Recupera File", type="primary"):
            if hidden_image:
                # Pulisci risultati precedenti
                if "recover_binary_result" in st.session_state:
                    del st.session_state["recover_binary_result"]
                try:
                    # Salva immagine temporaneamente
                    hidden_path = save_uploaded_file(hidden_image)
                    if hidden_path:
                        img = Image.open(hidden_path)

                        # Recupera file
                        with st.spinner("Recuperando file..."):
                            get_bin_file(
                                img,
                                output_name,
                                zip_mode,
                                n,
                                div,
                                size,
                                backup_file_path,
                                method=selected_method,
                                dwt_alpha=dwt_alpha,
                                dwt_bands=dwt_bands,
                                dwt_use_all_channels=dwt_use_all_channels,
                                pvd_ranges_type=pvd_ranges_type,
                                pvd_pair_step=pvd_pair_step,
                                pvd_channels=pvd_channels,
                            )

                        if os.path.exists(output_name):
                            st.success("✅ File recuperato!")

                            # Salva per il download
                            file_size = os.path.getsize(output_name)
                            with open(output_name, "rb") as f:
                                st.session_state["recover_binary_result"] = {
                                    "data": f.read(),
                                    "filename": output_name,
                                    "file_size": file_size,  # Mantieni info file
                                    "success_message": f"**File recuperato:** {output_name}",
                                }
                            # Cleanup
                            cleanup_temp_file(output_name)
                        else:
                            st.error("❌ Impossibile recuperare il file")
                    else:
                        st.error("❌ Errore nel salvare l'immagine")

                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
            else:
                st.warning("⚠️ Carica un'immagine!")

        # Sezione download se ci sono risultati
        if "recover_binary_result" in st.session_state:
            st.markdown("---")
            st.subheader("📥 Download Risultati")

            result_data = st.session_state["recover_binary_result"]

            # Mostra sempre le info del file recuperato
            if "success_message" in result_data:
                st.write(result_data["success_message"])
                st.write(f"**Dimensione:** {result_data['file_size']} bytes")

            create_download_button(
                result_data["data"],
                result_data["filename"],
                "application/octet-stream",
                "📥 Scarica file recuperato",
            )
