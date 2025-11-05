from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Meus Apps",
    layout="wide",
    page_icon="🇧🇷",
    initial_sidebar_state="auto",
)

readme_path: Path = Path(__file__).parent / "README.md"

st.markdown(readme_path.read_text(encoding="utf-8"), unsafe_allow_html=True)
