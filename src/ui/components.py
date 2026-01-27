"""
Componenti helper per l'interfaccia Streamlit
"""

import os
import tempfile

import streamlit as st


def save_uploaded_file(uploaded_file, suffix: str = "") -> str | None:
    """Salva un file caricato in una posizione temporanea"""
    if uploaded_file is not None:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{uploaded_file.name}{suffix}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None


def display_backup_options(
    data_type_key: str, show_manual: bool = True
) -> tuple[str | None, bool, bool]:
    """
    Mostra le opzioni di backup e recupero parametri

    Returns:
        Tuple di (backup_file_path, use_recent, manual_params)
    """
    st.subheader("🔧 Gestione Parametri")

    # Radio button per scelta parametri
    options = ["Automatico (usa variabili recenti)", "File backup (.dat)"]
    if show_manual:
        options.append("Inserimento manuale")

    param_choice = st.radio(
        "Come vuoi recuperare i parametri?",
        options,
        key=f"param_choice_{data_type_key}",
        horizontal=True,
    )

    backup_file_path = None
    use_recent = param_choice == "Automatico (usa variabili recenti)"
    manual_params = param_choice == "Inserimento manuale"

    if param_choice == "File backup (.dat)":
        backup_file = st.file_uploader(
            "Carica file backup (.dat)",
            type=["dat"],
            key=f"backup_upload_{data_type_key}",
        )
        if backup_file:
            backup_file_path = save_uploaded_file(backup_file)

    return backup_file_path, use_recent, manual_params


def display_image_info(uploaded_file, img, caption: str) -> None:
    """Mostra informazioni su un'immagine caricata"""
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image(uploaded_file, caption=caption, width=400)
    with col2:
        st.write(f"**Dimensioni:** {img.width} x {img.height}")
        st.write(f"**Modalità:** {img.mode}")
        if hasattr(uploaded_file, "type"):
            st.write(f"**Formato:** {uploaded_file.type}")


def cleanup_temp_file(file_path: str) -> None:
    """Rimuove un file temporaneo se esiste"""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass  # Ignora errori di cleanup


def create_download_button(data, filename: str, mime: str, label: str) -> None:
    """Crea un pulsante di download"""
    st.download_button(label=label, data=data, file_name=filename, mime=mime)
