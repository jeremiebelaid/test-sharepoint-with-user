#!/usr/bin/env python3
"""
Script de test utilisant l'API Microsoft Graph
pour vérifier l'accès SharePoint avec AzureCliCredential
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv('config.env')


def test_graph_api_access():
    """Test d'accès à SharePoint via Microsoft Graph API"""
    print("🔍 Test d'accès SharePoint via Microsoft Graph API")
    print("=" * 60)
    
    try:
        from azure.identity import AzureCliCredential
        
        # Configuration
        site_url = os.getenv("SHAREPOINT_SITE_URL")
        
        if not site_url:
            print("❌ URL SharePoint non configurée")
            return False
            
        print(f"🌐 Site SharePoint: {site_url}")
        print()
        
        # Obtention du credential
        print("🔐 Obtention du credential Azure CLI...")
        credential = AzureCliCredential()
        
        # Obtention du token pour Microsoft Graph
        print("🎫 Obtention du token Microsoft Graph...")
        token = credential.get_token("https://graph.microsoft.com/.default")
        print(f"✅ Token obtenu avec succès (expire dans "
              f"{token.expires_on} secondes)")
        
        # Extraction de l'ID du site depuis l'URL
        # Format: https://tenant.sharepoint.com/sites/site-name
        site_parts = site_url.split('/')
        if len(site_parts) >= 5:
            tenant = site_parts[2]  # tenant.sharepoint.com
            site_name = site_parts[4]  # sites/site-name
        else:
            print("❌ Format d'URL SharePoint invalide")
            return False
        
        # Test d'accès au site via Microsoft Graph
        print(f"🌐 Test d'accès au site: {site_name}")
        print(f"🏢 Tenant: {tenant}")
        
        headers = {
            'Authorization': f'Bearer {token.token}',
            'Content-Type': 'application/json'
        }
        
        # Récupération des informations du site
        # Utilisation de l'URL complète du tenant
        graph_url = f"https://graph.microsoft.com/v1.0/sites/{tenant}:/sites/{site_name}"
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            site_info = response.json()
            print(f"✅ Site trouvé: {site_info.get('displayName', 'N/A')}")
            print(f"📍 ID du site: {site_info.get('id', 'N/A')}")
            
            # Test d'accès aux listes du site
            print("\n📋 Test d'accès aux listes du site...")
            lists_url = f"{graph_url}/lists"
            lists_response = requests.get(lists_url, headers=headers)
            
            if lists_response.status_code == 200:
                lists_data = lists_response.json()
                lists = lists_data.get('value', [])
                print(f"✅ Nombre de listes trouvées: {len(lists)}")
                
                if lists:
                    print("📋 Listes disponibles:")
                    for lst in lists[:5]:  # Afficher les 5 premières
                        print(f"   - {lst.get('displayName', 'N/A')} "
                              f"({lst.get('list', {}).get('template', 'N/A')})")
            else:
                print(f"⚠️  Erreur d'accès aux listes: "
                      f"{lists_response.status_code}")
            
            # Test d'accès aux fichiers du site
            print("\n📁 Test d'accès aux fichiers du site...")
            drive_url = f"{graph_url}/drive"
            drive_response = requests.get(drive_url, headers=headers)
            
            if drive_response.status_code == 200:
                drive_info = drive_response.json()
                print(f"✅ Drive trouvé: {drive_info.get('name', 'N/A')}")
                
                # Test d'accès aux éléments racine
                root_url = f"{drive_url}/root/children"
                root_response = requests.get(root_url, headers=headers)
                
                if root_response.status_code == 200:
                    root_data = root_response.json()
                    items = root_data.get('value', [])
                    print(f"📄 Nombre d'éléments à la racine: {len(items)}")
                    
                    if items:
                        print("📋 Éléments à la racine:")
                        for item in items[:5]:  # Afficher les 5 premiers
                            item_type = "📁" if item.get('folder') else "📄"
                            print(f"   {item_type} {item.get('name', 'N/A')}")
                else:
                    print(f"⚠️  Erreur d'accès aux éléments racine: "
                          f"{root_response.status_code}")
            else:
                print(f"⚠️  Erreur d'accès au drive: "
                      f"{drive_response.status_code}")
                
        else:
            print(f"❌ Erreur d'accès au site: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
        
        print("\n✅ [bold green]Test d'accès Microsoft Graph réussi !"
              "[/bold green]")
        print("\n🚀 Pour tester avec Managed Identity sur Azure:")
        print("   ./deploy.sh")
        
        return True
        
    except ImportError as e:
        print(f"❌ [red]Module manquant: {str(e)}[/red]")
        print("💡 Installez les dépendances avec: pip install -r "
              "requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ [red]Erreur d'authentification: {str(e)}[/red]")
        print("\n💡 Solutions possibles:")
        print("   1. Connectez-vous à Azure: az login")
        print("   2. Vérifiez vos permissions SharePoint")
        print("   3. Vérifiez que vous avez accès au site SharePoint")
        return False


if __name__ == "__main__":
    success = test_graph_api_access()
    sys.exit(0 if success else 1) 