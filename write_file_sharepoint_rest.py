#!/usr/bin/env python3
"""
Script pour écrire un fichier dans SharePoint avec l'API REST SharePoint
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')


def write_file_sharepoint_rest():
    """Écrit un fichier de test dans SharePoint avec l'API REST"""
    print("📝 Écriture d'un fichier dans SharePoint avec API REST")
    print("=" * 60)
    
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
        
        # Obtention du token pour SharePoint
        print("🎫 Obtention du token SharePoint...")
        token = credential.get_token("https://ddasys.sharepoint.com/.default")
        print("✅ Token obtenu avec succès")
        
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json;odata=verbose',
            'Accept': 'application/json;odata=verbose'
        }
        
        # Test d'accès au site
        print("🌐 Test d'accès au site...")
        site_response = requests.get(f"{site_url}/_api/web", headers=headers)
        
        if site_response.status_code == 200:
            site_info = site_response.json()
            web_info = site_info.get('d', {})
            print(f"✅ Site accessible: {web_info.get('Title', 'N/A')}")
            print(f"📍 URL: {web_info.get('Url', 'N/A')}")
        else:
            print(f"❌ Erreur d'accès au site: {site_response.status_code}")
            return False
        
        # Création du contenu du fichier
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_content = f"""Test d'écriture SharePoint - API REST
=====================================

Fichier créé le: {timestamp}
Utilisateur: Identité personnelle (Azure CLI)
Site SharePoint: {site_url}
Dossier: {folder_path}

Ce fichier a été créé pour tester l'accès en écriture à SharePoint
avec l'API REST SharePoint et l'identité personnelle.

Test réussi ! 🎉
"""
        
        # Nom du fichier
        filename = f"test-rest-api-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        print(f"\n📝 Création du fichier: {filename}")
        
        # Tentative d'écriture dans le dossier racine
        print("📁 Tentative d'écriture dans le dossier racine...")
        
        # URL pour l'upload de fichier
        upload_url = f"{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents')/Files/add(url='{filename}',overwrite=true)"
        
        upload_headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json;odata=verbose',
            'Accept': 'application/json;odata=verbose',
            'X-RequestDigest': 'form digest value'  # Sera rempli automatiquement
        }
        
        # Obtention du form digest
        digest_response = requests.post(f"{site_url}/_api/contextinfo", headers=headers)
        if digest_response.status_code == 200:
            digest_info = digest_response.json()
            form_digest = digest_info.get('d', {}).get('GetContextWebInformation', {}).get('FormDigestValue')
            upload_headers['X-RequestDigest'] = form_digest
            print("✅ Form digest obtenu")
        else:
            print("⚠️ Impossible d'obtenir le form digest")
        
        # Upload du fichier
        upload_response = requests.post(
            upload_url,
            data=file_content.encode('utf-8'),
            headers=upload_headers
        )
        
        if upload_response.status_code in [200, 201]:
            print("✅ Fichier créé avec succès dans Shared Documents !")
            
            # Tentative d'écriture dans le dossier spécifique
            if folder_path:
                print(f"\n📁 Tentative d'écriture dans le dossier spécifique...")
                try:
                    # Création du dossier si nécessaire
                    folder_url = f"{site_url}/_api/web/folders"
                    folder_data = {
                        '__metadata': {'type': 'SP.Folder'},
                        'ServerRelativeUrl': f"Shared Documents/{folder_path}"
                    }
                    
                    folder_response = requests.post(
                        folder_url,
                        json=folder_data,
                        headers=upload_headers
                    )
                    
                    if folder_response.status_code in [200, 201, 409]:  # 409 = dossier existe déjà
                        print("✅ Dossier accessible")
                        
                        # Upload dans le dossier spécifique
                        specific_upload_url = f"{site_url}/_api/web/GetFolderByServerRelativeUrl('Shared Documents/{folder_path}')/Files/add(url='{filename}',overwrite=true)"
                        
                        specific_upload_response = requests.post(
                            specific_upload_url,
                            data=file_content.encode('utf-8'),
                            headers=upload_headers
                        )
                        
                        if specific_upload_response.status_code in [200, 201]:
                            print("✅ Fichier créé dans le dossier spécifique !")
                        else:
                            print(f"⚠️ Erreur lors de l'écriture dans le dossier spécifique: {specific_upload_response.status_code}")
                    else:
                        print(f"⚠️ Erreur d'accès au dossier spécifique: {folder_response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'écriture dans le dossier spécifique: {str(e)}")
            
            return True
        else:
            print(f"❌ Erreur lors de la création du fichier: {upload_response.status_code}")
            print(f"   Réponse: {upload_response.text}")
            return False
        
    except ImportError as e:
        print(f"❌ [red]Module manquant: {str(e)}[/red]")
        print("💡 Installez les dépendances avec: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ [red]Erreur: {str(e)}[/red]")
        return False


if __name__ == "__main__":
    success = write_file_sharepoint_rest()
    if success:
        print("\n🎉 Test d'écriture réussi !")
        print("Vous pouvez maintenant vérifier le fichier dans SharePoint.")
    else:
        print("\n❌ Test d'écriture échoué.")
    sys.exit(0 if success else 1) 