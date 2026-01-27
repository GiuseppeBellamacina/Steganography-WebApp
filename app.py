"""
Applicazione Streamlit principale per la Steganografia
Utilizza l'architettura modulare refactored
"""

import traceback

import streamlit as st

from src.ui.hide_pages import HideDataPages
from src.ui.image_utils import ResultDisplay

# Import dei moduli refactored
from src.ui.layout import AppLayout
from src.ui.recover_pages import RecoverDataPages


def main():
    """Funzione principale dell'applicazione"""
    try:
        # Setup della pagina
        AppLayout.setup_page()

        # Mostra selector del tipo di dato (cards cliccabili)
        data_type = AppLayout.show_data_type_selector()

        # Setup della sidebar con metodi
        selected_method = AppLayout.setup_sidebar()

        # Mostra metodo selezionato come sottotitolo
        method_names = {
            "lsb": "⚡ LSB - Least Significant Bit",
            "dwt": "🧪 DWT - Discrete Wavelet Transform",
            "pvd": "🔀 PVD - Pixel Value Differencing"
        }
        st.markdown(f"#### {method_names.get(selected_method, 'Nessuna modalità')}")

        # Tabs per Hide/Recover
        tab_hide, tab_recover = st.tabs(["🔒 Nascondi Dati", "🔓 Recupera Dati"])

        with tab_hide:
            hide_pages = HideDataPages()

            if data_type == "Stringhe":
                hide_pages.hide_string_page(selected_method)
            elif data_type == "Immagini":
                hide_pages.hide_image_page(selected_method)
            else:  # File binari
                hide_pages.hide_binary_page(selected_method)

        with tab_recover:
            recover_pages = RecoverDataPages()

            if data_type == "Stringhe":
                recover_pages.recover_string_page(selected_method)
            elif data_type == "Immagini":
                recover_pages.recover_image_page(selected_method)
            else:  # File binari
                recover_pages.recover_binary_page(selected_method)

        # Footer
        AppLayout.display_footer()

    except Exception as e:
        # Gestione errori globali
        ResultDisplay.show_error_message(
            f"Errore nell'applicazione: {str(e)}",
            [
                "Ricarica la pagina",
                "Verifica che tutti i file siano presenti",
                "Controlla i log per dettagli aggiuntivi"
            ]
        )

        # In modalità debug, mostra anche il traceback
        if st.sidebar.checkbox("🐛 Mostra dettagli debug"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
