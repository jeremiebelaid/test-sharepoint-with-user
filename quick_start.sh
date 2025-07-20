#!/bin/bash

echo "🚀 Démarrage rapide - Test SharePoint avec User Assigned Identity"
echo "================================================================"

# Vérification de la configuration
echo "🔍 Vérification de la configuration..."
python test_config.py

echo ""
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo ""
echo "🔐 Test d'authentification locale..."
python test_local_auth.py

echo ""
echo "🌐 Test complet avec le script principal..."
echo "   (Utilisez Ctrl+C pour arrêter si nécessaire)"
python sharepoint_auth.py

echo ""
echo "✅ Tests terminés !"
echo ""
echo "🚀 Pour déployer sur Azure:"
echo "   ./deploy.sh"
echo ""
echo "🔧 Pour vérifier la configuration Azure:"
echo "   ./azure-config.sh" 