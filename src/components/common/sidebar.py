import streamlit as st

def show_sidebar() -> None:
    with st.sidebar:
        # Load & show logo image
        logo_url = "https://res.cloudinary.com/helpkit/image/upload/v1688731978/poool_logo_dark_ff5c6f1fe4.png"
        st.logo(logo_url, size="large", link=None, icon_image=None)

        # Academy Helper Beta info
        st.markdown("""
        **Academy Helper (Beta)**
        
        Dein Assistent für alle Fragen rund um Poool Software. Aktuell noch in der Beta Version mit ggf. fehlerhaften Antworten.
        """)
        
        st.markdown("---")
        
        # Space for page-specific sidebar content
        # This can be extended by individual pages if needed