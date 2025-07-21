#!/usr/bin/env python3
"""
Script de test pour l'écriture sur SharePoint depuis un conteneur ACI.
Utilise l'identité managée assignée à l'ACI pour l'authentification.
"""

import os
import requests
from datetime import datetime
from azure.identity import ManagedIdentityCredential


def test_sharepoint_from_aci():
    """
    Tente d'écrire un fichier sur un site SharePoint en utilisant
    l'identité managée de l'ACI.
    """
    print("🚀 Test d'écriture sur SharePoint depuis l'ACI...")
    print("=" * 50)

    # --- Configuration (à adapter si nécessaire) ---
    # Ces variables peuvent être passées comme variables d'environnement à l'ACI
    site_url = os.getenv(
        "SHAREPOINT_SITE_URL", "https://ddasys.sharepoint.com/sites/DDASYS"
    )
    folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "ACI_Tests")
    identity_client_id = os.getenv("IDENTITY_CLIENT_ID")  # Doit être fourni

    if not identity_client_id:
        print("❌ ERREUR : La variable d'environnement "
              "IDENTITY_CLIENT_ID est requise.")
        print("💡 Vous pouvez la récupérer avec : az identity show "
              "--resource-group ... --name ... --query clientId -o tsv")
        return

    print(f"🔗 Site SharePoint cible : {site_url}")
    print(f"📂 Dossier cible : {folder_path}")
    print(f"🆔 Client ID de l'identité : {identity_client_id}")

    try:
        # 1. Authentification avec l'identité managée
        print("\n1. Authentification avec l'identité managée...")
        credential = ManagedIdentityCredential(client_id=identity_client_id)
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Jeton d'accès Microsoft Graph obtenu avec succès.")

        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }

        # 2. Récupération de l'ID du site et du Drive
        print("\n2. Récupération des IDs du Site et du Drive...")
        hostname = site_url.split('/')[2]
        site_path = '/' + '/'.join(site_url.split('/')[3:])

        site_info_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{site_path}"
        response = requests.get(site_info_url, headers=headers)
        response.raise_for_status()  # Lève une exception si erreur HTTP
        site_id = response.json()['id']
        print(f"   ✅ Site ID trouvé : {site_id}")

        drive_info_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive"
        response = requests.get(drive_info_url, headers=headers)
        response.raise_for_status()
        drive_id = response.json()['id']
        print(f"   ✅ Drive ID trouvé : {drive_id}")

        # 3. Test d'écriture
        print("\n3. Tentative d'écriture d'un fichier de test...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_from_aci_{timestamp}.txt"
        content = f"Fichier de test créé depuis l'ACI le {timestamp}."

        upload_url = (f"https://graph.microsoft.com/v1.0/drives/{drive_id}"
                      f"/root:/{folder_path}/{filename}:/content")

        upload_headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'text/plain'
        }

        response = requests.put(
            upload_url,
            data=content.encode('utf-8'),
            headers=upload_headers
        )

        if response.status_code == 404:  # Dossier non trouvé
            print("   ⚠️  Le dossier n'existe pas, tentative de création...")
            create_folder_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
            folder_data = {"name": folder_path, "folder": {}}
            requests.post(
                create_folder_url, json=folder_data, headers=headers
            ).raise_for_status()
            print("   ✅ Dossier créé. Nouvelle tentative d'upload...")
            response = requests.put(
                upload_url, data=content.encode('utf-8'), headers=upload_headers
            )

        response.raise_for_status()  # Lève une exception si l'upload a encore échoué

        file_info = response.json()
        print("\n🎉 SUCCÈS ! Fichier créé avec succès sur SharePoint.")
        print(f"   🔗 URL : {file_info.get('webUrl')}")

    except Exception as e:
        print("\n❌ ERREUR : Le test a échoué.")
        print(f"   Détails : {e}")
        if hasattr(e, 'response'):
            print(f"   Réponse de l'API : {e.response.text}")


if __name__ == "__main__":
    test_sharepoint_from_aci() 