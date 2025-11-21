#!/bin/bash

# Script pour creer un environnement virtuel Python et installer les dependances

echo "Creation de l'environnement virtuel..."
python3 -m venv venv

echo "Activation de l'environnement virtuel..."
source venv/bin/activate

echo "Mise a jour de pip..."
pip install --upgrade pip

echo "Installation des dependances..."
pip install -r requirements.txt

echo "Environnement virtuel cree et dependances installees."
echo "Pour activer l'environnement: source venv/bin/activate"

