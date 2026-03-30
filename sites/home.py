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
    - Intelligenter Chat-Assistent für Academy-Inhalte
    - Basiert auf aktueller Academy-Dokumentation
    - Automatische Quellenangaben
    - Verbessertes RAG-System für präzise Antworten
    """)
    if st.button("Öffnen →", key="btn_academy_chat", use_container_width=True):
        st.switch_page("sites/academy_chat.py")

with col2:
    st.markdown("**🔜 Weitere Tools**")
    st.markdown("""
    - Integration mit anderen Poool Tools geplant
    - Erweiterung des Academy-Systems
    - Zusätzliche Funktionalitäten
    - Feedback-System für kontinuierliche Verbesserung
    """)
    st.info("Weitere Tools werden in Kürze hinzugefügt")

st.markdown("---")

# Status und Informationen
st.subheader("ℹ️ Über das Academy Helper System")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("**Aktuelle Features:**")
    st.markdown("""
    - 📚 **Intelligenter Chat**: Beantwortet Fragen basierend auf Academy-Inhalten
    - 🔍 **Erweiterte Suche**: Findet relevante Informationen aus allen Dokumenten
    - 📊 **Feedback-System**: Kontinuierliche Verbesserung durch Nutzerfeedback
    - 🚀 **Performance**: Optimierte Embeddings für schnelle Antworten
    """)

with col2:
    st.markdown("**Technische Details:**")
    st.markdown("""
    - **RAG-System**: Retrieval-Augmented Generation für präzise Antworten
    - **Claude-Integration**: Anthropic's Claude für natürliche Sprachverarbeitung
    - **Caching**: Intelligentes Caching für bessere Performance
    - **N8N-Integration**: Automatisches Logging und Feedback-Sammlung
    """)

st.markdown("---")

# Beta-Hinweis
st.info("""
**🚧 Beta-Version**

Dieses System befindet sich noch in der Beta-Phase. Antworten können unvollständig oder fehlerhaft sein. 
Bei Problemen oder Verbesserungsvorschlägen nutze bitte das Feedback-System im Academy Chat.
""")

st.markdown("---")
st.markdown("Fragen, Ideen oder Feedback: [fabian.kainz@poool.cc](mailto:fabian.kainz@poool.cc)")