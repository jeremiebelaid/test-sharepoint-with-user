#!/usr/bin/env python3
"""
Script de test SharePoint DDASYS adapté du script fonctionnel
Prérequis: pip install azure-identity pandas openpyxl requests python-dotenv
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


class SharePointDDASYSTester:
    """Classe pour tester la connexion et l'écriture SharePoint DDASYS."""
    
    def __init__(self, site_url: str, folder_path: str):
        """
        Initialise le testeur SharePoint.
        
        Args:
            site_url: URL du site SharePoint
            folder_path: Chemin du dossier dans SharePoint
        """
        self.site_url = site_url
        self.folder_path = folder_path
        self.access_token = None
        self.credential = AzureCliCredential()
        self.site_id = None
        self.drive_id = None
        
    def get_access_token(self) -> str:
        """Récupère un token d'accès pour l'API Microsoft Graph."""
        if not self.access_token:
            try:
                # Utilisation des credentials Azure CLI (az login)
                token = self.credential.get_token("https://graph.microsoft.com/.default")
                self.access_token = token.token
                logger.info("Token d'accès Microsoft Graph obtenu avec succès")
            except Exception as e:
                logger.error(f"Échec d'obtention du token: {e}")
                raise
        return self.access_token
    
    def get_site_and_drive_info(self) -> bool:
        """
        Récupère les informations du site et du drive principal.
        
        Returns:
            bool: True si les informations sont récupérées avec succès
        """
        try:
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Extraction des informations du site depuis l'URL
            site_parts = self.site_url.split('/')
            if len(site_parts) >= 5:
                tenant = site_parts[2]  # tenant.sharepoint.com
                site_name = site_parts[4]  # sites/site-name
            else:
                logger.error("Format d'URL SharePoint invalide")
                return False
            
            # Récupération des informations du site
            graph_url = f"https://graph.microsoft.com/v1.0/sites/{tenant}:/sites/{site_name}"
            response = requests.get(graph_url, headers=headers)
            
            if response.status_code == 200:
                site_info = response.json()
                self.site_id = site_info.get('id')
                logger.info(f"Site trouvé: {site_info.get('displayName')}")
                logger.info(f"Site ID: {self.site_id}")
                
                # Récupération du drive principal
                drive_url = f"{graph_url}/drive"
                drive_response = requests.get(drive_url, headers=headers)
                
                if drive_response.status_code == 200:
                    drive_info = drive_response.json()
                    self.drive_id = drive_info.get('id')
                    logger.info(f"Drive trouvé: {drive_info.get('name')}")
                    logger.info(f"Drive ID: {self.drive_id}")
                    return True
                else:
                    logger.error(f"Erreur récupération drive: {drive_response.status_code}")
                    return False
            else:
                logger.error(f"Erreur récupération site: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Teste la connexion SharePoint en listant les fichiers du dossier racine.
        
        Returns:
            bool: True si la connexion fonctionne
        """
        try:
            if not self.site_id or not self.drive_id:
                if not self.get_site_and_drive_info():
                    return False
            
            token = self.get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Test de listage des fichiers à la racine
            list_url = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root/children"
            
            logger.info(f"Test de connexion sur: {list_url}")
            response = requests.get(list_url, headers=headers)
            
            if response.status_code == 200:
                files = response.json().get('value', [])
                logger.info(f"Connexion réussie - {len(files)} éléments trouvés à la racine")
                return True
            else:
                logger.error(f"Échec connexion - Code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion: {e}")
            return False
    
    def upload_excel_file(self, df: pd.DataFrame, filename: str, sheet_name: str = "Sheet1") -> Optional[str]:
        """
        Upload un DataFrame vers SharePoint en tant que fichier Excel.
        
        Args:
            df: DataFrame pandas à exporter
            filename: Nom du fichier (sans extension)
            sheet_name: Nom de la feuille Excel
            
        Returns:
            str: URL du fichier uploadé ou None en cas d'erreur
        """
        temp_file_path = None
        try:
            if not self.site_id or not self.drive_id:
                if not self.get_site_and_drive_info():
                    return None
            
            token = self.get_access_token()
            
            # Création d'un fichier Excel temporaire
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
                temp_file_path = temp_file.name
            
            # Export du DataFrame vers Excel
            with pd.ExcelWriter(temp_file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            logger.info(f"Fichier Excel temporaire créé: {temp_file_path}")
            
            # Lecture du contenu du fichier
            with open(temp_file_path, 'rb') as file:
                file_content = file.read()
            
            # Tentative d'upload dans le dossier spécifique d'abord
            if self.folder_path:
                upload_path = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{self.folder_path}/{filename}.xlsx:/content"
                logger.info(f"Tentative d'upload dans le dossier spécifique: {upload_path}")
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                }
                
                response = requests.put(upload_path, data=file_content, headers=headers)
                
                if response.status_code in [200, 201]:
                    file_info = response.json()
                    file_url = file_info.get('webUrl', '')
                    logger.info(f"Fichier uploadé avec succès dans le dossier spécifique: {file_url}")
                    return file_url
                else:
                    logger.warning(f"Échec upload dossier spécifique - Code: {response.status_code}")
            
            # Fallback: upload à la racine
            upload_path_root = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{filename}.xlsx:/content"
            logger.info(f"Tentative d'upload à la racine: {upload_path_root}")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
            
            response = requests.put(upload_path_root, data=file_content, headers=headers)
            
            if response.status_code in [200, 201]:
                file_info = response.json()
                file_url = file_info.get('webUrl', '')
                logger.info(f"Fichier uploadé avec succès à la racine: {file_url}")
                return file_url
            else:
                logger.error(f"Échec upload racine - Code: {response.status_code}, Réponse: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'upload: {e}")
            return None
        finally:
            # Nettoyage du fichier temporaire
            if temp_file_path:
                try:
                    Path(temp_file_path).unlink(missing_ok=True)
                    logger.info(f"Fichier temporaire supprimé: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier temporaire {temp_file_path}: {e}")

    def upload_text_file(self, content: str, filename: str) -> Optional[str]:
        """
        Upload un fichier texte vers SharePoint.
        
        Args:
            content: Contenu du fichier texte
            filename: Nom du fichier (avec extension)
            
        Returns:
            str: URL du fichier uploadé ou None en cas d'erreur
        """
        try:
            if not self.site_id or not self.drive_id:
                if not self.get_site_and_drive_info():
                    return None
            
            token = self.get_access_token()
            
            # Tentative d'upload dans le dossier spécifique d'abord
            if self.folder_path:
                upload_path = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{self.folder_path}/{filename}:/content"
                logger.info(f"Tentative d'upload texte dans le dossier spécifique: {upload_path}")
                
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'text/plain'
                }
                
                response = requests.put(upload_path, data=content.encode('utf-8'), headers=headers)
                
                if response.status_code in [200, 201]:
                    file_info = response.json()
                    file_url = file_info.get('webUrl', '')
                    logger.info(f"Fichier texte uploadé avec succès dans le dossier spécifique: {file_url}")
                    return file_url
                else:
                    logger.warning(f"Échec upload texte dossier spécifique - Code: {response.status_code}")
            
            # Fallback: upload à la racine
            upload_path_root = f"https://graph.microsoft.com/v1.0/drives/{self.drive_id}/root:/{filename}:/content"
            logger.info(f"Tentative d'upload texte à la racine: {upload_path_root}")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'text/plain'
            }
            
            response = requests.put(upload_path_root, data=content.encode('utf-8'), headers=headers)
            
            if response.status_code in [200, 201]:
                file_info = response.json()
                file_url = file_info.get('webUrl', '')
                logger.info(f"Fichier texte uploadé avec succès à la racine: {file_url}")
                return file_url
            else:
                logger.error(f"Échec upload texte racine - Code: {response.status_code}, Réponse: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'upload texte: {e}")
            return None


def main():
    """Fonction principale de test."""
    print("🔍 Test SharePoint DDASYS avec compte personnel (az login)")
    print("=" * 65)
    
    # Configuration depuis les variables d'environnement
    site_url = os.getenv("SHAREPOINT_SITE_URL")
    folder_path = os.getenv("SHAREPOINT_FOLDER_PATH")
    
    if not site_url:
        print("❌ URL SharePoint non configurée dans config.env")
        return
    
    print(f"🌐 Site SharePoint: {site_url}")
    print(f"📁 Dossier de test: {folder_path}")
    
    # Vérification que l'utilisateur est connecté via az login
    print("\n1. Vérification de l'authentification Azure CLI...")
    try:
        credential = AzureCliCredential()
        # Test simple pour voir si les credentials fonctionnent
        token = credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Authentification Azure CLI OK")
    except Exception as e:
        print(f"❌ Erreur d'authentification Azure CLI: {e}")
        print("💡 Assurez-vous d'être connecté avec: az login")
        return
    
    # Création du testeur SharePoint
    tester = SharePointDDASYSTester(
        site_url=site_url,
        folder_path=folder_path
    )
    
    # Test 1: Connexion et lecture
    print("\n2. Test de connexion SharePoint...")
    try:
        if tester.test_connection():
            print("✅ Connexion SharePoint réussie - permission de lecture OK")
        else:
            print("❌ Échec de la connexion SharePoint")
            print("💡 Vérifiez vos permissions SharePoint")
            return
    except Exception as e:
        print(f"❌ Erreur lors du test de connexion: {e}")
        return
    
    # Test 2: Écriture d'un fichier texte
    print("\n3. Test d'écriture de fichier texte...")
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text_content = f"""Test d'écriture SharePoint DDASYS - Identité Personnelle
=======================================================

Fichier créé le: {timestamp}
Utilisateur: Identité personnelle (Azure CLI)
Site SharePoint: {site_url}
Dossier: {folder_path}

Ce fichier a été créé pour tester l'accès en écriture à SharePoint
avec l'identité personnelle avant de tester avec User Assigned Identity.

Test réussi ! 🎉
"""
        
        filename = f"test-personal-identity-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        
        file_url = tester.upload_text_file(
            content=text_content,
            filename=filename
        )
        
        if file_url:
            print("✅ Fichier texte uploadé avec succès !")
            print(f"   📄 URL: {file_url}")
        else:
            print("❌ Échec de l'upload du fichier texte")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'upload texte: {e}")
    
    # Test 3: Écriture d'un fichier Excel
    print("\n4. Test d'écriture de fichier Excel...")
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
        
        print(f"   DataFrame créé avec {len(test_data)} lignes et {len(test_data.columns)} colonnes")
        
        # Upload du fichier de test
        file_url = tester.upload_excel_file(
            df=test_data,
            filename=f"test_sharepoint_ddasys_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            sheet_name="TestData"
        )
        
        if file_url:
            print("✅ Fichier Excel uploadé avec succès !")
            print(f"   📄 URL: {file_url}")
            print(f"   📊 Données: {len(test_data)} lignes, {len(test_data.columns)} colonnes")
        else:
            print("❌ Échec de l'upload du fichier Excel")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'upload Excel: {e}")
    
    print("\n" + "=" * 65)
    print("Test terminé ! 🎉")
    print("\nMaintenant vous pouvez procéder au test avec User Assigned Identity sur Azure.")


if __name__ == "__main__":
    main() 