import streamlit as st
from src.utils import get_color_scale, format_value
import base64

def render_header():
    st.title("📊 Lecteur DPE")
    st.markdown("Téléchargez votre fichier DPE (Excel) pour obtenir un résumé visuel.")
    st.divider()

def render_address_info(data):
    if data.get('adresse'):
        st.markdown(f"### 📍 {data['adresse']}")
    
    c1, c2 = st.columns(2)
    if data.get('date'):
        c1.caption(f"📅 Date de réalisation : {data['date']}")
    if data.get('date_fin_validite'):
        c2.caption(f"⏳ Valide jusqu'au : {data['date_fin_validite']}")
    
    st.divider()

def render_metrics(data):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Surface", format_value(data.get('surface'), 'm²'))
    
    with col2:
        st.metric("Conso. Énergie", format_value(data.get('conso_kwh'), 'kWh/m²/an'))
        
    with col3:
        st.metric("Émissions GES", format_value(data.get('conso_ges'), 'kgCO2/m²/an'))

def render_dpe_badge(label, type='energy'):
    if not label:
        return
        
    color = get_color_scale(label, type)
    title = "Classe Énergie" if type == 'energy' else "Classe Climat"
    
    html = f"""
    <div style="
        background-color: {color};
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
    ">
        {title} : {label}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_travaux_section(data):
    st.subheader("🛠️ Scénarios de Travaux (DPE)")
    
    packs = data.get('packs_travaux', [])
    recs = data.get('recommendations', [])
    
    if packs:
        # Display Packs from File
        for pack in packs:
            with st.container():
                st.markdown(f"### 📦 Pack de Travaux n°{pack['num']}")
                
                col_main, col_stats = st.columns([0.6, 0.4])
                
                with col_main:
                    st.markdown("**Travaux inclus :**")
                    for t in pack['travaux']:
                        # t is now a dict {titre, description}
                        if isinstance(t, dict):
                            st.markdown(f"- **{t['titre'].capitalize()}**")
                            if t['description']:
                                st.caption(f"  _{t['description']}_")
                        else:
                            # Fallback for old structure or simulated
                            st.markdown(f"- {str(t).capitalize()}")
                    
                    st.divider()
                    mini, maxi = format_value(pack['cout_min'], '€'), format_value(pack['cout_max'], '€')
                    st.markdown(f"**Budget Estimé :** {mini} - {maxi}")

                with col_stats:
                    st.markdown("**Projection après travaux :**")
                    c1, c2 = st.columns(2)
                    with c1:
                        if pack['classe_energie_apres'] != '?':
                            render_dpe_badge(pack['classe_energie_apres'], 'energy')
                        st.caption(f"Conso: {int(pack['conso_apres'])} kWh/m²")
                    with c2:
                         if pack['classe_climat_apres'] != '?':
                            render_dpe_badge(pack['classe_climat_apres'], 'climate')
                         st.caption(f"GES: {int(pack['ges_apres'])} kgCO2/m²")

            st.divider()
            
    elif recs:
        # Fallback to simulated recommendations
        st.info("⚠️ Les packs de travaux officiels n'ont pas été trouvés. Voici des recommandations simulées.")
        for rec in recs:
            with st.container():
                col_r1, col_r2 = st.columns([0.7, 0.3])
                with col_r1:
                    st.markdown(f"#### {rec['title']}")
                    st.write(rec['description'])
                    st.caption(f"_{rec['gain']}_")
                with col_r2:
                    if 'cout' in rec:
                         st.metric("Budget Est.", format_value(rec['cout'], '€'))
            st.divider()
    else:
        st.success("✅ Aucun travaux prioritaire identifié (Logement performant).")


def render_detailed_report(data):
    st.subheader("📋 Rapport Détaillé")
    
    tab1, tab2, tab3 = st.tabs(["🏗️ Général & Bâtiment", "🧱 Enveloppe (Isolation)", "⚙️ Systèmes"])
    
    with tab1:
        st.markdown(f"**Période de Construction:** {data.get('periode_construction')}")
        # st.markdown(f"**Zone Climatique:** {data.get('zone_climatique')}") # Removed as requested
        st.markdown(f"**Altitude:** {format_value(data.get('altitude'), 'm')}")

        st.markdown(f"**Hauteur sous plafond:** {format_value(data.get('hsp'), 'm')}")
    
    with tab2:
        st.markdown("### 🧱 Performance de l'Enveloppe")
        
        # --- 1. Schéma des déperditions ---
        st.markdown("#### Répartition des déperditions de chaleur")
        deps = data.get('deperditions', {})
        if deps:
            # Create a clean table-like display using columns
            labels = {
                'toiture': 'Toiture / Plafond',
                'mur': 'Murs',
                'baies': 'Menuiseries (Fenêtres/Portes)',
                'plancher_bas': 'Plancher Bas',
                'ventilation': 'Ventilation',
                'ponts_thermiques': 'Ponts Thermiques'
            }
            
            # Header
            h1, h2 = st.columns([0.8, 0.2])
            h1.caption("Poste de déperdition")
            h2.caption("Part (%)")
            st.divider()
            
            # Rows
            for k, label in labels.items():
                val = deps.get(k, 0)
                r1, r2 = st.columns([0.8, 0.2])
                with r1:
                    st.markdown(f"**{label}**")
                with r2:
                    st.markdown(f"**{val}%**")
                # Optional: Add small progress bar for better viz
                st.progress(val / 100)
                # st.divider() # Optional: too condensed for dividers between every row? Let's keep it clean sans dividers or minimal.
        
        st.divider()

        # --- 2. Performance de l'isolation & Ventilation ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Performance de l'isolation")
            # Logic to determine status based on Energy Class (Approximation)
            dpe_class = data.get('classe_energie', 'G')
            status = "INSUFFISANTE" if dpe_class in ['F', 'G'] else "MOYENNE" if dpe_class in ['D', 'E'] else "BONNE" if dpe_class in ['C'] else "TRÈS BONNE"
            color = "#ff4b4b" if status == "INSUFFISANTE" else "#ffa500" if status == "MOYENNE" else "#90ee90" if status == "BONNE" else "#228b22"
            
            st.markdown(f"""
            <div style="border: 2px solid #ddd; padding: 10px; border-radius: 5px; text-align: center;">
                <div style="font-size: 40px;">🏠</div>
                <div style="background-color: {color}; color: white; padding: 5px; font-weight: bold;">{status}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown("#### Système de ventilation")
            st.markdown(f"**Type:** {data.get('ventilation_type', 'Non identifié')}")
            st.caption("Une bonne ventilation est essentielle pour la qualité de l'air et la pérennité du bâti.")

        st.divider()

        # --- 3. Confort d'été & ENR ---
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("#### Confort d'été (hors clim)")
            # Simulated based on Inertia
            inertie_id = data.get('inertie_id', '1')
            # 1: Très légère -> Insuffisant, 4: Lourde -> Bon (Hypothesis)
            summer_status = "INSUFFISANT" if inertie_id in ['1', '2'] else "MOYEN"
            color_s = "#ff4b4b" if summer_status == "INSUFFISANT" else "#ffa500"
            
            st.markdown(f"""
            <div style="border: 2px solid #ddd; padding: 10px; border-radius: 5px; text-align: center;">
                <div style="font-size: 40px;">☹️</div>
                <div style="background-color: {color_s}; color: white; padding: 5px; font-weight: bold;">{summer_status}</div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("*Basé sur l'inertie et les protections solaires.")

        with c4:
            st.markdown("#### Énergies Renouvelables")
            has_enr = data.get('has_enr', False)
            if has_enr:
                st.success("✅ Ce logement est équipé de systèmes de production d'énergie renouvelable.")
            else:
                st.info("Ce logement n'est pas encore équipé de systèmes de production d'énergie renouvelable.")
                st.markdown("**Solutions existantes :**")
                st.markdown("- ☀️ Solaire Photovoltaïque")
                st.markdown("- 🌡️ Pompe à Chaleur")
                st.markdown("- 🔥 Chauffage au bois check")

    with tab3:
        st.markdown("### 🔥 Chauffage")
        st.markdown(f"**Générateur:** {data.get('chauffage_generateur')}")
        st.markdown(f"**Émetteur:** {data.get('chauffage_emetteur')}")
        
        st.divider()
        st.markdown("### 🚿 Eau Chaude Sanitaire")
        st.markdown(f"**Installation:** {data.get('ecs_type')}")
        
        st.divider()
        st.markdown("### 💨 Ventilation") # Leaving detailed desc here too
        st.markdown(f"**Type:** {data.get('ventilation_type')}")

def render_debug_view(data):
    with st.expander("🔍 Vue Debug (Données Brutes)"):
        st.write("Ci-dessous les valeurs brutes extraites de l'onglet 'logement'.")
        st.json(data.get('debug_raw', {}))
