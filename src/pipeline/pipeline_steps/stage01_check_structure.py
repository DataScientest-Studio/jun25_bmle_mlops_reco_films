#!/usr/bin/env python3

from pipeline.check_structure_pipeline import check_structure_pipeline

if __name__ == "__main__":
    # Définir les dossiers à vérifier/créer
    folders_to_check = [
        "data/logs",
        "data/temp",
        "output/reports"
    ]

    # Définir les fichiers à vérifier/créer
    files_to_check = [
        "data/config/settings.json",
        "output/reports/summary.txt"
    ]

    # Appel de la fonction pour vérifier/créer les fichiers et dossiers
    check_structure_pipeline(files=files_to_check, folders=folders_to_check)
