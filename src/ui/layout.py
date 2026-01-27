"""
Layout e istruzioni per l'interfaccia Streamlit
"""

import streamlit as st


class AppLayout:
    """Gestisce il layout dell'applicazione"""

    @staticmethod
    def setup_page():
        """Configura la pagina iniziale"""
        st.set_page_config(
            page_title="Steganografia App",
            page_icon="🎨",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Applica stili custom
        from .styles import apply_custom_styles

        apply_custom_styles()

        # Header principale
        st.markdown(
            """
            <div style='text-align: center; padding: 1rem 0 2rem 0;'>
                <h1 style='margin: 0; font-size: 4.5rem; font-weight: 700; 
                           background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           -webkit-background-clip: text;
                           -webkit-text-fill-color: transparent;
                           background-clip: text;
                           text-shadow: 0 0 30px rgba(102, 126, 234, 0.3),
                                        0 0 60px rgba(118, 75, 162, 0.2);'>
                    Steganography WebApp
                </h1>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.7;'>
                    Hide data within images using advanced algorithms
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def setup_sidebar():
        """Configura la sidebar con cards verticali per i metodi"""
        from config.constants import SteganographyMethod

        with st.sidebar:
            st.markdown("### ⚙️ Metodo Steganografico")
            st.markdown("")

            # Inizializza session state se non esiste
            if "selected_method" not in st.session_state:
                st.session_state.selected_method = SteganographyMethod.LSB

            # Selezione metodo con pulsanti stilizzati come card
            # Card LSB
            lsb_selected = st.session_state.selected_method == SteganographyMethod.LSB
            st.markdown(
                f'<div class="method-card-container {"selected" if lsb_selected else ""}"></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "⚡\nLSB\nVeloce • Alta capacità",
                key="btn_lsb",
                use_container_width=True,
            ):
                st.session_state.selected_method = SteganographyMethod.LSB
                st.rerun()

            # Card DWT
            dwt_selected = st.session_state.selected_method == SteganographyMethod.DWT
            st.markdown(
                f'<div class="method-card-container {"selected" if dwt_selected else ""}"></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "🧪\nDWT\nRobusto • Qualità", key="btn_dwt", use_container_width=True
            ):
                st.session_state.selected_method = SteganographyMethod.DWT
                st.rerun()

            # Card PVD
            pvd_selected = st.session_state.selected_method == SteganographyMethod.PVD
            st.markdown(
                f'<div class="method-card-container {"selected" if pvd_selected else ""}"></div>',
                unsafe_allow_html=True,
            )
            if st.button(
                "🔀\nPVD\nAdattivo • Versatile", key="btn_pvd", use_container_width=True
            ):
                st.session_state.selected_method = SteganographyMethod.PVD
                st.rerun()

        return st.session_state.selected_method

    @staticmethod
    def show_data_type_selector():
        """Mostra le cards per selezionare il tipo di dato"""
        st.markdown("### 📊 Seleziona il tipo di dato")

        col1, col2, col3 = st.columns(3)

        # Inizializza session state se non esiste
        if "selected_data_type" not in st.session_state:
            st.session_state.selected_data_type = "Stringhe"

        with col1:
            text_selected = st.session_state.selected_data_type == "Stringhe"
            st.markdown(
                f'<div class="data-type-card-container {"selected" if text_selected else ""}"></div>',
                unsafe_allow_html=True,
            )
            if st.button("📝\nTesto", key="btn_text", use_container_width=True):
                st.session_state.selected_data_type = "Stringhe"
                st.rerun()

        with col2:
            img_selected = st.session_state.selected_data_type == "Immagini"
            st.markdown(
                f'<div class="data-type-card-container {"selected" if img_selected else ""}"></div>',
                unsafe_allow_html=True,
            )
            if st.button("🖼️\nImmagini", key="btn_image", use_container_width=True):
                st.session_state.selected_data_type = "Immagini"
                st.rerun()

        with col3:
            bin_selected = st.session_state.selected_data_type == "File binari"
            st.markdown(
                f'<div class="data-type-card-container {"selected" if bin_selected else ""}"></div>',
                unsafe_allow_html=True,
            )
            if st.button("📦\nFile Binari", key="btn_binary", use_container_width=True):
                st.session_state.selected_data_type = "File binari"
                st.rerun()

        return st.session_state.selected_data_type

    @staticmethod
    def display_host_image_section():
        """Mostra la sezione per caricare l'immagine host"""
        st.subheader("🖼️ Immagine di destinazione")
        host_image = st.file_uploader(
            "Carica l'immagine su cui nascondere i dati",
            type=["png", "jpg", "jpeg"],
            key="host_image",
        )
        return host_image

    @staticmethod
    def display_hidden_image_section():
        """Mostra la sezione per caricare l'immagine con dati nascosti"""
        st.subheader("🖼️ Immagine con dati nascosti")
        hidden_image = st.file_uploader(
            "Carica l'immagine che contiene i dati nascosti",
            type=["png", "jpg", "jpeg"],
            key="hidden_image",
        )
        return hidden_image

    @staticmethod
    def display_footer():
        """Mostra il footer dell'applicazione"""
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="app-footer">
                <p style='font-size: 1.1rem; margin: 0;'>
                    <strong>Steganography WebApp</strong>
                </p>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;'>
                    <em>Hiding is an art, revealing is a science</em>
                </p>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.6;'>
                    Sviluppato con ❤️ usando Streamlit • Python 3.12
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
