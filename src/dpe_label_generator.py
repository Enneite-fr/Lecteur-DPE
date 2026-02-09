import base64

def generate_dpe_svg(conso, classe):
    """
    Génère une étiquette DPE compacte au format SVG.
    Retourne le code SVG sous forme de chaîne.
    """
    
    # Couleurs et paliers DPE
    # Format: (Classe, Couleur, BorneMin, BorneMax)
    # Les bornes Max sont indicatives pour l'affichage du texte
    paliers = [
        ('A', '#009c6d', 0, 70),
        ('B', '#52b153', 71, 110),
        ('C', '#78bd76', 111, 180),
        ('D', '#f4e70f', 181, 250),
        ('E', '#f0b50f', 251, 330),
        ('F', '#eb8235', 331, 420),
        ('G', '#d7221f', 421, 9999)
    ]

    width = 350
    height = 280
    
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">'
    
    
    svg += f'<text x="50%" y="30" text-anchor="middle" font-weight="bold" font-size="16" fill="#333">Consommation</text>'
    svg += f'<text x="50%" y="48" text-anchor="middle" font-size="12" fill="#666">(kWh/m²/an)</text>'
    
    start_y = 65
    step_height = 24
    arrow_width_base = 70
    arrow_step = 12
    
    current_y = start_y
    
    for p_classe, p_color, p_min, p_max in paliers:
        w = arrow_width_base + (ord(p_classe) - ord('A')) * arrow_step
        h = step_height - 4
        
        # Add left padding for centering? Or just keep left aligned with margin.
        left_margin = 20
        
        points = f"{left_margin},{current_y} {left_margin+w-10},{current_y} {left_margin+w},{current_y+h/2} {left_margin+w-10},{current_y+h} {left_margin},{current_y+h}"
        
        svg += f'<polygon points="{points}" fill="{p_color}" />'
        
        svg += f'<text x="{left_margin+w-18}" y="{current_y+h-5}" font-weight="bold" font-size="14" fill="white">{p_classe}</text>'
        
        range_txt = f"≤ {p_max}" if p_classe == 'A' else f"> {420}" if p_classe == 'G' else f"{p_min} à {p_max}"
        
        if w > 60:
             svg += f'<text x="{left_margin+8}" y="{current_y+h/2 + 4}" font-size="11" fill="white" font-weight="bold">{range_txt}</text>'
        
        if classe == p_classe:
            arrow_x = left_margin + w + 15
            arrow_center_y = current_y + h/2
            box_w = 70
            
            svg += f'<path d="M{arrow_x} {arrow_center_y} L{arrow_x+10} {arrow_center_y-10} L{arrow_x+10+box_w} {arrow_center_y-10} L{arrow_x+10+box_w} {arrow_center_y+10} L{arrow_x+10} {arrow_center_y+10} Z" fill="black" />'
            svg += f'<text x="{arrow_x+10+box_w/2}" y="{arrow_center_y+5}" text-anchor="middle" font-weight="bold" font-size="18" fill="white">{int(conso)}</text>'
            
        current_y += step_height

    svg += '</svg>'
    return svg


def generate_ges_svg(emission, classe):
    """
    Génère une étiquette GES compacte au format SVG.
    """
    # ... (colors same as before) ...
    paliers = [
        ('A', '#A3E3F5', 0, 6),
        ('B', '#7AB1D6', 7, 11),
        ('C', '#5E8CB8', 12, 30),
        ('D', '#426899', 31, 50),
        ('E', '#2F487A', 51, 70),
        ('F', '#1F2C5C', 71, 100),
        ('G', '#10143D', 101, 9999)
    ]

    width = 350
    height = 280
    
    svg = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">'
    
    
    svg += f'<text x="50%" y="30" text-anchor="middle" font-weight="bold" font-size="16" fill="#333">Émissions GES</text>'
    svg += f'<text x="50%" y="48" text-anchor="middle" font-size="12" fill="#666">(kg CO₂/m²/an)</text>'
    
    start_y = 65
    step_height = 24
    arrow_width_base = 70
    arrow_step = 12
    
    current_y = start_y
    
    for p_classe, p_color, p_min, p_max in paliers:
        w = arrow_width_base + (ord(p_classe) - ord('A')) * arrow_step
        h = step_height - 4
        
        left_margin = 20
        
        points = f"{left_margin},{current_y} {left_margin+w-10},{current_y} {left_margin+w},{current_y+h/2} {left_margin+w-10},{current_y+h} {left_margin},{current_y+h}"
        
        svg += f'<polygon points="{points}" fill="{p_color}" />'
        svg += f'<text x="{left_margin+w-18}" y="{current_y+h-5}" font-weight="bold" font-size="14" fill="white">{p_classe}</text>'
        
        range_txt = f"≤ {p_max}" if p_classe == 'A' else f"> {100}" if p_classe == 'G' else f"{p_min} à {p_max}"
        if w > 60:
             txt_fill = "black" if p_classe in ['A', 'B'] else "white"
             svg += f'<text x="{left_margin+8}" y="{current_y+h/2 + 4}" font-size="11" fill="{txt_fill}" font-weight="bold">{range_txt}</text>'

        if classe == p_classe:
            arrow_x = left_margin + w + 15
            arrow_center_y = current_y + h/2
            box_w = 70
            
            svg += f'<path d="M{arrow_x} {arrow_center_y} L{arrow_x+10} {arrow_center_y-10} L{arrow_x+10+box_w} {arrow_center_y-10} L{arrow_x+10+box_w} {arrow_center_y+10} L{arrow_x+10} {arrow_center_y+10} Z" fill="black" />'
            svg += f'<text x="{arrow_x+10+box_w/2}" y="{arrow_center_y+5}" text-anchor="middle" font-weight="bold" font-size="18" fill="white">{int(emission)}</text>'
            
        current_y += step_height

    svg += '</svg>'
    return svg
