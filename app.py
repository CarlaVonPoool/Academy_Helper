import streamlit as st
from src.components.common import sidebar

# Show sidebar on all pages
sidebar.show_sidebar()

# Define navigation
home = st.Page("sites/home.py", title="Übersicht", icon="🏠", default=True)

# Academy Tools
academy_chat = st.Page("sites/academy_chat.py", title="Academy Chat", icon="📚")

pg = st.navigation({
    "Allgemein": [home],
    "Academy Tools": [academy_chat]
})

pg.run()