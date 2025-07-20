#!/usr/bin/env python3
"""
Script utilitaire pour extraire automatiquement les IDs SharePoint (site_id, drive_id)
à partir de l'URL SharePoint DDASYS en utilisant l'API Microsoft Graph.

Prérequis: pip install azure-identity requests urllib3 python-dotenv
"""

import logging
import os
import urllib.parse
from typing import Optional, Tuple

import requests
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SharePointIDExtractorDDASYS:
    """Classe pour extraire les IDs SharePoint DDASYS via Microsoft Graph."""

    def __init__(self):
        """Initialise l'extracteur avec l'authentification Azure CLI."""
        self.credential = AzureCliCredential()
        self.access_token = None

    def get_access_token(self) -> str:
        """Récupère un token d'accès pour l'API Microsoft Graph."""
        if not self.access_token:
            try:
                token = self.credential.get_token(
                    "https://graph.microsoft.com/.default"
                )
                self.access_token = token.token
                logger.info("Token d'accès Microsoft Graph obtenu avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'obtention du token: {e}")
                raise
        return self.access_token

    def parse_sharepoint_url(self, url: str) -> Tuple[str, str, str]:
        """
        Parse une URL SharePoint DDASYS pour extraire les composants.

        Args:
            url: URL SharePoint complète

        Returns:
            Tuple[tenant, site_name, folder_path]: Composants de l'URL
        """
        # Décoder l'URL
        decoded_url = urllib.parse.unquote(url)
        logger.info(f"URL décodée: {decoded_url}")

        # Parser l'URL
        parsed = urllib.parse.urlparse(decoded_url)

        # Extraire le tenant (ex: ddasys.sharepoint.com)
        tenant = parsed.netloc

        # Extraire le nom du site depuis le path
        path_parts = parsed.path.split("/")
        site_name = None
        for i, part in enumerate(path_parts):
            if part == "sites" and i + 1 < len(path_parts):
                site_name = path_parts[i + 1]
                break

        # Extraire le folder path depuis les paramètres de query
        folder_path = ""
        if "id=" in parsed.query:
            query_params = urllib.parse.parse_qs(parsed.query)
            if "id" in query_params:
                id_param = query_params["id"][0]
                # Le paramètre id contient le chemin complet
                if ("Shared Documents" in id_param or 
                     "Documents partages" in id_param):
                     # Extraire le chemin après Documents partages
                     parts = id_param.split("Shared Documents/")
                     if len(parts) > 1:
                         folder_path = parts[1].replace("/", "/")
                     else:
                         # Essayer avec "Documents partages"
                         parts = id_param.split("Documents partages/")
                         if len(parts) > 1:
                             folder_path = parts[1].replace("/", "/")

        logger.info(f"Tenant: {tenant}")
        logger.info(f"Site: {site_name}")
        logger.info(f"Folder path: {folder_path}")

        return tenant, site_name, folder_path

    def get_site_id(self, tenant: str, site_name: str) -> Optional[str]:
        """
        Récupère le site ID via l'API Microsoft Graph.

        Args:
            tenant: Nom du tenant SharePoint
            site_name: Nom du site

        Returns:
            str: Site ID ou None en cas d'erreur
        """
        try:
            token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Construire l'URL pour récupérer le site
            api_url = (
                f"https://graph.microsoft.com/v1.0/sites/"
                f"{tenant}:/sites/{site_name}"
            )

            logger.info(f"Requête GET vers: {api_url}")
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                site_data = response.json()
                site_id = site_data.get("id")
                site_display_name = site_data.get("displayName", "")
                logger.info(f"Site ID trouvé: {site_id}")
                logger.info(f"Nom du site: {site_display_name}")
                return site_id
            else:
                logger.error(
                    f"Erreur lors de la récupération du site ID: "
                    f"{response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception lors de la récupération du site ID: {e}")
            return None

    def get_drive_id(
        self, site_id: str, drive_name: str = "Documents partages"
    ) -> Optional[str]:
        """
        Récupère le drive ID d'un site SharePoint.

        Args:
            site_id: ID du site SharePoint
            drive_name: Nom du drive (par défaut "Documents partages")

        Returns:
            str: Drive ID ou None en cas d'erreur
        """
        try:
            token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Récupérer tous les drives du site
            api_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"

            logger.info(f"Requête GET vers: {api_url}")
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                drives_data = response.json()
                drives = drives_data.get("value", [])

                logger.info(f"Drives trouvés ({len(drives)}):")
                for drive in drives:
                    drive_id = drive.get("id")
                    drive_display_name = drive.get("name", "Unknown")
                    drive_type = drive.get("driveType", "Unknown")
                    logger.info(f"  - {drive_display_name} "
                                f"({drive_type}): {drive_id}")

                    # Chercher le drive "Documents partages" ou similaire
                    if drive_display_name.lower() in [
                        "documents partages",
                        "documents",
                        "shared documents",
                    ]:
                        logger.info(f"Drive principal trouvé: {drive_id}")
                        return drive_id

                # Si pas trouvé par nom, prendre le premier drive de type documentLibrary
                for drive in drives:
                    if drive.get("driveType") == "documentLibrary":
                        default_drive_id = drive.get("id")
                        logger.info(
                            f"Utilisation du premier drive "
                            f"documentLibrary: {default_drive_id}"
                        )
                        return default_drive_id

                # Si toujours pas trouvé, prendre le premier drive
                if drives:
                    default_drive_id = drives[0].get("id")
                    logger.info(
                        f"Utilisation du premier drive par défaut: "
                        f"{default_drive_id}"
                    )
                    return default_drive_id

            else:
                logger.error(
                    f"Erreur lors de la récupération des drives: "
                    f"{response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception lors de la récupération du drive ID: {e}")
            return None

    def list_site_content(self, site_id: str, drive_id: str) -> None:
        """
        Liste le contenu du site SharePoint pour aide au débogage.

        Args:
            site_id: ID du site SharePoint
            drive_id: ID du drive principal
        """
        try:
            token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            # Lister les fichiers à la racine du drive
            api_url = (f"https://graph.microsoft.com/v1.0/drives/"
                       f"{drive_id}/root/children")

            logger.info(f"Listing contenu du drive: {api_url}")
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                items_data = response.json()
                items = items_data.get("value", [])

                logger.info(f"Contenu du drive ({len(items)} éléments):")
                for item in items:
                    item_name = item.get("name", "Unknown")
                    item_type = "Folder" if "folder" in item else "File"
                    logger.info(f"  - {item_type}: {item_name}")

            else:
                logger.error(
                    f"Erreur lors du listing: {response.status_code} - {response.text}"
                )

        except Exception as e:
            logger.error(f"Exception lors du listing: {e}")

    def extract_all_ids(
        self, sharepoint_url: str
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        Extrait tous les IDs nécessaires d'une URL SharePoint DDASYS.

        Args:
            sharepoint_url: URL SharePoint complète

        Returns:
            Tuple[site_id, drive_id, folder_path]: IDs extraits
        """
        logger.info("Extraction des IDs SharePoint DDASYS...")

        # 1. Parser l'URL
        tenant, site_name, folder_path = self.parse_sharepoint_url(sharepoint_url)

        if not tenant or not site_name:
            logger.error("Impossible de parser l'URL SharePoint")
            return None, None, folder_path

        # 2. Récupérer le site ID
        site_id = self.get_site_id(tenant, site_name)
        if not site_id:
            return None, None, folder_path

        # 3. Récupérer le drive ID
        drive_id = self.get_drive_id(site_id)

        # 4. Lister le contenu pour aide au débogage
        if site_id and drive_id:
            self.list_site_content(site_id, drive_id)

        return site_id, drive_id, folder_path


def main():
    """Fonction principale."""
    # URL SharePoint depuis config.env ou valeur par défaut
    sharepoint_url = os.getenv("SHAREPOINT_SITE_URL")
    
    if not sharepoint_url:
        # URL par défaut si non configurée
        sharepoint_url = "https://ddasys.sharepoint.com/sites/DDASYS"
        print("⚠️  URL SharePoint non trouvée dans config.env")
        print(f"   Utilisation de l'URL par défaut: {sharepoint_url}")

    print("🔍 Extraction des IDs SharePoint DDASYS")
    print("=" * 60)

    # Vérification de l'authentification Azure CLI
    print("1. Vérification de l'authentification Azure CLI...")
    try:
        credential = AzureCliCredential()
        credential.get_token("https://graph.microsoft.com/.default")
        print("✅ Authentification Azure CLI OK")
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        print("💡 Connectez-vous avec: az login")
        return

    # Extraction des IDs
    print("\n2. Extraction des IDs depuis l'URL SharePoint...")
    print(f"URL: {sharepoint_url}")

    extractor = SharePointIDExtractorDDASYS()
    site_id, drive_id, folder_path = extractor.extract_all_ids(sharepoint_url)

    # Affichage des résultats
    print("\n" + "=" * 60)
    print("📋 RÉSULTATS POUR VOS SCRIPTS SHAREPOINT DDASYS")
    print("=" * 60)

    if site_id:
        print(f'SITE_ID = "{site_id}"')
    else:
        print('SITE_ID = "ERROR - Non trouvé"')

    if drive_id:
        print(f'DRIVE_ID = "{drive_id}"')
    else:
        print('DRIVE_ID = "ERROR - Non trouvé"')

    # Nettoyer le folder path
    clean_folder_path = folder_path.strip("/")
    if clean_folder_path:
        print(f'FOLDER_PATH = "{clean_folder_path}"')
    else:
        print('FOLDER_PATH = ""  # Racine du drive')

    print("\n💡 Ajoutez ces valeurs dans votre fichier config.env :")
    print(f"SHAREPOINT_SITE_ID={site_id or 'ERREUR'}")
    print(f"SHAREPOINT_DRIVE_ID={drive_id or 'ERREUR'}")
    if clean_folder_path:
        print(f"SHAREPOINT_FOLDER_PATH={clean_folder_path}")

    if site_id and drive_id:
        print("\n✅ Extraction réussie ! Vous pouvez maintenant utiliser ces IDs.")
        print("🔗 URLs utiles pour tests :")
        print(f"   Site: https://graph.microsoft.com/v1.0/sites/{site_id}")
        print(f"   Drive: https://graph.microsoft.com/v1.0/drives/{drive_id}")
        print(f"   Contenu: https://graph.microsoft.com/v1.0/drives/{drive_id}/root")
    else:
        print("\n❌ Extraction échouée. Vérifiez :")
        print("   - Vos permissions sur le site SharePoint DDASYS")
        print("   - Que vous êtes connecté avec le bon compte Azure")
        print("   - Que l'URL SharePoint est correcte")


if __name__ == "__main__":
    main() 