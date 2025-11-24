#!/usr/bin/env python3
"""
Script de téléchargement du dataset MovieLens 20M
Télécharge et extrait automatiquement le dataset depuis GroupLens
"""
import os
import sys
import requests
import zipfile
from pathlib import Path

# Configuration
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-20m.zip"
DATA_DIR = Path("./data/ml-20m")
ZIP_FILE = Path("./data/ml-20m.zip")

def download_file(url, destination, chunk_size=8192):
    """Télécharge un fichier avec barre de progression."""
    print(f"📥 Téléchargement depuis {url}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r  Progression: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB)", end='')
    
    print("\n✅ Téléchargement terminé!")

def extract_zip(zip_path, extract_to):
    """Extrait un fichier ZIP."""
    print(f"📦 Extraction de {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    print("✅ Extraction terminée!")

def move_files_to_target(source_dir, target_dir):
    """Déplace les fichiers CSV du sous-dossier ml-20m vers le dossier cible."""
    ml20m_subdir = source_dir / "ml-20m"
    
    if not ml20m_subdir.exists():
        print(f"⚠️  Le sous-dossier {ml20m_subdir} n'existe pas")
        return
    
    print(f"📁 Déplacement des fichiers vers {target_dir}...")
    
    # Créer le dossier cible s'il n'existe pas
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Déplacer tous les fichiers CSV
    for file in ml20m_subdir.glob("*.csv"):
        target_file = target_dir / file.name
        file.rename(target_file)
        print(f"  ✓ {file.name}")
    
    # Déplacer aussi README.txt si présent
    readme = ml20m_subdir / "README.txt"
    if readme.exists():
        readme.rename(target_dir / "README.txt")
        print(f"  ✓ README.txt")
    
    # Supprimer le sous-dossier vide
    if ml20m_subdir.exists():
        ml20m_subdir.rmdir()
    
    print("✅ Fichiers déplacés!")

def main():
    """Fonction principale."""
    print("🎬 Téléchargement du dataset MovieLens 20M")
    print("=" * 60)
    
    # Vérifier si les données existent déjà
    if DATA_DIR.exists() and any(DATA_DIR.glob("*.csv")):
        print(f"✅ Le dataset existe déjà dans {DATA_DIR}")
        print("   Fichiers trouvés:")
        for csv_file in sorted(DATA_DIR.glob("*.csv")):
            size_mb = csv_file.stat().st_size / 1024 / 1024
            print(f"     - {csv_file.name} ({size_mb:.1f} MB)")
        
        response = input("\n⚠️  Voulez-vous re-télécharger? (y/N): ")
        if response.lower() != 'y':
            print("Annulé.")
            return 0
    
    # Créer le dossier data s'il n'existe pas
    DATA_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Télécharger le fichier ZIP
        download_file(MOVIELENS_URL, ZIP_FILE)
        
        # Extraire le ZIP
        extract_zip(ZIP_FILE, DATA_DIR.parent)
        
        # Déplacer les fichiers vers le bon dossier
        move_files_to_target(DATA_DIR.parent, DATA_DIR)
        
        # Supprimer le fichier ZIP
        print(f"🗑️  Suppression de {ZIP_FILE}...")
        ZIP_FILE.unlink()
        
        print("\n" + "=" * 60)
        print("✅ Dataset MovieLens 20M prêt!")
        print(f"📁 Emplacement: {DATA_DIR.absolute()}")
        print("\nFichiers disponibles:")
        for csv_file in sorted(DATA_DIR.glob("*.csv")):
            size_mb = csv_file.stat().st_size / 1024 / 1024
            print(f"  - {csv_file.name} ({size_mb:.1f} MB)")
        
        print("\n🚀 Vous pouvez maintenant lancer: docker compose up --build -d")
        return 0
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
