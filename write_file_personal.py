#!/usr/bin/env python3
"""
Script pour écrire un fichier dans SharePoint avec l'identité personnelle
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')


def write_file_to_sharepoint():
    """Écrit un fichier de test dans SharePoint avec l'identité personnelle"""
    print("📝 Écriture d'un fichier dans SharePoint avec identité personnelle")
    print("=" * 70)
    
    try:
        from azure.identity import AzureCliCredential
        import requests
        
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
        
        # Obtention du token pour Microsoft Graph
        print("🎫 Obtention du token Microsoft Graph...")
        token = credential.get_token("https://graph.microsoft.com/.default")
        print(f"✅ Token obtenu avec succès")
        
        # Extraction des informations du site
        site_parts = site_url.split('/')
        if len(site_parts) >= 5:
            tenant = site_parts[2]  # tenant.sharepoint.com
            site_name = site_parts[4]  # sites/site-name
        else:
            print("❌ Format d'URL SharePoint invalide")
            return False
        
        print(f"🏢 Tenant: {tenant}")
        print(f"🌐 Site: {site_name}")
        
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        # Récupération de l'ID du site
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{tenant}:/sites/{site_name}"
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Erreur d'accès au site: {response.status_code}")
            return False
            
        site_info = response.json()
        site_id = site_info.get('id')
        print(f"✅ Site trouvé: {site_info.get('displayName')}")
        print(f"📍 ID du site: {site_id}")
        
        # Création du contenu du fichier
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_content = f"""Test d'écriture SharePoint - Identité Personnelle
===============================================

Fichier créé le: {timestamp}
Utilisateur: Identité personnelle (Azure CLI)
Site SharePoint: {site_url}
Dossier: {folder_path}

Ce fichier a été créé pour tester l'accès en écriture à SharePoint
avec l'identité personnelle avant de tester avec User Assigned Identity.

Informations du site:
- Nom: {site_info.get('displayName')}
- URL: {site_info.get('webUrl')}
- ID: {site_id}

Test réussi ! 🎉
"""
        
        # Nom du fichier
        filename = f"test-personal-identity-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        print(f"\n📝 Création du fichier: {filename}")
        
        # Écriture du fichier dans le dossier racine du site
        # On utilise d'abord le drive principal du site
        drive_url = f"{graph_url}/drive"
        drive_response = requests.get(drive_url, headers=headers)
        
        if drive_response.status_code == 200:
            drive_info = drive_response.json()
            drive_id = drive_info.get('id')
            print(f"✅ Drive trouvé: {drive_info.get('name')}")
            
            # Upload du fichier
            upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{filename}:/content"
            
            upload_headers = {
                'Authorization': f'Bearer {token.token}',
                'Content-Type': 'text/plain'
            }
            
            upload_response = requests.put(
                upload_url, 
                data=file_content.encode('utf-8'),
                headers=upload_headers
            )
            
            if upload_response.status_code in [200, 201]:
                file_info = upload_response.json()
                print(f"✅ Fichier créé avec succès !")
                print(f"📄 Nom: {file_info.get('name')}")
                print(f"📏 Taille: {file_info.get('size')} bytes")
                print(f"🔗 URL: {file_info.get('webUrl')}")
                
                # Tentative d'écriture dans le dossier spécifique
                if folder_path:
                    print(f"\n📁 Tentative d'écriture dans le dossier spécifique...")
                    try:
                        # Recherche du dossier
                        folder_upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}/{filename}:/content"
                        
                        folder_upload_response = requests.put(
                            folder_upload_url,
                            data=file_content.encode('utf-8'),
                            headers=upload_headers
                        )
                        
                        if folder_upload_response.status_code in [200, 201]:
                            folder_file_info = folder_upload_response.json()
                            print(f"✅ Fichier créé dans le dossier spécifique !")
                            print(f"📄 Nom: {folder_file_info.get('name')}")
                            print(f"🔗 URL: {folder_file_info.get('webUrl')}")
                        else:
                            print(f"⚠️  Impossible d'écrire dans le dossier spécifique: {folder_upload_response.status_code}")
                            print(f"   Le dossier '{folder_path}' n'existe peut-être pas encore")
                            
                    except Exception as e:
                        print(f"⚠️  Erreur lors de l'écriture dans le dossier spécifique: {str(e)}")
                
                return True
            else:
                print(f"❌ Erreur lors de la création du fichier: {upload_response.status_code}")
                print(f"   Réponse: {upload_response.text}")
                return False
        else:
            print(f"❌ Erreur d'accès au drive: {drive_response.status_code}")
            return False
        
    except ImportError as e:
        print(f"❌ [red]Module manquant: {str(e)}[/red]")
        print("💡 Installez les dépendances avec: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ [red]Erreur: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    success = write_file_to_sharepoint()
    if success:
        print("\n🎉 Test d'écriture réussi !")
        print("Vous pouvez maintenant vérifier le fichier dans SharePoint.")
    else:
        print("\n❌ Test d'écriture échoué.")
    sys.exit(0 if success else 1) 