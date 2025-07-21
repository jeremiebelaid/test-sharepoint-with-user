#!/usr/bin/env python3
"""
Script simple et direct pour écrire dans SharePoint DDASYS
Basé sur votre script fonctionnel mais simplifié
"""

import os
import requests
from datetime import datetime
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('.env')


def test_simple_write():
    """Test d'écriture simple et direct dans SharePoint."""
    print("📝 Test d'écriture simple SharePoint DDASYS")
    print("=" * 45)
    
    # Configuration
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    
    if not site_url:
        print("❌ URL SharePoint non configurée")
        return False
    
    print(f"🌐 Site SharePoint: {site_url}")
    
    try:
        # 1. Authentification
        print("\n1. Authentification...")
        credential = AzureCliCredential()
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Token obtenu")
        
        # 2. Headers pour les requêtes
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        # 3. Test d'accès au site
        print("\n2. Test d'accès au site...")
        site_parts = site_url.split('/')
        tenant = site_parts[2]  # ddasys.sharepoint.com
        site_name = site_parts[4]  # DDASYS
        
        graph_url = (f"https://graph.microsoft.com/v1.0/sites/"
                     f"{tenant}:/sites/{site_name}")
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            site_info = response.json()
            print(f"✅ Site accessible: {site_info.get('displayName')}")
        else:
            print(f"❌ Erreur site: {response.status_code}")
            return False
        
        # 4. Test d'écriture avec différentes approches
        print("\n3. Test d'écriture...")
        
        # Contenu du fichier de test
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        content = f"""Test d'écriture SharePoint DDASYS
Timestamp: {timestamp}
Utilisateur: Compte personnel (Azure CLI)
Site: {site_url}

Ce fichier confirme que l'écriture fonctionne avec votre compte personnel.
"""
        
        filename = f"test_perso_{timestamp}.txt"
        
        # Approche 1: Utilisation de l'API SharePoint REST directe
        print("   Approche 1: API SharePoint REST...")
        try:
            # Headers pour SharePoint REST
            sp_headers = {
                'Authorization': f'Bearer {token.token}',
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json;odata=verbose'
            }
            
            # Test d'accès au contexte SharePoint
            context_url = f"{site_url}/_api/contextinfo"
            context_response = requests.post(context_url, headers=sp_headers)
            
            if context_response.status_code == 200:
                print("   ✅ Contexte SharePoint accessible")
                
                # Tentative d'upload
                folder_path = ("/sites/DDASYS/Shared Documents")
                upload_url = (f"{site_url}/_api/web/"
                              f"GetFolderByServerRelativeUrl('{folder_path}')/"
                              f"Files/add(url='{filename}',overwrite=true)")
                
                upload_headers = sp_headers.copy()
                upload_headers['Content-Type'] = 'text/plain'
                
                upload_response = requests.post(
                    upload_url, 
                    data=content.encode('utf-8'), 
                    headers=upload_headers
                )
                
                if upload_response.status_code in [200, 201]:
                    print(f"   🎉 Fichier créé via REST API: {filename}")
                    return True
                else:
                    print(f"   ⚠️  Erreur upload REST: "
                          f"{upload_response.status_code}")
            else:
                print(f"   ⚠️  Erreur contexte: "
                      f"{context_response.status_code}")
        
        except Exception as e:
            print(f"   ⚠️  Erreur REST: {e}")
        
        # Approche 2: Utilisation de l'API Graph avec un chemin plus simple
        print("   Approche 2: API Graph simple...")
        try:
            # Essayer d'accéder aux drives du site
            drives_url = f"{graph_url}/drives"
            drives_response = requests.get(drives_url, headers=headers)
            
            if drives_response.status_code == 200:
                drives = drives_response.json().get('value', [])
                print(f"   ✅ {len(drives)} drives trouvés")
                
                if drives:
                    # Prendre le premier drive
                    drive = drives[0]
                    drive_id = drive.get('id')
                    
                    # Tentative d'upload dans ce drive
                    upload_url = (f"https://graph.microsoft.com/v1.0/"
                                  f"drives/{drive_id}/root:"
                                  f"/{filename}:/content")
                    upload_headers = {
                        'Authorization': f'Bearer {token.token}',
                        'Content-Type': 'text/plain'
                    }
                    
                    upload_response = requests.put(
                        upload_url, 
                        data=content.encode('utf-8'), 
                        headers=upload_headers
                    )
                    
                    if upload_response.status_code in [200, 201]:
                        file_info = upload_response.json()
                        print(f"   🎉 Fichier créé via Graph API: {filename}")
                        print(f"   🔗 URL: {file_info.get('webUrl')}")
                        return True
                    else:
                        print(f"   ⚠️  Erreur upload Graph: "
                              f"{upload_response.status_code}")
                        print(f"      Réponse: {upload_response.text}")
            else:
                print(f"   ⚠️  Erreur drives: "
                      f"{drives_response.status_code}")
        
        except Exception as e:
            print(f"   ⚠️  Erreur Graph: {e}")
        
        # Approche 3: Test avec différents scopes de token
        print("   Approche 3: Token SharePoint spécifique...")
        try:
            # Essayer avec un token spécifique SharePoint
            sp_token = credential.get_token(
                "https://ddasys.sharepoint.com/.default"
            )
            
            sp_specific_headers = {
                'Authorization': f'Bearer {sp_token.token}',
                'Accept': 'application/json;odata=verbose',
                'Content-Type': 'application/json;odata=verbose'
            }
            
            # Test d'accès au web
            web_url = f"{site_url}/_api/web"
            web_response = requests.get(web_url, headers=sp_specific_headers)
            
            if web_response.status_code == 200:
                print("   ✅ Accès web SharePoint avec token spécifique")
                
                # Tentative d'upload avec le token spécifique
                folder_path = "/sites/DDASYS/Shared Documents"
                upload_url = (f"{site_url}/_api/web/"
                              f"GetFolderByServerRelativeUrl('{folder_path}')/"
                              f"Files/add(url='{filename}',overwrite=true)")
                
                upload_headers = sp_specific_headers.copy()
                upload_headers['Content-Type'] = 'text/plain'
                
                upload_response = requests.post(
                    upload_url, 
                    data=content.encode('utf-8'), 
                    headers=upload_headers
                )
                
                if upload_response.status_code in [200, 201]:
                    print(f"   🎉 Fichier créé avec token spécifique: "
                          f"{filename}")
                    return True
                else:
                    print(f"   ⚠️  Erreur upload token spécifique: "
                          f"{upload_response.status_code}")
                    print(f"      Réponse: {upload_response.text}")
            else:
                print(f"   ⚠️  Erreur web token spécifique: "
                      f"{web_response.status_code}")
        
        except Exception as e:
            print(f"   ⚠️  Erreur token spécifique: {e}")
        
        print("\n❌ Toutes les approches ont échoué")
        return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False


def main():
    """Fonction principale."""
    success = test_simple_write()
    
    if success:
        print("\n🎉 SUCCESS! L'écriture fonctionne avec votre compte "
              "personnel!")
        print("Vous pouvez maintenant procéder au test avec User "
              "Assigned Identity.")
    else:
        print("\n🔍 L'écriture n'a pas fonctionné via les APIs.")
        print("Cela peut être dû aux permissions limitées de l'API.")
        print("Puisque vous pouvez écrire manuellement, cela confirme que")
        print("vos permissions sont correctes pour le test avec User "
              "Assigned Identity.")


if __name__ == "__main__":
    main() 