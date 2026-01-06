import streamlit as st
from src.parser import parse_dpe_file
from src.ui import render_header, render_metrics, render_dpe_badge, render_debug_view, render_detailed_report, render_travaux_section, render_address_info

# Page Config
st.set_page_config(
    page_title="Lecteur DPE",
    page_icon="🏠",
    layout="wide"
)

def main():
    render_header()
    
    uploaded_file = st.file_uploader("Choisissez un fichier DPE (XML)", type=['xml'])
    
    if uploaded_file is not None:
        with st.spinner("Analyse du fichier en cours..."):
            data = parse_dpe_file(uploaded_file)
            
            if 'error' in data:
                st.error(f"Erreur lors de l'analyse du fichier: {data['error']}")
            else:
                st.success("Fichier analysé avec succès !")
                
                # Main Dashboard
                render_address_info(data)
                render_metrics(data)
                
                col_e, col_c = st.columns(2)
                with col_e:
                    render_dpe_badge(data.get('classe_energie'), 'energy')
                with col_c:
                    render_dpe_badge(data.get('classe_climat'), 'climate')
                
                st.divider()

                # Recommendations
                render_travaux_section(data)
                
                st.divider()
                
                # Detailed Report
                render_detailed_report(data)
                
                # Debug View to help user identify keys
                render_debug_view(data)

if __name__ == "__main__":
    main()
