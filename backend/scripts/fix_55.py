import os
from mana_library import LibraryMaster

def fix_55():
    master = LibraryMaster()
    target_zips = [
        'assets/FooSoft/innocent_corpus.zip', 
        'assets/FooSoft/kanjium_pitch_accents.zip', 
        'assets/scriptin/jmdict-eng-3.6.2+20260504132921.json.zip', 
        'assets/scriptin/kanjidic2-en-3.6.2+20260504132921.json.zip', 
        'assets/scriptin/jmnedict-all-3.6.2+20260504132921.json.zip', 
        'assets/scriptin/jmdict-examples-eng-3.6.2+20260504132921.json.zip', 
        'assets/MarvNC/MarvNC)-20260508T012345Z-3-001.zip', 
        'assets/MarvNC/MarvNC)-20260508T012345Z-3-003.zip', 
        'assets/MarvNC/MarvNC)-20260508T012345Z-3-002.zip', 
        'assets/MarvNC/JP Ressources-20260508T015850Z-3-001.zip', 
        'assets/MarvNC/JP Ressources-20260508T015850Z-3-002.zip', 
        'assets/MarvNC/JP Ressources-20260508T015850Z-3-003.zip', 
        'assets/MarvNC/MarvNC)-20260508T012345Z-3-004.zip', 
        'assets/MarvNC/辭典-20260508T020417Z-3-002.zip', 
        'assets/MarvNC/辭典-20260508T020417Z-3-003.zip', 
        'assets/MarvNC/1nip86.zip', 
        'assets/MarvNC/辭典-20260508T020417Z-3-001.zip'
    ]
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Starting targeted fix for {len(target_zips)} root zips containing the 55 anomalies...")
    for tz in target_zips:
        full_path = os.path.join(BASE_DIR, tz)
        if os.path.exists(full_path):
            print(f"Processing: {tz}")
            master.decipher_and_bind(full_path)
        else:
            print(f"Not found: {tz}")

if __name__ == "__main__":
    fix_55()
