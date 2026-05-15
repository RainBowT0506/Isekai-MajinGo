import os
import zipfile
import json
import shutil
from pathlib import Path

def unzip_recursive(zip_path, extract_to):
    """Unzips a file and recursively unzips any zip files found inside."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Check for nested zips
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                if file.lower().endswith('.zip'):
                    nested_zip_path = os.path.join(root, file)
                    # Create a folder for the nested zip
                    nested_folder_name = "".join([c for c in file[:-4] if c.isalnum() or c in (' ', '_', '-')]).rstrip()
                    nested_extract_to = os.path.join(root, nested_folder_name)
                    
                    print(f"Extracting nested zip: {nested_zip_path}")
                    unzip_recursive(nested_zip_path, nested_extract_to)
                    # Optionally remove the nested zip after extraction to save space
                    # os.remove(nested_zip_path)
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")

def analyze_dictionaries(base_path):
    """Finds all index.json files and extracts dictionary metadata."""
    dictionaries = []
    for root, dirs, files in os.walk(base_path):
        if 'index.json' in files:
            index_path = os.path.join(root, 'index.json')
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    dictionaries.append({
                        'title': data.get('title', 'Unknown'),
                        'author': data.get('author', 'Unknown'),
                        'description': data.get('description', ''),
                        'revision': data.get('revision', ''),
                        'path': root
                    })
            except Exception as e:
                print(f"Error reading {index_path}: {e}")
    return dictionaries

def main():
    base_dir = '/Users/linchengyi/PycharmProjects/Isekai-MajinGo'
    assets_dir = os.path.join(base_dir, 'backend/assets')
    extract_dir = os.path.join(assets_dir, 'extracted')
    os.makedirs(extract_dir, exist_ok=True)

    # 1. Extract all zips in backend/assets/MarvNC
    marvnc_dir = os.path.join(assets_dir, 'MarvNC')
    if os.path.exists(marvnc_dir):
        for file in os.listdir(marvnc_dir):
            if file.lower().endswith('.zip'):
                zip_path = os.path.join(marvnc_dir, file)
                # Use filename as folder name (strip extension)
                folder_name = "".join([c for c in file[:-4] if c.isalnum() or c in (' ', '_', '-')]).rstrip()
                target_path = os.path.join(extract_dir, folder_name)
                
                if not os.path.exists(target_path):
                    print(f"Extracting {zip_path} to {target_path}...")
                    unzip_recursive(zip_path, target_path)

    # 2. Analyze all dictionaries (including already unzipped ones)
    all_dicts = analyze_dictionaries(assets_dir)
    
    # 3. Generate Report
    report_path = os.path.join(assets_dir, 'dictionary_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Japanese Dictionary Assets Report\n\n")
        f.write(f"Total Dictionaries Found: {len(all_dicts)}\n\n")
        f.write("| Title | Author | Revision | Path |\n")
        f.write("|-------|--------|----------|------|\n")
        for d in all_dicts:
            rel_path = os.path.relpath(d['path'], assets_dir)
            f.write(f"| {d['title']} | {d['author']} | {d['revision']} | `{rel_path}` |\n")
        
        f.write("\n## Detailed Descriptions\n\n")
        for d in all_dicts:
            f.write(f"### {d['title']}\n")
            f.write(f"- **Author:** {d['author']}\n")
            f.write(f"- **Revision:** {d['revision']}\n")
            f.write(f"- **Path:** `{d['path']}`\n")
            f.write(f"- **Description:** {d['description']}\n\n")

    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    main()
