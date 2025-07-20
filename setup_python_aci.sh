#!/bin/bash
"""
Script d'installation Python et dépendances pour l'ACI
À exécuter une fois connecté dans le container ACI
"""

set -e

echo "🐍 Installation de Python et dépendances pour test SharePoint"
echo "============================================================="

# 1. Mise à jour du système
echo -e "\n📦 Mise à jour du système..."
apk update
apk add --no-cache python3 python3-dev py3-pip gcc musl-dev libffi-dev

# 2. Installation des dépendances Python
echo -e "\n🔧 Installation des dépendances Python..."
pip3 install --no-cache-dir \
    azure-identity \
    requests \
    urllib3

# 3. Vérification de l'installation
echo -e "\n✅ Vérification de l'installation..."
python3 --version
python3 -c "import azure.identity; print('✅ azure-identity installé')"
python3 -c "import requests; print('✅ requests installé')"

# 4. Création du dossier de travail
echo -e "\n📁 Création du dossier de travail..."
mkdir -p /app
cd /app

# 5. Informations de l'environnement
echo -e "\n📋 Informations de l'environnement:"
echo "   Python: $(python3 --version)"
echo "   Pip: $(pip3 --version)"
echo "   Working Directory: $(pwd)"
echo "   User: $(whoami)"

# 6. Test des variables d'environnement
echo -e "\n🔍 Variables d'environnement Azure:"
echo "   AZURE_CLIENT_ID: ${AZURE_CLIENT_ID:0:20}..."
echo "   SHAREPOINT_SITE_ID: ${SHAREPOINT_SITE_ID:0:30}..."
echo "   SHAREPOINT_DRIVE_ID: ${SHAREPOINT_DRIVE_ID:0:30}..."
echo "   SHAREPOINT_FOLDER_PATH: ${SHAREPOINT_FOLDER_PATH}"

echo -e "\n🎉 Installation terminée!"
echo "💡 Vous pouvez maintenant copier et exécuter votre script de test SharePoint" 