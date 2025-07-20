#!/usr/bin/env python3
"""
Script de test rapide pour vérifier la configuration SharePoint
"""
import os
from dotenv import load_dotenv

def test_configuration():
    """Test de la configuration SharePoint"""
    print("🔍 Test de la configuration SharePoint")
    print("=" * 50)
    
    # Chargement des variables d'environnement
    load_dotenv('.env')
    
    # Vérification des variables
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    folder_path = os.getenv("SHAREPOINT_FOLDER_PATH")
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY")
    
    print(f"🌐 Site SharePoint: {site_url}")
    print(f"📁 Dossier de test: {folder_path}")
    print(f"🔐 Managed Identity: {use_managed_identity}")
    
    # Vérification de l'URL
    if site_url and "ddasys.sharepoint.com" in site_url:
        print("✅ URL SharePoint valide")
    else:
        print("❌ URL SharePoint invalide")
    
    # Vérification du dossier
    if folder_path and "Test-user-assigned-identity" in folder_path:
        print("✅ Dossier de test configuré")
    else:
        print("❌ Dossier de test non configuré")
    
    print("\n📋 URL complète du dossier:")
    print(f"{site_url}/{folder_path}")
    
    print("\n🚀 Pour tester l'authentification:")
    print("python sharepoint_auth.py")

if __name__ == "__main__":
    test_configuration() 