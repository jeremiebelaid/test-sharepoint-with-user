"""
Script d'authentification SharePoint avec Azure Managed Identity
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File
from office365.sharepoint.lists.list import List
import requests
from rich.console import Console
from rich.table import Table
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Chargement des variables d'environnement
load_dotenv()

class SharePointAuthenticator:
    """
    Classe pour gérer l'authentification SharePoint avec Managed Identity
    """
    
    def __init__(self, site_url: str, use_managed_identity: bool = True):
        """
        Initialise l'authentificateur SharePoint
        
        Args:
            site_url: URL du site SharePoint
            use_managed_identity: Utiliser Managed Identity (True) ou DefaultAzureCredential (False)
        """
        self.site_url = site_url
        self.use_managed_identity = use_managed_identity
        self.ctx = None
        self.credential = None
        
    def authenticate(self) -> bool:
        """
        Authentification avec Managed Identity
        
        Returns:
            bool: True si l'authentification réussit
        """
        try:
            console.print("🔐 [bold blue]Début de l'authentification SharePoint...[/bold blue]")
            
            # Choix du type de credential
            if self.use_managed_identity:
                console.print("📋 Utilisation de Managed Identity...")
                self.credential = ManagedIdentityCredential()
            else:
                console.print("📋 Utilisation de DefaultAzureCredential...")
                self.credential = DefaultAzureCredential()
            
            # Test de l'obtention du token
            console.print("🎫 Obtention du token d'accès...")
            token = self.credential.get_token("https://graph.microsoft.com/.default")
            console.print(f"✅ Token obtenu avec succès (expire dans {token.expires_on} secondes)")
            
            # Création du contexte SharePoint
            console.print("🌐 Création du contexte SharePoint...")
            self.ctx = ClientContext(self.site_url).with_credentials(self.credential)
            
            # Test de la connexion
            console.print("🔍 Test de la connexion SharePoint...")
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            console.print(f"✅ [bold green]Connecté avec succès au site SharePoint: {web.title}[/bold green]")
            console.print(f"📍 URL: {self.site_url}")
            
            return True
            
        except Exception as e:
            console.print(f"❌ [bold red]Erreur d'authentification: {str(e)}[/bold red]")
            logger.error(f"Erreur d'authentification: {str(e)}")
            return False
    
    def get_site_info(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations du site SharePoint
        
        Returns:
            Dict contenant les informations du site
        """
        if not self.ctx:
            console.print("❌ [red]Non authentifié. Appelez d'abord authenticate()[/red]")
            return None
            
        try:
            console.print("📊 Récupération des informations du site...")
            
            web = self.ctx.web
            self.ctx.load(web)
            self.ctx.execute_query()
            
            site_info = {
                "title": web.title,
                "url": web.url,
                "description": web.description,
                "created": web.created,
                "last_modified": web.last_item_modified_date
            }
            
            return site_info
            
        except Exception as e:
            console.print(f"❌ [red]Erreur lors de la récupération des informations: {str(e)}[/red]")
            return None
    
    def list_lists(self) -> Optional[list]:
        """
        Liste toutes les listes SharePoint du site
        
        Returns:
            Liste des listes SharePoint
        """
        if not self.ctx:
            console.print("❌ [red]Non authentifié. Appelez d'abord authenticate()[/red]")
            return None
            
        try:
            console.print("📋 Récupération des listes SharePoint...")
            
            lists = self.ctx.web.lists
            self.ctx.load(lists)
            self.ctx.execute_query()
            
            lists_info = []
            for lst in lists:
                lists_info.append({
                    "title": lst.title,
                    "id": lst.id,
                    "item_count": lst.item_count,
                    "hidden": lst.hidden
                })
            
            return lists_info
            
        except Exception as e:
            console.print(f"❌ [red]Erreur lors de la récupération des listes: {str(e)}[/red]")
            return None
    
    def test_file_operations(self, folder_path: str = None) -> bool:
        """
        Test des opérations de fichiers
        
        Args:
            folder_path: Chemin du dossier à tester (par défaut: dossier de test configuré)
            
        Returns:
            bool: True si les tests réussissent
        """
        if not self.ctx:
            console.print("❌ [red]Non authentifié. Appelez d'abord authenticate()[/red]")
            return False
            
        # Utilisation du dossier de test par défaut si non spécifié
        if folder_path is None:
            folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "Documents partages/General/Test-user-assigned-identity")
            
        try:
            console.print(f"📁 Test des opérations de fichiers dans '{folder_path}'...")
            
            # Récupération du dossier
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_path)
            self.ctx.load(folder)
            self.ctx.execute_query()
            
            console.print(f"✅ Dossier trouvé: {folder.name}")
            
            # Liste des fichiers
            files = folder.files
            self.ctx.load(files)
            self.ctx.execute_query()
            
            console.print(f"📄 Nombre de fichiers trouvés: {len(files)}")
            
            # Affichage des fichiers trouvés
            if len(files) > 0:
                console.print("📋 Fichiers dans le dossier:")
                for file in files:
                    console.print(f"   - {file.name} ({file.length} bytes)")
            
            return True
            
        except Exception as e:
            console.print(f"❌ [red]Erreur lors du test des fichiers: {str(e)}[/red]")
            return False

    def create_test_file(self, folder_path: str = None, filename: str = "test-user-assigned-identity.txt") -> bool:
        """
        Crée un fichier de test dans le dossier SharePoint
        
        Args:
            folder_path: Chemin du dossier (par défaut: dossier de test configuré)
            filename: Nom du fichier à créer
            
        Returns:
            bool: True si la création réussit
        """
        if not self.ctx:
            console.print("❌ [red]Non authentifié. Appelez d'abord authenticate()[/red]")
            return False
            
        # Utilisation du dossier de test par défaut si non spécifié
        if folder_path is None:
            folder_path = os.getenv("SHAREPOINT_FOLDER_PATH", "Documents partages/General/Test-user-assigned-identity")
            
        try:
            console.print(f"📝 Création du fichier de test '{filename}' dans '{folder_path}'...")
            
            # Récupération du dossier
            folder = self.ctx.web.get_folder_by_server_relative_url(folder_path)
            self.ctx.load(folder)
            self.ctx.execute_query()
            
            # Contenu du fichier de test
            from datetime import datetime
            test_content = f"""Test User Assigned Identity - {filename}
Créé le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Authentification: Managed Identity
Site: {self.site_url}
Dossier: {folder_path}

Ce fichier a été créé automatiquement pour tester l'authentification SharePoint
avec Azure User Assigned Identity via Python.
"""
            
            # Création du fichier
            folder.upload_file(filename, test_content.encode('utf-8'))
            self.ctx.execute_query()
            
            console.print(f"✅ Fichier '{filename}' créé avec succès !")
            return True
            
        except Exception as e:
            console.print(f"❌ [red]Erreur lors de la création du fichier: {str(e)}[/red]")
            return False

def display_site_info(site_info: Dict[str, Any]):
    """Affiche les informations du site dans un tableau"""
    table = Table(title="Informations du Site SharePoint")
    table.add_column("Propriété", style="cyan")
    table.add_column("Valeur", style="green")
    
    for key, value in site_info.items():
        table.add_row(key, str(value))
    
    console.print(table)

def display_lists(lists_info: list):
    """Affiche les listes dans un tableau"""
    table = Table(title="Listes SharePoint")
    table.add_column("Titre", style="cyan")
    table.add_column("ID", style="blue")
    table.add_column("Nombre d'éléments", style="green")
    table.add_column("Cachée", style="yellow")
    
    for lst in lists_info:
        table.add_row(
            lst["title"],
            lst["id"],
            str(lst["item_count"]),
            "Oui" if lst["hidden"] else "Non"
        )
    
    console.print(table)

def main():
    """Fonction principale"""
    console.print("🚀 [bold blue]Test d'authentification SharePoint avec Managed Identity[/bold blue]")
    console.print("=" * 60)
    
    # Configuration
    site_url = os.getenv("SHAREPOINT_SITE_URL", "https://your-tenant.sharepoint.com/sites/your-site")
    use_managed_identity = os.getenv("USE_MANAGED_IDENTITY", "true").lower() == "true"  # True par défaut pour Azure
    
    console.print(f"🌐 Site SharePoint: {site_url}")
    console.print(f"🔐 Type d'authentification: {'Managed Identity' if use_managed_identity else 'DefaultAzureCredential'}")
    console.print()
    
    # Création de l'authentificateur
    authenticator = SharePointAuthenticator(site_url, use_managed_identity)
    
    # Authentification
    if not authenticator.authenticate():
        console.print("❌ [bold red]Échec de l'authentification. Arrêt du programme.[/bold red]")
        return
    
    console.print()
    
    # Récupération des informations du site
    site_info = authenticator.get_site_info()
    if site_info:
        display_site_info(site_info)
        console.print()
    
    # Liste des listes SharePoint
    lists_info = authenticator.list_lists()
    if lists_info:
        display_lists(lists_info)
        console.print()
    
    # Test des opérations de fichiers
    authenticator.test_file_operations()
    
    # Création d'un fichier de test
    console.print()
    console.print("📝 [bold blue]Test de création de fichier...[/bold blue]")
    authenticator.create_test_file()
    
    console.print()
    console.print("✅ [bold green]Test terminé avec succès ![/bold green]")

if __name__ == "__main__":
    main() 