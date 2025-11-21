import os

def check_structure_pipeline(files=None, folders=None):
    """
    Vérifie et crée automatiquement plusieurs fichiers et dossiers.
    
    Args:
        files (list[str]): Liste de chemins de fichiers à vérifier/créer.
        folders (list[str]): Liste de chemins de dossiers à vérifier/créer.
    
    Retourne toujours True pour éviter les blocages dans un pipeline.
    """
    # Gestion des dossiers
    if folders:
        for folder_path in folders:
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"Folder '{folder_path}' created automatically.")
            else:
                print(f"Folder '{folder_path}' already exists.")

    # Gestion des fichiers
    if files:
        for file_path in files:
            if os.path.isfile(file_path):
                print(f"File '{file_path}' exists. Will be overwritten automatically if needed.")
            else:
                # Créer le dossier parent si nécessaire
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Créer le fichier vide
                open(file_path, 'a').close()
                print(f"File '{file_path}' created automatically.")
    
    return True


# Bloc d'execution directe
if __name__ == "__main__":
    folders_to_check = [
        "data/logs",
        "data/temp",
        "output/reports"
    ]
    files_to_check = [
        "data/config/settings.json",
        "output/reports/summary.txt"
    ]

    check_structure_pipeline(files=files_to_check, folders=folders_to_check)
