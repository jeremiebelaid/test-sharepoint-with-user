#!/usr/bin/env python3
"""
Script optimisé pour tester l'écriture SharePoint DDASYS
Utilise directement les IDs extraits avec l'API Microsoft Graph
"""

import os
import requests
from datetime import datetime
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')


def test_sharepoint_with_ids():
    """Test d'écriture SharePoint en utilisant les IDs extraits."""
    print("🚀 Test SharePoint DDASYS avec IDs extraits")
    print("=" * 50)
    
    # Configuration depuis config.env
    site_id = os.getenv("SHAREPOINT_SITE_ID")
    drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
    folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "")
    
    if not site_id or not drive_id:
        print("❌ IDs SharePoint non configurés dans config.env")
        print("💡 Exécutez d'abord: python extract_sharepoint_ids_ddasys.py")
        return False
    
    print(f"📍 Site ID: {site_id[:50]}...")
    print(f"📁 Drive ID: {drive_id[:50]}...")
    print(f"📂 Folder: {folder_path or 'Racine du drive'}")
    
    try:
        # 1. Authentification
        print("\n1. Authentification Azure CLI...")
        credential = AzureCliCredential()
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Token Microsoft Graph obtenu")
        
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        # 2. Vérification accès au site
        print("\n2. Vérification accès au site...")
        site_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        response = requests.get(site_url, headers=headers)
        
        if response.status_code == 200:
            site_info = response.json()
            print(f"✅ Site accessible: {site_info.get('displayName')}")
        else:
            print(f"❌ Erreur accès site: {response.status_code}")
            return False
        
        # 3. Vérification accès au drive
        print("\n3. Vérification accès au drive...")
        drive_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
        response = requests.get(drive_url, headers=headers)
        
        if response.status_code == 200:
            drive_info = response.json()
            print(f"✅ Drive accessible: {drive_info.get('name')}")
        else:
            print(f"❌ Erreur accès drive: {response.status_code}")
            return False
        
        # 4. Test d'écriture
        print("\n4. Test d'écriture dans le drive...")
        
        # Contenu du fichier de test
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        content = f"""Test d'écriture SharePoint DDASYS avec IDs extraits
Timestamp: {timestamp}
Site ID: {site_id}
Drive ID: {drive_id}
Folder: {folder_path}

Ce fichier confirme que l'écriture fonctionne avec les IDs extraits.
Test effectué avec Azure CLI et l'API Microsoft Graph.
"""
        
        filename = f"test_with_ids_{timestamp}.txt"
        
        # Construire le chemin de destination
        if folder_path and folder_path.strip():
            # Upload dans un dossier spécifique
            clean_folder = folder_path.strip().strip('/')
            upload_path = f"/{clean_folder}/{filename}"
            print(f"   📝 Upload vers: {clean_folder}/{filename}")
        else:
            # Upload à la racine
            upload_path = f"/{filename}"
            print(f"   📝 Upload vers la racine: {filename}")
        
        # API Graph pour upload
        upload_url = (f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
                      f"/root:{upload_path}:/content")
        
        upload_headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'text/plain; charset=utf-8'
        }
        
        print(f"   🌐 URL API: {upload_url}")
        
        # Tentative d'upload
        response = requests.put(
            upload_url, 
            data=content.encode('utf-8'), 
            headers=upload_headers
        )
        
        if response.status_code in [200, 201]:
            file_info = response.json()
            file_url = file_info.get('webUrl', 'URL non disponible')
            print(f"   🎉 Fichier créé avec succès!")
            print(f"   🔗 URL SharePoint: {file_url}")
            print(f"   📏 Taille: {file_info.get('size', 0)} bytes")
            return True
        else:
            print(f"   ❌ Erreur upload: {response.status_code}")
            print(f"   📝 Réponse: {response.text}")
            
            # Si erreur dossier, essayer de créer le dossier d'abord
            if response.status_code == 404 and folder_path:
                print(f"   🔧 Tentative de création du dossier...")
                return create_folder_and_retry(
                    drive_id, folder_path, filename, content, headers
                )
        
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False


def create_folder_and_retry(drive_id, folder_path, filename, content, headers):
    """Crée le dossier s'il n'existe pas et retry l'upload."""
    try:
        # Séparer les composants du chemin
        path_parts = [p.strip() for p in folder_path.split('/') if p.strip()]
        
        print(f"   📁 Création du chemin: {' > '.join(path_parts)}")
        
        # Créer chaque dossier dans le chemin
        current_path = ""
        for part in path_parts:
            if current_path:
                parent_path = f"/root:/{current_path}"
            else:
                parent_path = "/root"
            
            # Vérifier si le dossier existe
            check_url = (f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
                        f"{parent_path}/children")
            
            response = requests.get(check_url, headers=headers)
            
            folder_exists = False
            if response.status_code == 200:
                items = response.json().get('value', [])
                folder_exists = any(
                    item.get('name') == part and 'folder' in item 
                    for item in items
                )
            
            if not folder_exists:
                # Créer le dossier
                create_url = (f"https://graph.microsoft.com/v1.0/drives/"
                             f"{drive_id}{parent_path}/children")
                
                folder_data = {
                    "name": part,
                    "folder": {},
                    "@microsoft.graph.conflictBehavior": "rename"
                }
                
                response = requests.post(
                    create_url, 
                    json=folder_data, 
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    print(f"   ✅ Dossier créé: {part}")
                else:
                    print(f"   ⚠️  Erreur création dossier {part}: "
                          f"{response.status_code}")
            else:
                print(f"   ✅ Dossier existe: {part}")
            
            # Mettre à jour le chemin courant
            if current_path:
                current_path += f"/{part}"
            else:
                current_path = part
        
        # Retry l'upload après création du dossier
        print(f"   🔄 Nouvelle tentative d'upload...")
        upload_path = f"/{folder_path.strip().strip('/')}/{filename}"
        upload_url = (f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
                      f"/root:{upload_path}:/content")
        
        upload_headers = {
            'Authorization': headers['Authorization'],
            'Content-Type': 'text/plain; charset=utf-8'
        }
        
        response = requests.put(
            upload_url, 
            data=content.encode('utf-8'), 
            headers=upload_headers
        )
        
        if response.status_code in [200, 201]:
            file_info = response.json()
            file_url = file_info.get('webUrl', 'URL non disponible')
            print(f"   🎉 Fichier créé après création dossier!")
            print(f"   🔗 URL SharePoint: {file_url}")
            return True
        else:
            print(f"   ❌ Erreur upload après création dossier: "
                  f"{response.status_code}")
            print(f"   📝 Réponse: {response.text}")
            return False
        
    except Exception as e:
        print(f"   ❌ Erreur création dossier: {e}")
        return False


def main():
    """Fonction principale."""
    success = test_sharepoint_with_ids()
    
    if success:
        print("\n🎉 SUCCESS! L'écriture fonctionne avec les IDs extraits!")
        print("✅ Votre configuration SharePoint est opérationnelle.")
        print("🚀 Vous pouvez maintenant tester avec User Assigned Identity.")
    else:
        print("\n❌ L'écriture a échoué.")
        print("🔍 Vérifiez :")
        print("   - Les IDs dans config.env")
        print("   - Vos permissions SharePoint")
        print("   - Votre authentification Azure CLI")


if __name__ == "__main__":
    main() 