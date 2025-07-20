#!/usr/bin/env python3
"""
Script simple pour écrire un fichier dans SharePoint
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')


def write_file_simple():
    """Écrit un fichier de test dans SharePoint de manière simple"""
    print("📝 Écriture simple d'un fichier dans SharePoint")
    print("=" * 50)
    
    try:
        from azure.identity import AzureCliCredential
        from office365.sharepoint.client_context import ClientContext
        
        # Configuration
        site_url = os.getenv("SHAREPOINT_SITE_URL")
        folder_path = os.getenv("SHAREPOINT_FOLDER_PATH")
        
        if not site_url:
            print("❌ URL SharePoint non configurée")
            return False
            
        print(f"🌐 Site SharePoint: {site_url}")
        print(f"📁 Dossier de destination: {folder_path}")
        print()
        
        # Obtention du credential
        print("🔐 Obtention du credential Azure CLI...")
        credential = AzureCliCredential()
        
        # Obtention du token
        print("🎫 Obtention du token...")
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Token obtenu avec succès")
        
        # Création du contexte SharePoint
        print("🌐 Création du contexte SharePoint...")
        ctx = ClientContext(site_url).with_credentials(credential)
        
        # Test de connexion
        web = ctx.web
        ctx.load(web)
        ctx.execute_query()
        print(f"✅ Connecté au site: {web.title}")
        
        # Création du contenu du fichier
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_content = f"""Test d'écriture SharePoint - Simple
===============================

Fichier créé le: {timestamp}
Utilisateur: Identité personnelle (Azure CLI)
Site SharePoint: {site_url}
Dossier: {folder_path}

Ce fichier a été créé pour tester l'accès en écriture à SharePoint
avec l'identité personnelle.

Test réussi ! 🎉
"""
        
        # Nom du fichier
        filename = f"test-simple-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        print(f"\n📝 Création du fichier: {filename}")
        
        # Tentative d'écriture dans Shared Documents
        print("📁 Tentative d'écriture dans Shared Documents...")
        try:
            # Récupération du dossier Shared Documents
            folder = ctx.web.get_folder_by_server_relative_url("Shared Documents")
            ctx.load(folder)
            ctx.execute_query()
            print(f"✅ Dossier trouvé: {folder.name}")
            
            # Upload du fichier
            folder.upload_file(filename, file_content.encode('utf-8'))
            ctx.execute_query()
            print("✅ Fichier créé avec succès dans Shared Documents !")
            
            # Tentative d'écriture dans le dossier spécifique
            if folder_path:
                print(f"\n📁 Tentative d'écriture dans le dossier spécifique...")
                try:
                    # Récupération du dossier spécifique
                    specific_folder = ctx.web.get_folder_by_server_relative_url(folder_path)
                    ctx.load(specific_folder)
                    ctx.execute_query()
                    print(f"✅ Dossier spécifique trouvé: {specific_folder.name}")
                    
                    # Upload dans le dossier spécifique
                    specific_folder.upload_file(filename, file_content.encode('utf-8'))
                    ctx.execute_query()
                    print("✅ Fichier créé dans le dossier spécifique !")
                    
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'écriture dans le dossier spécifique: {str(e)}")
                    print("   Le dossier n'existe peut-être pas encore")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'écriture: {str(e)}")
            return False
        
    except ImportError as e:
        print(f"❌ [red]Module manquant: {str(e)}[/red]")
        print("💡 Installez les dépendances avec: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ [red]Erreur: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    success = write_file_simple()
    if success:
        print("\n🎉 Test d'écriture réussi !")
        print("Vous pouvez maintenant vérifier le fichier dans SharePoint.")
    else:
        print("\n❌ Test d'écriture échoué.")
    sys.exit(0 if success else 1) 