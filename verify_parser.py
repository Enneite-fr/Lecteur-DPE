import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.parser import parse_dpe_file

# File path
xml_file = "2508E0729579F.xml"

if os.path.exists(xml_file):
    print(f"Parsing {xml_file}...")
    data = parse_dpe_file(xml_file)
    
    if 'error' in data:
        print(f"Error: {data['error']}")
    else:
        print("Scucces!")
        print(f"Générateur: {data.get('chauffage_generateur')}")
        print(f"Émetteur: {data.get('chauffage_emetteur')}")
else:
    print(f"File {xml_file} not found.")
