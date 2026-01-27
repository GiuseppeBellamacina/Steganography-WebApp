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
            page_icon="🔒",
            layout="wide",
            initial_sidebar_state="expanded",
        )
        
        # Applica stili custom
        from .styles import apply_custom_styles
        apply_custom_styles()
        
        # Header compatto inline
        col_logo, col_title = st.columns([1, 5])
        with col_logo:
            st.markdown(
                "<div style='font-size: 3rem; text-align: center;'>🔒</div>",
                unsafe_allow_html=True,
            )
        with col_title:
            st.markdown(
                "<h2 style='margin-top: 0.5rem; color: var(--text-color);'>Steganografia</h2>",
                unsafe_allow_html=True,
            )
        
        st.markdown("")
    
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
            st.markdown(f'<div class="method-card-container {"selected" if lsb_selected else ""}"></div>', unsafe_allow_html=True)
            if st.button("⚡\nLSB\nVeloce • Alta capacità", key="btn_lsb", use_container_width=True):
                st.session_state.selected_method = SteganographyMethod.LSB
                st.rerun()
            
            # Card DWT
            dwt_selected = st.session_state.selected_method == SteganographyMethod.DWT
            st.markdown(f'<div class="method-card-container {"selected" if dwt_selected else ""}"></div>', unsafe_allow_html=True)
            if st.button("🧪\nDWT\nRobusto • Qualità", key="btn_dwt", use_container_width=True):
                st.session_state.selected_method = SteganographyMethod.DWT
                st.rerun()
            
            # Card PVD
            pvd_selected = st.session_state.selected_method == SteganographyMethod.PVD
            st.markdown(f'<div class="method-card-container {"selected" if pvd_selected else ""}"></div>', unsafe_allow_html=True)
            if st.button("🔀\nPVD\nAdattivo • Versatile", key="btn_pvd", use_container_width=True):
                st.session_state.selected_method = SteganographyMethod.PVD
                st.rerun()
        
        return st.session_state.selected_method

    @staticmethod
    def show_data_type_selector():
        """Mostra le cards per selezionare il tipo di dato"""
        st.markdown("### 📊 Seleziona il tipo di dato")
        st.markdown("")
        
        col1, col2, col3 = st.columns(3)
        
        # Inizializza session state se non esiste
        if "selected_data_type" not in st.session_state:
            st.session_state.selected_data_type = "Stringhe"
        
        with col1:
            text_selected = st.session_state.selected_data_type == "Stringhe"
            st.markdown(f'<div class="data-type-card-container {"selected" if text_selected else ""}"></div>', unsafe_allow_html=True)
            if st.button("📝\nTesto", key="btn_text", use_container_width=True):
                st.session_state.selected_data_type = "Stringhe"
                st.rerun()
        
        with col2:
            img_selected = st.session_state.selected_data_type == "Immagini"
            st.markdown(f'<div class="data-type-card-container {"selected" if img_selected else ""}"></div>', unsafe_allow_html=True)
            if st.button("🖼️\nImmagini", key="btn_image", use_container_width=True):
                st.session_state.selected_data_type = "Immagini"
                st.rerun()
        
        with col3:
            bin_selected = st.session_state.selected_data_type == "File binari"
            st.markdown(f'<div class="data-type-card-container {"selected" if bin_selected else ""}"></div>', unsafe_allow_html=True)
            if st.button("📦\nFile Binari", key="btn_binary", use_container_width=True):
                st.session_state.selected_data_type = "File binari"
                st.rerun()
        
        st.markdown("")
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
                    🔒 <strong>Steganografia App</strong>
                </p>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.8;'>
                    <em>Nascondere è un'arte, rivelare è una scienza</em>
                </p>
                <p style='margin: 0.5rem 0 0 0; font-size: 0.85rem; opacity: 0.6;'>
                    Sviluppato con ❤️ usando Streamlit • Python 3.12
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


class DynamicInstructions:
    """Gestisce le istruzioni dinamiche nella sidebar"""

    @staticmethod
    def show_instructions(data_type: str, mode: str = ""):
        """Mostra istruzioni dinamiche compatte basate su tipo di dati"""
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 💡 Suggerimenti Rapidi")

            if data_type == "Stringhe":
                st.markdown("""
                **Testo:**
                - Inserisci il messaggio
                - Nascondi nell'immagine
                - Recupera quando serve
                """)
            elif data_type == "Immagini":
                st.markdown("""
                **Immagini:**
                - Host deve essere più grande
                - Usa backup per parametri
                - Verifica qualità con PSNR
                """)
            else:  # File binari
                st.markdown("""
                **File:**
                - Comprimi per risparmiare spazio
                - Salva sempre i parametri
                - Usa DIV per file grandi
                """)

    @staticmethod
    def clear_instructions():
        """Pulisce le istruzioni dalla sidebar"""
        with st.sidebar:
            st.empty()

    @staticmethod
    def _show_hide_instructions(data_type: str):
        """Istruzioni per nascondere dati"""
        if data_type == "Stringhe":
            st.markdown("""
            **Nascondere Stringhe:**
            1. 📤 Carica l'immagine di destinazione
            2. ✍️ Scrivi il messaggio da nascondere
            3. 💾 Opzionalmente salva parametri su file
            4. 🔒 Clicca "Nascondi Messaggio"
            5. 📥 Scarica il risultato
            """)
        elif data_type == "Immagini":
            st.markdown("""
            **Nascondere Immagini:**
            1. 📤 Carica l'immagine host (più grande)
            2. 🖼️ Carica l'immagine da nascondere
            3. ⚙️ Imposta parametri LSB/MSB/DIV
            4. 💾 Opzionalmente salva parametri
            5. 🔒 Clicca "Nascondi Immagine"
            6. 📥 Scarica il risultato
            """)
        else:  # File binari
            st.markdown("""
            **Nascondere File:**
            1. 📤 Carica l'immagine di destinazione
            2. 📁 Carica il file da nascondere
            3. ⚙️ Scegli compressione e parametri
            4. 💾 Opzionalmente salva parametri
            5. 🔒 Clicca "Nascondi File"
            6. 📥 Scarica il risultato
            """)

    @staticmethod
    def _show_recover_instructions(data_type: str):
        """Istruzioni per recuperare dati"""
        if data_type == "Stringhe":
            st.markdown("""
            **Recuperare Stringhe:**
            1. 📤 Carica l'immagine con messaggio
            2. 🔓 Clicca "Recupera Messaggio"
            3. 📖 Leggi il messaggio recuperato
            4. 📥 Scarica come file di testo
            
            💡 **Nessun parametro richiesto!**
            """)
        elif data_type == "Immagini":
            st.markdown("""
            **Recuperare Immagini:**
            1. 📤 Carica l'immagine con dati nascosti
            2. 🔧 Scegli fonte parametri:
               - 🔄 Automatico (variabili recenti)
               - 📄 File backup (.dat)
               - ✋ Inserimento manuale
            3. 🔓 Clicca "Recupera Immagine"
            4. 📥 Scarica l'immagine recuperata
            """)
        else:  # File binari
            st.markdown("""
            **Recuperare File:**
            1. 📤 Carica l'immagine con file nascosto
            2. 🔧 Scegli fonte parametri:
               - 🔄 Automatico (variabili recenti)
               - 📄 File backup (.dat)
               - ✋ Inserimento manuale
            3. 🔓 Clicca "Recupera File"
            4. 📥 Scarica il file recuperato
            """)
