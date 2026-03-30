import streamlit as st

st.set_page_config(
    page_title="Poool Academy Helper",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Poool Academy Helper")
st.markdown("Intelligenter Assistent für alle Fragen rund um Poool Software und Academy Inhalte")

st.markdown("---")

# Academy Tools
st.subheader("📚 Academy Tools")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("**📚 Academy Chat**")
    st.markdown("""
    - Chat-Assistent für Poool Academy Inhalte
    - Mit Quellenangabe
    - Unterstützt beim beantworten von Fragen zu Poool
    - Beta-Version ggf. Fehleranfällig
    """)
    if st.button("Öffnen →", key="btn_academy_chat", use_container_width=True):
        st.switch_page("sites/academy_chat.py")


st.markdown("---")
st.markdown("Fragen, Ideen oder Feedback: [fabian.kainz@poool.cc](mailto:fabian.kainz@poool.cc)")