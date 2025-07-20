#!/usr/bin/env python3
"""
Script de test local pour l'authentification SharePoint
Utilise AzureCliCredential pour le développement local
"""
import os
import sys
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')


def test_local_authentication():
    """Test d'authentification locale avec AzureCliCredential"""
    print("🔍 Test d'authentification locale SharePoint")
    print("=" * 60)
    
    try:
        # Import des modules nécessaires
        from azure.identity import AzureCliCredential
        from office365.sharepoint.client_context import ClientContext
        
        # Configuration
        site_url = os.getenv("SHAREPOINT_SITE_URL")
        folder_path = os.getenv("SHAREPOINT_FOLDER_PATH")
        
        if not site_url:
            print("❌ URL SharePoint non configurée")
            return False
            
        print(f"🌐 Site SharePoint: {site_url}")
        print(f"📁 Dossier de test: {folder_path}")
        print()
        
        # Test de l'obtention du credential
        print("🔐 Test de l'obtention du credential...")
        credential = AzureCliCredential()
        
        # Test de l'obtention du token
        print("🎫 Test de l'obtention du token...")
        token = credential.get_token("https://graph.microsoft.com/.default")
        print(f"✅ Token obtenu avec succès (expire dans "
              f"{token.expires_on} secondes)")
        
        # Test de la connexion SharePoint
        print("🌐 Test de la connexion SharePoint...")
        ctx = ClientContext(site_url).with_credentials(credential)
        
        # Test de récupération des informations du site
        web = ctx.web
        ctx.load(web)
        ctx.execute_query()
        
        print(f"✅ Connecté avec succès au site: {web.title}")
        print(f"📍 URL: {web.url}")
        
        # Test d'accès au dossier
        if folder_path:
            print(f"\n📁 Test d'accès au dossier: {folder_path}")
            try:
                folder = ctx.web.get_folder_by_server_relative_url(
                    folder_path)
                ctx.load(folder)
                ctx.execute_query()
                print(f"✅ Dossier trouvé: {folder.name}")
                
                # Liste des fichiers
                files = folder.files
                ctx.load(files)
                ctx.execute_query()
                print(f"📄 Nombre de fichiers trouvés: {len(files)}")
                
                if len(files) > 0:
                    print("📋 Fichiers dans le dossier:")
                    for file in files:
                        print(f"   - {file.name} ({file.length} bytes)")
                
            except Exception as e:
                print(f"⚠️  Erreur d'accès au dossier: {str(e)}")
                print("   Cela peut être normal si le dossier n'existe pas")
        
        print("\n✅ [bold green]Test d'authentification locale réussi !"
              "[/bold green]")
        print("\n🚀 Pour tester avec Managed Identity sur Azure:")
        print("   ./deploy.sh")
        
        return True
        
    except ImportError as e:
        print(f"❌ [red]Module manquant: {str(e)}[/red]")
        print("💡 Installez les dépendances avec: pip install -r "
              "requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ [red]Erreur d'authentification: {str(e)}[/red]")
        print("\n💡 Solutions possibles:")
        print("   1. Connectez-vous à Azure: az login")
        print("   2. Vérifiez vos permissions SharePoint")
        print("   3. Utilisez un environnement virtuel")
        return False


if __name__ == "__main__":
    success = test_local_authentication()
    sys.exit(0 if success else 1) 