#!/usr/bin/env python3
"""
Script de test SharePoint DDASYS pour Azure Container Instance
Utilise ManagedIdentityCredential avec User Assigned Identity
"""

import os
import sys
import requests
from datetime import datetime
from azure.identity import ManagedIdentityCredential
import json

def test_sharepoint_from_aci():
    """Test d'écriture SharePoint depuis ACI avec User Assigned Identity."""
    print("🐳 Test SharePoint DDASYS depuis Azure Container Instance")
    print("=" * 60)
    
    # Configuration depuis les variables d'environnement
    client_id = os.getenv("AZURE_CLIENT_ID")
    site_id = os.getenv("SHAREPOINT_SITE_ID")
    drive_id = os.getenv("SHAREPOINT_DRIVE_ID")
    folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "")
    
    print(f"🔑 Client ID: {client_id[:20]}..." if client_id else "❌ AZURE_CLIENT_ID manquant")
    print(f"📍 Site ID: {site_id[:50]}..." if site_id else "❌ SHAREPOINT_SITE_ID manquant")
    print(f"📁 Drive ID: {drive_id[:50]}..." if drive_id else "❌ SHAREPOINT_DRIVE_ID manquant")
    print(f"📂 Folder: {folder_path or 'Racine du drive'}")
    
    if not all([client_id, site_id, drive_id]):
        print("\n❌ Variables d'environnement manquantes")
        print("💡 Vérifiez que l'ACI a été créé avec les bonnes variables")
        return False
    
    try:
        # 1. Authentification avec Managed Identity
        print("\n1. Authentification avec User Assigned Identity...")
        credential = ManagedIdentityCredential(client_id=client_id)
        
        try:
            token = credential.get_token("https://graph.microsoft.com/.default")
            print("✅ Token Microsoft Graph obtenu avec Managed Identity")
            print(f"   Token valide jusqu'à: {datetime.fromtimestamp(token.expires_on)}")
        except Exception as e:
            print(f"❌ Erreur d'authentification Managed Identity: {e}")
            print("\n🔍 Vérifications nécessaires:")
            print("   - L'ACI a-t-il la User Assigned Identity configurée?")
            print("   - Les permissions Microsoft Graph sont-elles attribuées?")
            print("   - L'administrateur a-t-il donné son consentement?")
            return False
        
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        # 2. Test d'accès au site SharePoint
        print("\n2. Test d'accès au site SharePoint...")
        site_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}"
        
        try:
            response = requests.get(site_url, headers=headers)
            if response.status_code == 200:
                site_info = response.json()
                print(f"✅ Site SharePoint accessible: {site_info.get('displayName')}")
                print(f"   URL: {site_info.get('webUrl')}")
            else:
                print(f"❌ Erreur accès site: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion site: {e}")
            return False
        
        # 3. Test d'accès au drive
        print("\n3. Test d'accès au drive...")
        drive_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
        
        try:
            response = requests.get(drive_url, headers=headers)
            if response.status_code == 200:
                drive_info = response.json()
                print(f"✅ Drive accessible: {drive_info.get('name')}")
                print(f"   Type: {drive_info.get('driveType')}")
            else:
                print(f"❌ Erreur accès drive: {response.status_code}")
                print(f"   Réponse: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur connexion drive: {e}")
            return False
        
        # 4. Test d'écriture dans SharePoint
        print("\n4. Test d'écriture dans SharePoint...")
        
        # Informations sur l'environnement ACI
        hostname = os.getenv("HOSTNAME", "unknown")
        container_info = {
            "hostname": hostname,
            "client_id": client_id,
            "python_version": sys.version,
            "working_directory": os.getcwd()
        }
        
        # Contenu du fichier de test
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        content = f"""Test d'écriture SharePoint DDASYS depuis Azure Container Instance
Timestamp: {timestamp}
Environnement: Azure Container Instance (ACI)
Authentification: User Assigned Identity (Managed Identity)

=== Informations du Container ===
Hostname: {hostname}
Client ID: {client_id}
Python Version: {sys.version.split()[0]}
Working Directory: {os.getcwd()}

=== Configuration SharePoint ===
Site ID: {site_id}
Drive ID: {drive_id}
Folder Path: {folder_path}

=== Test de fonctionnement ===
✅ Authentification Managed Identity: OK
✅ Accès Site SharePoint: OK  
✅ Accès Drive SharePoint: OK
✅ Création de fichier: OK

Ce fichier confirme que l'écriture SharePoint fonctionne
depuis un Azure Container Instance avec User Assigned Identity.

Test effectué le {datetime.now().strftime('%Y-%m-%d à %H:%M:%S')} UTC
"""
        
        filename = f"test_aci_{timestamp}.txt"
        
        # Construire le chemin de destination
        if folder_path and folder_path.strip():
            clean_folder = folder_path.strip().strip('/')
            upload_path = f"/{clean_folder}/{filename}"
            print(f"   📝 Upload vers: {clean_folder}/{filename}")
        else:
            upload_path = f"/{filename}"
            print(f"   📝 Upload vers la racine: {filename}")
        
        # URL API Graph pour upload
        upload_url = (f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
                      f"/root:{upload_path}:/content")
        
        upload_headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'text/plain; charset=utf-8'
        }
        
        print(f"   🌐 URL API: {upload_url}")
        
        # Tentative d'upload
        try:
            response = requests.put(
                upload_url, 
                data=content.encode('utf-8'), 
                headers=upload_headers,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                file_info = response.json()
                file_url = file_info.get('webUrl', 'URL non disponible')
                file_size = file_info.get('size', 0)
                
                print(f"   🎉 Fichier créé avec succès!")
                print(f"   📄 Nom: {filename}")
                print(f"   📏 Taille: {file_size} bytes")
                print(f"   🔗 URL SharePoint: {file_url}")
                
                return True
            else:
                print(f"   ❌ Erreur upload: {response.status_code}")
                print(f"   📝 Réponse: {response.text}")
                
                # Diagnostic des erreurs courantes
                if response.status_code == 403:
                    print("\n🔍 Erreur 403 - Permissions insuffisantes:")
                    print("   - Vérifiez que les permissions Microsoft Graph sont attribuées")
                    print("   - L'administrateur doit donner son consentement")
                elif response.status_code == 404:
                    print("\n🔍 Erreur 404 - Chemin non trouvé:")
                    print("   - Vérifiez le chemin du dossier")
                    print("   - Le dossier doit peut-être être créé d'abord")
                
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur lors de l'upload: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test de l'environnement ACI."""
    print("\n🔍 Test de l'environnement Azure Container Instance")
    print("=" * 55)
    
    # Variables d'environnement importantes
    env_vars = [
        "AZURE_CLIENT_ID",
        "SHAREPOINT_SITE_ID", 
        "SHAREPOINT_DRIVE_ID",
        "SHAREPOINT_FOLDER_PATH",
        "HOSTNAME"
    ]
    
    print("📋 Variables d'environnement:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if len(value) > 50:
                print(f"   ✅ {var}: {value[:47]}...")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Non définie")
    
    # Test de connectivité Internet
    print("\n🌐 Test de connectivité:")
    try:
        response = requests.get("https://graph.microsoft.com/", timeout=10)
        print(f"   ✅ Microsoft Graph accessible (Status: {response.status_code})")
    except Exception as e:
        print(f"   ❌ Erreur connectivité Microsoft Graph: {e}")
    
    # Informations système
    print(f"\n💻 Informations système:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Hostname: {os.getenv('HOSTNAME', 'unknown')}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   User: {os.getenv('USER', 'unknown')}")


def main():
    """Fonction principale."""
    print("🚀 Test SharePoint depuis Azure Container Instance")
    print("📅 " + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'))
    print()
    
    # Test de l'environnement
    test_environment()
    
    # Test SharePoint
    success = test_sharepoint_from_aci()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS! SharePoint fonctionne depuis ACI!")
        print("✅ User Assigned Identity opérationnelle")
        print("✅ Écriture SharePoint depuis container réussie")
        print("\n🚀 Votre solution est prête pour la production!")
    else:
        print("❌ Le test a échoué")
        print("\n🔍 Actions à vérifier:")
        print("1. 🔑 Permissions Microsoft Graph attribuées par l'admin")
        print("2. 🏗️  User Assigned Identity bien configurée sur l'ACI") 
        print("3. 🌐 Connectivité réseau depuis l'ACI")
        print("4. 📝 Variables d'environnement correctes")
    
    print("=" * 60)


if __name__ == "__main__":
    main() 