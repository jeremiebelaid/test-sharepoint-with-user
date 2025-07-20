#!/usr/bin/env python3
"""
Script final pour écrire un fichier dans SharePoint DDASYS
Utilise l'API sites directement pour contourner les limitations
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd
import requests
from azure.identity import AzureCliCredential
from dotenv import load_dotenv
import os

# Chargement de la configuration
load_dotenv('config.env')

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Fonction principale de test d'écriture SharePoint."""
    print("📝 Test d'écriture SharePoint DDASYS - Version finale")
    print("=" * 55)
    
    # Configuration depuis les variables d'environnement
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    folder_path = os.getenv("SHAREPOINT_FOLDER_PATH")
    
    if not site_url:
        print("❌ URL SharePoint non configurée dans config.env")
        return
    
    print(f"🌐 Site SharePoint: {site_url}")
    print(f"📁 Dossier de test: {folder_path}")
    
    # Vérification de l'authentification Azure CLI
    print("\n1. Vérification de l'authentification Azure CLI...")
    try:
        credential = AzureCliCredential()
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Authentification Azure CLI OK")
    except Exception as e:
        print(f"❌ Erreur d'authentification Azure CLI: {e}")
        print("💡 Assurez-vous d'être connecté avec: az login")
        return
    
    # Récupération des informations du site
    print("\n2. Récupération des informations du site...")
    try:
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        # Extraction des informations du site depuis l'URL
        site_parts = site_url.split('/')
        if len(site_parts) >= 5:
            tenant = site_parts[2]  # tenant.sharepoint.com
            site_name = site_parts[4]  # sites/site-name
        else:
            print("❌ Format d'URL SharePoint invalide")
            return
        
        # Récupération des informations du site
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{tenant}:/sites/{site_name}"
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            site_info = response.json()
            site_id = site_info.get('id')
            print(f"✅ Site trouvé: {site_info.get('displayName')}")
            print(f"📍 Site ID: {site_id}")
        else:
            print(f"❌ Erreur d'accès au site: {response.status_code}")
            return
    
    except Exception as e:
        print(f"❌ Erreur lors de l'accès au site: {e}")
        return
    
    # Test d'écriture avec l'API lists
    print("\n3. Test d'écriture avec l'API lists...")
    try:
        # Récupération des lists du site
        lists_url = f"{graph_url}/lists"
        lists_response = requests.get(lists_url, headers=headers)
        
        if lists_response.status_code == 200:
            lists_data = lists_response.json()
            lists = lists_data.get('value', [])
            print(f"✅ {len(lists)} listes trouvées")
            
            # Recherche de la liste "Documents" ou "Documents Shared"
            documents_list = None
            for lst in lists:
                list_name = lst.get('displayName', '').lower()
                if 'document' in list_name or 'shared' in list_name:
                    documents_list = lst
                    print(f"📋 Liste trouvée: {lst.get('displayName')}")
                    break
            
            if documents_list:
                # Test d'upload via l'API drive de la liste
                list_id = documents_list.get('id')
                drive_url = f"{graph_url}/lists/{list_id}/drive"
                drive_response = requests.get(drive_url, headers=headers)
                
                if drive_response.status_code == 200:
                    drive_info = drive_response.json()
                    drive_id = drive_info.get('id')
                    print(f"✅ Drive de la liste trouvé: {drive_info.get('name')}")
                    
                    # Création du contenu du fichier
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    text_content = f"""Test d'écriture SharePoint DDASYS - Identité Personnelle
=======================================================

Fichier créé le: {timestamp}
Utilisateur: Identité personnelle (Azure CLI)
Site SharePoint: {site_url}
Dossier: {folder_path}

Ce fichier a été créé pour tester l'accès en écriture à SharePoint
avec l'identité personnelle avant de tester avec User Assigned Identity.

Méthode: API Microsoft Graph - Drive de liste
Site ID: {site_id}
Drive ID: {drive_id}

Test réussi ! 🎉
"""
                    
                    filename = f"test-final-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
                    
                    # Upload du fichier dans le drive de la liste
                    upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{filename}:/content"
                    
                    upload_headers = {
                        'Authorization': f'Bearer {token.token}',
                        'Content-Type': 'text/plain'
                    }
                    
                    upload_response = requests.put(
                        upload_url, 
                        data=text_content.encode('utf-8'),
                        headers=upload_headers
                    )
                    
                    if upload_response.status_code in [200, 201]:
                        file_info = upload_response.json()
                        print("🎉 ✅ SUCCÈS ! Fichier créé avec succès !")
                        print(f"   📄 Nom: {file_info.get('name')}")
                        print(f"   📏 Taille: {file_info.get('size')} bytes")
                        print(f"   🔗 URL: {file_info.get('webUrl')}")
                        
                        # Test d'écriture d'un fichier Excel aussi
                        print("\n4. Test d'écriture fichier Excel...")
                        try:
                            # Création d'un DataFrame de test
                            test_data = pd.DataFrame({
                                'nom': ['Alice', 'Bob', 'Charlie', 'Diana'],
                                'age': [25, 30, 35, 28],
                                'score': [85.5, 92.0, 78.5, 88.2],
                                'date_test': datetime.now(),
                                'site': site_url,
                                'dossier': folder_path
                            })
                            
                            # Création d'un fichier Excel temporaire
                            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
                                temp_file_path = temp_file.name
                            
                            # Export du DataFrame vers Excel
                            with pd.ExcelWriter(temp_file_path, engine='openpyxl') as writer:
                                test_data.to_excel(writer, sheet_name="TestData", index=False)
                            
                            # Lecture du contenu du fichier
                            with open(temp_file_path, 'rb') as file:
                                file_content = file.read()
                            
                            excel_filename = f"test-excel-{datetime.now().strftime('%Y%m%d-%H%M%S')}.xlsx"
                            excel_upload_url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{excel_filename}:/content"
                            
                            excel_headers = {
                                'Authorization': f'Bearer {token.token}',
                                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            }
                            
                            excel_response = requests.put(
                                excel_upload_url,
                                data=file_content,
                                headers=excel_headers
                            )
                            
                            if excel_response.status_code in [200, 201]:
                                excel_info = excel_response.json()
                                print("🎉 ✅ Fichier Excel créé avec succès !")
                                print(f"   📊 Nom: {excel_info.get('name')}")
                                print(f"   📏 Taille: {excel_info.get('size')} bytes")
                                print(f"   🔗 URL: {excel_info.get('webUrl')}")
                            else:
                                print(f"⚠️  Échec upload Excel: {excel_response.status_code}")
                            
                            # Nettoyage du fichier temporaire
                            Path(temp_file_path).unlink(missing_ok=True)
                            
                        except Exception as e:
                            print(f"⚠️  Erreur Excel: {e}")
                        
                        return True
                    else:
                        print(f"❌ Erreur upload: {upload_response.status_code}")
                        print(f"   Réponse: {upload_response.text}")
                else:
                    print(f"❌ Erreur accès drive de liste: {drive_response.status_code}")
            else:
                print("❌ Aucune liste de documents trouvée")
        else:
            print(f"❌ Erreur accès aux listes: {lists_response.status_code}")
    
    except Exception as e:
        print(f"❌ Erreur lors du test d'écriture: {e}")
    
    print("\n" + "=" * 55)
    print("Test terminé")


if __name__ == "__main__":
    main() 