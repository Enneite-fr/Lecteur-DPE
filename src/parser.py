import xml.etree.ElementTree as ET


def safe_text(element):
    """Safely return text from an XML element, or empty string."""
    return element.text if element is not None and element.text else ""

def safe_float(text):
    """Safely convert text to float."""
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0

def parse_dpe_file(uploaded_file):
    """
    Parses the DPE XML file.
    """
    data = {
        'surface': None,
        'conso_kwh': None,
        'conso_ges': None,
        'chauffage_type': None,
        'classe_energie': None,
        'classe_climat': None,
        'adresse': None,
        'dpe_id': None,
        'date': None,
        'packs_travaux': [],
        'recommendations': [], # Kept for compatibility if we want to add generic ones
        'debug_raw': {}
    }
    
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        
        # Helper to find nodes without worrying too much about namespaces if they change
        # For now, we assume standard structure. 
        # The XML provided has a default namespace. ET requires explicit namespace handling
        # or we can strip it. Let's try to map with namespace if needed, 
        # but the provided file output showed <dpe ...> without prefixes on children 
        # (though they inherit default NS).
        # A robust way is to use local-name() in XPath but ET doesn't support that fully.
        # We'll traverse or use {http://www.w3.org/2001/XMLSchema} style if strict, 
        # but often it's easier to just find keys.
        
        # To make it easier, let's just use a recursive search or strip namespaces?
        # Actually, let's try direct paths first. If it fails, we can adjust.
        # Looking at the `view_file` output:
        # <dpe xmlns:xsd="..." ...>
        #   <numero_dpe>...
        
        # ElementTree tag usually includes {namespace}tag.
        # Let's verify by just printing root.tag in a debug step if this fails? 
        # No, I should write robust code.
        
        # Quick namespace map removal strategy:
        # Iterate and strip
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]  # Strip namespace

        # --- Administratif ---
        data['dpe_id'] = safe_text(root.find('numero_dpe'))
        
        admin = root.find('administratif')
        if admin:
            data['date'] = safe_text(admin.find('date_etablissement_dpe'))
            
            geo = admin.find('geolocalisation')
            if geo:
                addr = geo.find('adresses/adresse_bien/label_brut')
                data['adresse'] = safe_text(addr)
                
            # Calculate validity date (10 years for new DPEs)
            if data['date']:
                try:
                    # simplistic date add, assuming YYYY-MM-DD
                    year = int(data['date'][:4])
                    data['date_fin_validite'] = data['date'].replace(str(year), str(year + 10))
                except:
                    data['date_fin_validite'] = "Non déterminé"


        # --- Logement ---
        logement = root.find('logement')
        if logement:
            # General
            carac = logement.find('caracteristique_generale')
            if carac:
                data['surface'] = safe_float(safe_text(carac.find('surface_habitable_logement')))
                data['nombre_niveaux'] = safe_text(carac.find('nombre_niveau_logement'))
                data['annee_construction'] = safe_text(carac.find('annee_construction'))
            
            # Meteo
            meteo = logement.find('meteo')
            if meteo:
                 data['altitude_id'] = safe_text(meteo.find('enum_classe_altitude_id'))
                 data['zone_climatique_id'] = safe_text(meteo.find('enum_zone_climatique_id'))

            # Sortie (Metrics)
            sortie = logement.find('sortie')
            if sortie:
                ep_conso = sortie.find('ep_conso')
                if ep_conso:
                     data['conso_kwh'] = safe_float(safe_text(ep_conso.find('ep_conso_5_usages_m2')))
                     data['classe_energie'] = safe_text(ep_conso.find('classe_bilan_dpe'))
                
                ges = sortie.find('emission_ges')
                if ges:
                    data['conso_ges'] = safe_float(safe_text(ges.find('emission_ges_5_usages_m2')))
                    data['classe_climat'] = safe_text(ges.find('classe_emission_ges'))

            # Heating Description (Generator & Emitter)
            chauffage_coll = logement.find('installation_chauffage_collection')
            generators = []
            emitters = []

            if chauffage_coll:
                for ch in chauffage_coll.findall('installation_chauffage'):
                    # 1. Generators
                    gen_coll = ch.find('generateur_chauffage_collection')
                    if gen_coll:
                        for gen in gen_coll.findall('generateur_chauffage'):
                            desc = safe_text(gen.find('donnee_entree/description'))
                            if desc:
                                generators.append(desc)
                    
                    # 2. Emitters
                    # First try specific emitter nodes
                    em_coll = ch.find('emetteur_chauffage_collection')
                    found_specific_emitter = False
                    if em_coll:
                        for em in em_coll.findall('emetteur_chauffage'):
                            desc = safe_text(em.find('donnee_entree/description'))
                            if desc:
                                emitters.append(desc)
                                found_specific_emitter = True
                    
                    # Fallback: Extract from main description if "Emetteur(s):" is present
                    if not found_specific_emitter:
                        main_desc = safe_text(ch.find('donnee_entree/description'))
                        if "Emetteur(s):" in main_desc:
                            try:
                                # Split and take the part after "Emetteur(s):"
                                em_part = main_desc.split("Emetteur(s):")[1].strip()
                                # Sometimes it might be followed by other text, but usually it's at the end or separated by punctuation.
                                # For now, let's take the whole remainder line or up to a standard delimiter if found? 
                                # The example shows it at the end: "... Emetteur(s): radiateur bitube sans robinet thermostatique"
                                if em_part:
                                    emitters.append(em_part)
                            except IndexError:
                                pass

            # Deduplicate and Join
            data['chauffage_generateur'] = " + ".join(sorted(list(set(generators)))) if generators else "N/A"
            data['chauffage_emetteur'] = " + ".join(sorted(list(set(emitters)))) if emitters else "N/A"
            
            # Legacy compatibility (optional, but good to keep `chauffage_type` populated with something meaningful)
            data['chauffage_type'] = data['chauffage_generateur'] if data['chauffage_generateur'] != "N/A" else "Non identifié"


            # --- Recommendations (Travaux) ---
            travaux_section = root.find('descriptif_travaux')
            if travaux_section:
                packs = travaux_section.find('pack_travaux_collection')
                if packs:
                    pack_counter = 1
                    for pack in packs.findall('pack_travaux'):
                        pack_data = {
                            'num': str(pack_counter), # Renumber sequentially as requested (Pack 1, Pack 2...)
                            'cout_min': safe_float(safe_text(pack.find('cout_pack_travaux_min'))) * 100,
                            'cout_max': safe_float(safe_text(pack.find('cout_pack_travaux_max'))) * 100,
                            'conso_apres': safe_float(safe_text(pack.find('conso_5_usages_apres_travaux'))),
                            'ges_apres': safe_float(safe_text(pack.find('emission_ges_5_usages_apres_travaux'))),
                            'classe_energie_apres': '?', # Not explicitly in pack usually, calculated?
                            'travaux': []
                        }
                        pack_counter += 1
                        
                        # Calculate projected class (approximate)
                        # Standard DPE 2021 thresholds for EP
                        val = pack_data['conso_apres']
                        if val < 70: pack_data['classe_energie_apres'] = 'A'
                        elif val < 110: pack_data['classe_energie_apres'] = 'B'
                        elif val < 180: pack_data['classe_energie_apres'] = 'C'
                        elif val < 250: pack_data['classe_energie_apres'] = 'D'
                        elif val < 330: pack_data['classe_energie_apres'] = 'E'
                        elif val < 420: pack_data['classe_energie_apres'] = 'F'
                        else: pack_data['classe_energie_apres'] = 'G'
                        
                        # Calculate projected climate class
                        val_ges = pack_data['ges_apres']
                        if val_ges < 6: pack_data['classe_climat_apres'] = 'A'
                        elif val_ges < 11: pack_data['classe_climat_apres'] = 'B'
                        elif val_ges < 30: pack_data['classe_climat_apres'] = 'C'
                        elif val_ges < 50: pack_data['classe_climat_apres'] = 'D'
                        elif val_ges < 70: pack_data['classe_climat_apres'] = 'E'
                        elif val_ges < 100: pack_data['classe_climat_apres'] = 'F'
                        else: pack_data['classe_climat_apres'] = 'G'


                        coll = pack.find('travaux_collection')
                        if coll:
                            for t in coll.findall('travaux'):
                                pack_data['travaux'].append({
                                    'titre': safe_text(t.find('description_travaux')),
                                    'description': safe_text(t.find('performance_recommande')) # Mapping performance to desc for UI
                                })
                        
                        data['packs_travaux'].append(pack_data)

            # --- Fiche Technique (Details) ---
            # Initialise defaults
            data.update({
                'periode_construction': data.get('annee_construction'),
                'hsp': 'Non précis',
                'mur_materiaux': 'Non précis',
                'isolation_type': 'Non précis',
                'plancher_bas_type': 'Non précis',
                'plancher_haut_type': 'Non précis',
                'vitrage_type': 'Non précis',
                'baie_type': 'Non précis',
                'ecs_type': 'Non précis',
                'ventilation_type': 'Non précis',
                'chauffage_distribution': 'Non précis',
                'zone_climatique': data.get('zone_climatique_id', 'Inconnue'),
                'altitude': data.get('altitude_id', 'Inconnue')
            })

            # --- ECS Logic Enhancement ---
            ecs_coll = logement.find('installation_ecs_collection')
            if ecs_coll:
                ecs_systems = []
                for ecs in ecs_coll.findall('installation_ecs'):
                    # 1. Generators
                    gen_ecs_coll = ecs.find('generateur_ecs_collection')
                    has_gen = False
                    if gen_ecs_coll:
                        for gen in gen_ecs_coll.findall('generateur_ecs'):
                            desc_g = safe_text(gen.find('donnee_entree/description'))
                            if desc_g:
                                ecs_systems.append(desc_g)
                                has_gen = True
                    
                    # 2. Main Description (Fallback)
                    if not has_gen:
                        desc_m = safe_text(ecs.find('donnee_entree/description'))
                        if desc_m:
                            ecs_systems.append(desc_m)
                
                if ecs_systems:
                     data['ecs_type'] = " + ".join(sorted(list(set(ecs_systems))))

            ft_coll = root.find('fiche_technique_collection')
            if ft_coll:
                # Iterate all sub-fiches
                for ft in ft_coll.findall('fiche_technique'):
                    sub_coll = ft.find('sous_fiche_technique_collection')
                    if sub_coll:
                        for sub in sub_coll.findall('sous_fiche_technique'):
                            val = safe_text(sub.find('valeur'))
                            desc = safe_text(sub.find('description'))
                            
                            if 'Hauteur moyenne sous plafond' in desc:
                                data['hsp'] = val
                            elif 'Matériau mur' in desc and data['mur_materiaux'] == 'Non précis':
                                data['mur_materiaux'] = val
                            elif 'Isolation:' in desc and data['isolation_type'] == 'Non précis':
                                data['isolation_type'] = val
                            elif 'Type de pb' in desc:
                                data['plancher_bas_type'] = val
                            elif 'Type de ph' in desc:
                                data['plancher_haut_type'] = val
                            elif 'Type de vitrage' in desc and data['vitrage_type'] == 'Non précis':
                                data['vitrage_type'] = val
                            elif 'Type ouverture' in desc and data['baie_type'] == 'Non précis':
                                data['baie_type'] = val
                            elif ('Type production ECS' in desc or 'Type installation ECS' in desc) and data['ecs_type'] == 'Non précis':
                                data['ecs_type'] = val
                            elif 'Type de ventilation' in desc:
                                data['ventilation_type'] = val
                            elif 'Type de distribution' in desc:
                                data['chauffage_distribution'] = val
                            elif 'Altitude' in desc:
                                data['altitude'] = val
                            elif 'Zone climatique' in desc: # Might not be explicit in description like this
                                data['zone_climatique'] = val
                            elif 'Année de construction' in desc:
                                data['periode_construction'] = val

            # Fallback for construction period if not found in fiche_technique
            if not data.get('periode_construction'):
                # Mapping ID to text
                # 1: Avant 1948, 2: 1949-1974, 3: 1975-1977, 4: 1978-1982, 5: 1983-1988
                # 6: 1989-2000, 7: 2001-2005, 8: 2006-2012, 9: 2013-2021, 10: Après 2021
                period_map = {
                    '1': "Avant 1948", '2': "1949-1974", '3': "1975-1977", '4': "1978-1982",
                    '5': "1983-1988", '6': "1989-2000", '7': "2001-2005", '8': "2006-2012",
                    '9': "2013-2021", '10': "Après 2021"
                }
                pid = safe_text(logement.find('caracteristique_generale/enum_periode_construction_id'))
                data['periode_construction'] = period_map.get(pid, "Inconnue")

            # --- Enveloppe Details (Heat Loss & Comfort) ---
            data['deperditions'] = {}
            if sortie:
                dep = sortie.find('deperdition')
                if dep:
                    # Extract absolute values
                    vals = {
                        'mur': safe_float(safe_text(dep.find('deperdition_mur'))),
                        'toiture': safe_float(safe_text(dep.find('deperdition_plancher_haut'))),
                        'plancher_bas': safe_float(safe_text(dep.find('deperdition_plancher_bas'))),
                        'baies': safe_float(safe_text(dep.find('deperdition_baie_vitree'))) + safe_float(safe_text(dep.find('deperdition_porte'))),
                        'ponts_thermiques': safe_float(safe_text(dep.find('deperdition_pont_thermique'))),
                        'ventilation': safe_float(safe_text(dep.find('deperdition_renouvellement_air')))
                    }
                    total = sum(vals.values())
                    if total > 0:
                        # Calculate percentages ensuring sum is 100% (Largest Remainder Method)
                        # 1. Calculate raw shares
                        raw_shares = {k: (v / total) * 100 for k, v in vals.items()}
                        
                        # 2. Initial floor rounding
                        rounded_shares = {k: int(v) for k, v in raw_shares.items()}
                        
                        # 3. Calculate difference
                        diff = 100 - sum(rounded_shares.values())
                        
                        # 4. Distribute remainder to largest fractional parts
                        # Sort by fractional part descending
                        sorted_keys = sorted(raw_shares.keys(), key=lambda k: raw_shares[k] - int(raw_shares[k]), reverse=True)
                        
                        for i in range(diff):
                            key = sorted_keys[i % len(sorted_keys)]
                            rounded_shares[key] += 1
                            
                        data['deperditions'] = rounded_shares
            
            # Inertie & Comfort
            env = root.find('logement/enveloppe')
            if env:
                inertie = env.find('inertie/enum_classe_inertie_id')
                data['inertie_id'] = safe_text(inertie) # 1: Très légère, 2: Légère, 3: Moyenne, 4: Lourde (Approx mapping needed)
            
            # Renewables
            enr = root.find('logement/production_elec_enr')
            data['has_enr'] = True if enr is not None and enr.get('{http://www.w3.org/2001/XMLSchema-instance}nil') != 'true' else False

    except Exception as e:
        return {'error': f"Erreur XML: {str(e)}"}
    
    return data
