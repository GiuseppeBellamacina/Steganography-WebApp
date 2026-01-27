"""
Custom CSS styles per l'interfaccia Streamlit
"""


def get_custom_css() -> str:
    """Restituisce il CSS custom per l'applicazione"""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }
    .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span { color: var(--text-color) !important; }
    .element-container, [data-testid="stVerticalBlock"] { background-color: transparent !important; }
    .app-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem; box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3); }
    .app-header h1 { margin: 0; font-size: 2.5rem; font-weight: 700; color: white !important; }
    .app-header p { margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9; color: white !important; }
    .data-type-card { background: var(--background-color); border: 2px solid rgba(102, 126, 234, 0.3); border-radius: 12px; padding: 1.5rem; text-align: center; cursor: pointer; transition: all 0.3s ease; height: 100%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
    .data-type-card:hover { transform: translateY(-5px); border-color: #667eea; box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3); }
    .data-type-card.selected { border-color: #667eea; background: rgba(102, 126, 234, 0.15); box-shadow: 0 5px 15px rgba(102, 126, 234, 0.25); }
    .card-icon { font-size: 3rem; margin-bottom: 0.5rem; }
    .card-title { font-size: 1.3rem; font-weight: 600; color: var(--text-color) !important; margin-bottom: 0.5rem; }
    .card-description { font-size: 0.9rem; color: var(--text-color) !important; opacity: 0.7; }
    .app-footer { text-align: center; padding: 2rem; background-color: var(--secondary-background-color); border-radius: 12px; margin-top: 3rem; color: var(--text-color) !important; }
    .app-footer p, .app-footer strong, .app-footer em { color: var(--text-color) !important; }
    /* Stilizza i pulsanti metodo come card nella sidebar */
    .method-card-container {
        display: none;
    }
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 15px;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 15px !important;
        padding: 20px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
        color: white !important;
        font-size: 1em !important;
        font-weight: 500 !important;
        white-space: pre-line !important;
        text-align: center !important;
        line-height: 1.6 !important;
        height: auto !important;
        min-height: 130px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="stSidebar"] .stButton > button:focus:not(:active) {
        color: white !important;
    }
    /* Marker per card selezionata nella sidebar */
    [data-testid="stSidebar"] .method-card-container.selected + div .stButton > button {
        box-shadow: 0 0 0 3px #4CAF50, 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transform: scale(1.02) !important;
    }
    /* Stilizza i pulsanti tipo dato come card */
    .data-type-card-container {
        display: none;
    }
    [data-testid="column"] .stButton > button {
        background: white !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 12px !important;
        padding: 25px 15px !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        min-height: 150px !important;
        height: auto !important;
        white-space: pre-line !important;
        font-size: 1.1em !important;
        font-weight: 600 !important;
        color: #333 !important;
        line-height: 1.6 !important;
    }
    [data-testid="column"] .stButton > button:hover {
        border-color: #667eea !important;
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.2) !important;
        background: white !important;
    }
    [data-testid="column"] .stButton > button:focus:not(:active) {
        border-color: #e0e0e0 !important;
        color: #333 !important;
    }
    /* Marker per card selezionata tipo dato */
    [data-testid="column"] .data-type-card-container.selected + div .stButton > button {
        border-color: #4CAF50 !important;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%) !important;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: var(--secondary-background-color); padding: 0.5rem; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 0.75rem 1.5rem; font-weight: 600; background-color: transparent; border: none; color: var(--text-color) !important; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; color: white !important; }
    .stTabs [data-baseweb="tab-panel"] { background-color: transparent !important; }
    .stButton > button { border-radius: 8px; padding: 0.75rem 2rem; font-weight: 600; border: none; transition: all 0.3s ease; }
    .stButton > button[kind="primary"] { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); }
    .stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4); }
    [data-testid="stFileUploader"] { background-color: transparent !important; }
    [data-testid="stFileUploader"] section { border: 2px dashed rgba(102, 126, 234, 0.3); border-radius: 10px; padding: 1rem; background: var(--secondary-background-color); transition: all 0.3s ease; }
    [data-testid="stFileUploader"] section:hover { border-color: #667eea; background: rgba(102, 126, 234, 0.05); }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] small { color: var(--text-color) !important; }
    .streamlit-expanderHeader { background-color: var(--secondary-background-color) !important; border-radius: 8px; font-weight: 600; color: var(--text-color) !important; }
    .streamlit-expanderHeader:hover { background-color: rgba(102, 126, 234, 0.1) !important; }
    .streamlit-expanderHeader p, .streamlit-expanderHeader svg { color: var(--text-color) !important; }
    .streamlit-expanderContent { background-color: transparent !important; border-color: var(--secondary-background-color) !important; }
    .stSuccess, .stError, .stWarning, .stInfo { border-radius: 10px; border-left-width: 5px; background-color: var(--secondary-background-color) !important; }
    .stSuccess [data-testid="stMarkdownContainer"], .stError [data-testid="stMarkdownContainer"], .stWarning [data-testid="stMarkdownContainer"], .stInfo [data-testid="stMarkdownContainer"] { color: var(--text-color) !important; }
    [data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: 700; color: #667eea !important; }
    [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] { color: var(--text-color) !important; }
    [data-testid="stSidebar"] { background: var(--secondary-background-color); }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span { color: var(--text-color) !important; }
    [data-testid="stSidebar"] .stInfo { background-color: rgba(102, 126, 234, 0.15) !important; border-color: #667eea !important; }
    .stDownloadButton > button { background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); color: white !important; border-radius: 8px; padding: 0.75rem 2rem; font-weight: 600; border: none; box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3); transition: all 0.3s ease; }
    .stDownloadButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(72, 187, 120, 0.4); }
    .stProgress > div > div > div { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { border-radius: 8px; border-color: var(--secondary-background-color); background: var(--background-color); color: var(--text-color) !important; }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus, .stNumberInput > div > div > input:focus { border-color: #667eea !important; box-shadow: 0 0 0 1px #667eea !important; }
    [data-baseweb="select"] { background-color: var(--background-color) !important; }
    [data-baseweb="select"] span, [data-baseweb="select"] div { color: var(--text-color) !important; }
    .stTextInput label, .stTextArea label, .stSelectbox label, .stFileUploader label, .stNumberInput label, .stCheckbox label, .stRadio label, .stSlider label { color: var(--text-color) !important; font-weight: 500; }
    .stCheckbox span, .stRadio span { color: var(--text-color) !important; }
    [data-testid="column"] { background-color: transparent !important; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .animate-fade-in { animation: fadeIn 0.5s ease-out; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    @media (max-width: 768px) { .app-header h1 { font-size: 1.8rem; } .card-icon { font-size: 2rem; } }
    </style>
    """


def apply_custom_styles():
    import streamlit as st

    st.markdown(get_custom_css(), unsafe_allow_html=True)
