def get_color_scale(value, type='energy'):
    """
    Returns the color for a given DPE class or value.
    """
    # Official DPE color scale roughly approximated
    colors = {
        'A': '#2E8B57', # SeaGreen
        'B': '#3CB371', # MediumSeaGreen
        'C': '#9ACD32', # YellowGreen
        'D': '#FFD700', # Gold
        'E': '#FF8C00', # DarkOrange
        'F': '#FF4500', # OrangeRed
        'G': '#8B0000'  # DarkRed
    }
    
    
    if isinstance(value, str):
        return colors.get(value.upper(), '#808080') # Grey if unknown
    
    return '#808080'

def format_value(value, unit=''):
    """
    Smart formatting:
    - If value > 100 -> Round to integer
    - If value < 10 -> 2 decimals
    - If value ends in .0 -> Remove decimal
    """
    if value is None or value == '':
        return "-"
        
    try:
        val_float = float(value)
        
        # Check if it's effectively an integer
        if val_float.is_integer():
            formatted = f"{int(val_float):_}".replace('_', ' ')
        elif val_float > 100:
             formatted = f"{int(round(val_float)):_}".replace('_', ' ')
        elif val_float < 10:
             formatted = f"{val_float:.2f}"
        else:
             formatted = f"{val_float:.1f}"
             
        # Add unit if provided
        result = f"{formatted} {unit}" if unit else formatted
        
        # French Localization: replace dot with comma for display
        return result.replace('.', ',')
        
    except (ValueError, TypeError):
        return str(value)
