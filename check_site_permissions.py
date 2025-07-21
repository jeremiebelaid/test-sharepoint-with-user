#!/usr/bin/env python3
"""
Script pour vérifier les permissions d'un site SharePoint spécifique
via l'API Microsoft Graph.
"""

import requests
import json
from azure.identity import AzureCliCredential


def check_site_permissions():
    """
    Récupère et affiche les permissions pour un site SharePoint spécifique
    en utilisant l'API Microsoft Graph.
    """

    # Endpoint fourni pour vérifier les permissions
    endpoint_url = (
        "https://graph.microsoft.com/v1.0/sites/"
        "ddasys.sharepoint.com,90022be8-5b4d-437e-b7b8-428a5b4a9d75,"
        "dfdecd9e-4cd3-470d-a08f-e0b602bf8390/permissions"
    )

    print(f"▶️  Interrogation du endpoint : {endpoint_url}")

    try:
        # 1. Authentification via les identifiants de l'Azure CLI
        print("🔄 Authentification via Azure CLI en cours...")
        credential = AzureCliCredential()
        # Obtention d'un token pour l'API Microsoft Graph
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Authentification réussie. Token obtenu.")

        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }

        # 2. Exécution de la requête GET
        print("▶️  Envoi de la requête GET à l'API Microsoft Graph...")
        response = requests.get(endpoint_url, headers=headers)

        # 3. Traitement de la réponse
        print(f"◀️  Code de statut de la réponse : {response.status_code}")

        if response.status_code == 200:
            permissions = response.json()
            print("\n✅ Permissions récupérées avec succès :")
            # Affichage formaté de la réponse JSON
            print(json.dumps(permissions, indent=2, ensure_ascii=False))
        else:
            print("\n❌ Erreur lors de la récupération des permissions :")
            # Affichage des détails de l'erreur si disponibles
            try:
                error_details = response.json()
                print(json.dumps(error_details, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response.text)

    except Exception as e:
        print(f"\n❌ Une erreur inattendue est survenue : {e}")


if __name__ == "__main__":
    check_site_permissions() 