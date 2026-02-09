from nicegui import ui
from src.parser import parse_dpe_file
from src.utils import get_color_scale, format_value
import io
import json
from src.dpe_label_generator import generate_dpe_svg, generate_ges_svg

def render_dpe_badge(label, type='energy'):
    if not label:
        return
    color = get_color_scale(label, type)
    title = "Classe Énergie" if type == 'energy' else "Classe Climat"
    
    with ui.card().classes('w-full text-white text-center p-4 rounded-xl shadow-lg').style(f'background-color: {color}'):
        ui.label(f'{title} : {label}').classes('text-2xl font-bold')

def render_dpe_scale(current_class, val_conso, val_ges, current_class_ges):
    # DPE & GES Scale Component using SVG Generator
    # Wrap on mobile (flex-wrap), centered
    with ui.row().classes('w-full justify-center items-stretch flex-wrap gap-8'):
         # DPE Energy Scale - Centered with card frame
         with ui.card().classes('items-center justify-center p-6 min-w-[300px] flex-grow md:flex-grow-0 border dark:border-gray-700 shadow-sm'):
            ui.label('Étiquette Énergie').classes('text-xl font-bold mb-4 text-primary dark:text-blue-400')
            svg_dpe = generate_dpe_svg(val_conso, current_class)
            ui.html(svg_dpe).style('width: 350px; height: 280px;')

         # GES Scale (Climate)
         with ui.card().classes('items-center justify-center p-6 min-w-[300px] flex-grow md:flex-grow-0 border dark:border-gray-700 shadow-sm'):
            ui.label('Étiquette Climat').classes('text-xl font-bold mb-4 text-primary dark:text-blue-400')
            svg_ges = generate_ges_svg(val_ges, current_class_ges)
            ui.html(svg_ges).style('width: 350px; height: 280px;')



def render_metrics(data):
    # Wrap on mobile
    with ui.row().classes('w-full justify-center gap-4 mt-4 flex-wrap'):
        with ui.card().classes('p-4 items-center dark:bg-slate-800 min-w-[200px] flex-grow text-center'):
            ui.label('Surface').classes('text-gray-500 dark:text-gray-400')
            with ui.row().classes('items-baseline gap-2 justify-center'):
                ui.label(format_value(data.get('surface'), 'm²')).classes('text-2xl font-bold')
                if data.get('nombre_niveaux'):
                    ui.label(f"({data.get('nombre_niveaux')} niveaux)").classes('text-sm text-gray-400')

        with ui.card().classes('p-4 items-center dark:bg-slate-800 min-w-[200px] flex-grow text-center'):
            ui.label('Conso. Énergie').classes('text-gray-500 dark:text-gray-400')
            ui.label(format_value(data.get('conso_kwh'), 'kWh/m²/an')).classes('text-2xl font-bold')
        with ui.card().classes('p-4 items-center dark:bg-slate-800 min-w-[200px] flex-grow text-center'):
            ui.label('Émissions GES').classes('text-gray-500 dark:text-gray-400')
            ui.label(format_value(data.get('conso_ges'), 'kgCO2/m²/an')).classes('text-2xl font-bold')

def render_travaux_section(data):
    ui.label('🛠️ Scénarios de Travaux (DPE)').classes('text-2xl font-bold mt-8 text-center w-full')
    
    packs = data.get('packs_travaux', [])
    if packs:
        for pack in packs:
            with ui.card().classes('w-full p-6 mb-8 dark:bg-slate-800'):
                ui.label(f"📦 Pack de Travaux n°{pack['num']}").classes('text-xl font-bold mb-4')
                
                # Stack on mobile, side-by-side on desktop from md
                with ui.row().classes('w-full justify-center items-stretch gap-8 flex-wrap'):
                    # Description & Cost
                    with ui.column().classes('w-full md:w-5/12 lg:w-1/2 flex-grow min-w-[300px] justify-between'):
                        ui.label('Travaux inclus :').classes('font-bold text-lg')
                        for t in pack['travaux']:
                            if isinstance(t, dict):
                                with ui.column().classes('mb-2 ml-2'):
                                    ui.label(f"• {t['titre'].capitalize()}").classes('font-medium text-base')
                                    if t['description']:
                                        ui.label(t['description']).classes('text-sm italic text-gray-600 ml-4 dark:text-gray-400')
                        
                        ui.separator().classes('my-4')
                        mini, maxi = format_value(pack['cout_min'], '€'), format_value(pack['cout_max'], '€')
                        ui.label(f"Budget Estimé : {mini} - {maxi}").classes('text-xl font-bold text-primary dark:text-blue-400')

                    # Projections - Centered in remaining space
                    with ui.column().classes('w-full md:w-5/12 lg:w-auto flex-grow items-center justify-center border-t md:border-t-0 md:border-l pt-6 md:pt-0 pl-0 md:pl-8 border-gray-200 dark:border-gray-700'):
                         ui.label('Après travaux :').classes('font-bold mb-4 text-lg w-full text-center')
                         
                         # Allow wrapping if screen is narrow, but side-by-side if space allows
                         # Center content within this block
                         with ui.row().classes('gap-6 justify-center flex-wrap w-full'):
                            # Energy Badge (SVG)
                            if pack['classe_energie_apres'] != '?':
                                with ui.card().classes('items-center justify-center p-4 border dark:border-gray-700 shadow-sm'):
                                    svg_en = generate_dpe_svg(pack['conso_apres'], pack['classe_energie_apres'])
                                    # Use consistent scale
                                    ui.html(svg_en).style('width: 280px; height: 280px;')

                            # Climate Badge (SVG)
                            if pack['classe_climat_apres'] != '?':
                                with ui.card().classes('items-center justify-center p-4 border dark:border-gray-700 shadow-sm'):
                                    svg_ges = generate_ges_svg(pack['ges_apres'], pack['classe_climat_apres'])
                                    ui.html(svg_ges).style('width: 280px; height: 280px;')
    else:
        ui.label('✅ Aucun travaux prioritaire identifié (Logement performant).').classes('text-green-600 font-bold dark:text-green-400 text-center w-full')

def render_detailed_report(data):
    ui.label('📋 Rapport Détaillé').classes('text-2xl font-bold mt-8 mb-4 text-center w-full')
    
    # Responsive grid: 1 col on small, 2 on medium, 3 on large screens
    with ui.grid().classes('w-full gap-8 grid-cols-1 md:grid-cols-2 lg:grid-cols-3 auto-rows-fr'):
        # --- Column 1: General ---
        with ui.card().classes('p-6 dark:bg-slate-800 h-full flex flex-col justify-between'):
            with ui.column().classes('gap-4'):
                ui.label('🏗️ Général & Bâtiment').classes('text-xl font-bold text-primary dark:text-blue-400')
                with ui.column().classes('gap-2 text-base'):
                    ui.label(f"Période de Construction: {data.get('periode_construction')}").classes('font-medium')
                    ui.label(f"Altitude: {format_value(data.get('altitude'), 'm')}").classes('font-medium')
                    ui.label(f"Hauteur sous plafond: {format_value(data.get('hsp'), 'm')}").classes('font-medium')
                    if data.get('nombre_niveaux'):
                        ui.label(f"Nombre de niveaux: {data.get('nombre_niveaux')}").classes('font-medium')
            
            with ui.column().classes('mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 w-full'):
                ui.label('Système de ventilation').classes('font-bold mb-1')
                ui.label(f"Type: {data.get('ventilation_type', 'Non identifié')}")
                ui.label("Une bonne ventilation est essentielle pour la qualité de l'air.").classes('text-sm italic text-gray-500 dark:text-gray-400 mt-2')

        # --- Column 2: Envelope ---
        with ui.card().classes('p-6 dark:bg-slate-800 h-full flex flex-col justify-between'):
             with ui.column().classes('gap-4 w-full'):
                ui.label('🧱 Enveloppe (Isolation)').classes('text-xl font-bold text-primary dark:text-blue-400')
                
                ui.label("Répartition des déperditions").classes('font-bold mb-2')
                deps = data.get('deperditions', {})
                if deps:
                   labels = {
                       'toiture': 'Toiture',
                       'mur': 'Murs',
                       'baies': 'Menuiseries',
                       'plancher_bas': 'Sol',
                       'ventilation': 'Ventil.',
                       'ponts_thermiques': 'Ponts Th.'
                   }
                   for k, label in labels.items():
                       val = deps.get(k, 0)
                       if val > 0: # Only show non-zero
                           with ui.row().classes('w-full items-center mb-1 text-sm'):
                               ui.label(label).classes('flex-grow font-medium')
                               ui.label(f'{val}%').classes('font-bold mr-2')
                               ui.linear_progress(value=val/100).classes('w-1/3 rounded-full h-2').props('color=primary track-color=grey-3')
             
             with ui.column().classes('mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 w-full'):
                 ui.label('Performance Isolation').classes('font-bold mb-2')
                 dpe_class = data.get('classe_energie', 'G')
                 status = "INSUFFISANTE" if dpe_class in ['F', 'G'] else "MOYENNE" if dpe_class in ['D', 'E'] else "BONNE" if dpe_class in ['C'] else "TRÈS BONNE"
                 color = "#ff4b4b" if status == "INSUFFISANTE" else "#ffa500" if status == "MOYENNE" else "#90ee90" if status == "BONNE" else "#228b22"
                 ui.label(status).style(f'background-color: {color}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; display: inline-block;')

        # --- Column 3: Systems ---
        with ui.card().classes('p-6 dark:bg-slate-800 h-full flex flex-col justify-start'):
             ui.label('⚙️ Systèmes').classes('text-xl font-bold mb-4 text-primary dark:text-blue-400')
             
             with ui.column().classes('gap-2'):
                 ui.label('🔥 Chauffage').classes('font-bold text-lg')
                 with ui.row().classes('items-center gap-2'):
                     ui.icon('thermostat').classes('text-gray-500')
                     ui.label(f"Générateur: {data.get('chauffage_generateur')}").classes('font-medium')
                 with ui.row().classes('items-center gap-2'):
                     ui.icon('heat_pump').classes('text-gray-500')
                     ui.label(f"Émetteurs: {data.get('chauffage_emetteur')}").classes('font-medium')
             
             ui.separator().classes('my-6')
             
             with ui.column().classes('gap-2'):
                 ui.label('🚿 Eau Chaude Sanitaire').classes('font-bold text-lg')
                 with ui.row().classes('items-center gap-2'):
                     ui.icon('water_drop').classes('text-blue-500')
                     ui.label(f"Installation ECS: {data.get('ecs_type')}").classes('font-medium')

async def handle_upload(e, container):

    
    # Try different ways to access content
    # Try different ways to access content
    content = None
    
    try:
        if hasattr(e, 'content') and e.content:
            content = e.content.read()
            # NiceGUI/Starlette upload content might look like a file but read() returns bytes
            
        elif hasattr(e, 'file') and hasattr(e.file, 'read'):
            content = e.file.read()
            if hasattr(content, '__await__'):
                content = await content
                
    except Exception as err:
        ui.notify(f"Erreur de lecture: {str(err)}", type='negative')
        content = None

    if not content:
        ui.notify("Erreur interne: Impossible de lire le fichier (format non supporté ?).", type='negative')
        return

    data = parse_dpe_file(io.BytesIO(content))
    
    container.clear()
    with container:
        if 'error' in data:
            ui.notify(f"Erreur: {data['error']}", type='negative')
            return
        
        ui.notify("Fichier analysé avec succès !", type='positive')
        
        # Address & Validity
        if data.get('adresse'):
            ui.label(f"📍 {data['adresse']}").classes('text-2xl font-bold mt-4 text-center')
        with ui.row().classes('w-full mt-2 justify-center gap-4 flex-wrap'):
            if data.get('date'):
                ui.label(f"📅 Date : {data['date']}").classes('text-gray-500 dark:text-gray-400')
            if data.get('date_fin_validite'):
                ui.label(f"⏳ Valide jusqu'au : {data['date_fin_validite']}").classes('text-gray-500 dark:text-gray-400')
        
        render_metrics(data)
        
        with ui.row().classes('w-full justify-center mt-8'): # ID: render_dpe_scale_call
            render_dpe_scale(data.get('classe_energie'), data.get('conso_kwh'), data.get('conso_ges'), data.get('classe_climat'))
            
        ui.separator().classes('my-6')
        render_travaux_section(data)
        ui.separator().classes('my-6')
        render_detailed_report(data)
        
        with ui.expansion('🔍 Vue Debug (Données Brutes)').classes('w-full mt-8'):
            ui.code(json.dumps(data.get('debug_raw', {}), indent=2, default=str), language='json')

@ui.page('/')
def main_page():
    # Dark mode (auto system preference by default)
    dark = ui.dark_mode()
    
    # Body background color adapting to light/dark mode
    ui.query('body').classes('bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors duration-300')
    
    # Adaptive Main Container (wider on large screens)
    with ui.column().classes('w-full max-w-screen-xl mx-auto px-4 md:px-8 py-8 items-center'):
        # Header row with title and dark mode toggle
        with ui.row().classes('w-full justify-between items-center mb-8'):
            ui.label('📊 Lecteur DPE').classes('text-3xl md:text-5xl font-bold text-primary dark:text-blue-400')
            with ui.row().classes('items-center gap-2'):
                ui.button(icon='dark_mode', on_click=lambda: dark.toggle()).props('flat round color=grey')

        ui.label('Téléchargez votre fichier DPE (XML) pour obtenir un résumé visuel.').classes('text-center text-lg text-gray-600 dark:text-gray-300 mb-8')
        
        result_container = ui.column().classes('w-full items-center gap-8')
        
        ui.upload(on_upload=lambda e: handle_upload(e, result_container), 
                  label='Choisir un fichier DPE (XML)',
                  auto_upload=True,
                  multiple=False).classes('w-full max-w-md shadow-md dark:bg-slate-800').props('flat bordered')
