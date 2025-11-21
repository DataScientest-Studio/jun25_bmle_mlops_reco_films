@echo off

REM Script pour creer un environnement virtuel Python et installer les dependances

echo Creation de l'environnement virtuel...
python -m venv venv

echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo Mise a jour de pip...
python -m pip install --upgrade pip

echo Installation des dependances...
pip install -r requirements.txt

echo Environnement virtuel cree et dependances installees.
echo Pour activer l'environnement: venv\Scripts\activate

