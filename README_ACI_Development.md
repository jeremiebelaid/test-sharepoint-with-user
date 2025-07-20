# 🚀 Environnement de développement Azure Container Instance (ACI)

Ce guide vous explique comment utiliser votre Azure Container Instance comme environnement de développement remote avec VS Code et devcontainers.

## 🎯 Avantages de cette approche

- ✅ **User Assigned Identity** : Accès direct à SharePoint depuis l'ACI
- ✅ **Environnement cloud** : Pas de configuration locale complexe
- ✅ **VS Code Remote-SSH** : Développement natif dans l'ACI
- ✅ **Synchronisation automatique** : Vos fichiers locaux vers l'ACI
- ✅ **Isolation** : Environnement de test séparé de votre machine locale

## 📋 Prérequis

- Azure CLI installé et connecté (`az login`)
- VS Code avec l'extension **Remote - SSH**
- User Assigned Identity configurée (voir section précédente)

## 🔧 Configuration initiale

### 1. Créer l'environnement de développement ACI

```bash
# Configurer l'ACI avec SSH et environnement de développement
./setup_aci_dev_environment.sh
```

Ce script va :
- ✅ Générer une clé SSH (si nécessaire)
- ✅ Créer un ACI avec IP publique et SSH
- ✅ Installer Python, Git, et toutes les dépendances
- ✅ Configurer l'utilisateur `vscode` avec sudo
- ✅ Configurer les variables d'environnement SharePoint
- ✅ Tester la connexion SSH

### 2. Synchroniser vos fichiers vers l'ACI

```bash
# Synchroniser le projet vers l'ACI
./sync_to_aci.sh
```

Ce script va :
- ✅ Copier tous vos fichiers vers `/workspace` dans l'ACI
- ✅ Installer les dépendances Python (`requirements.txt`)
- ✅ Configurer les permissions des fichiers

## 🖥️ Développement avec VS Code Remote-SSH

### Option 1 : Connexion directe SSH

```bash
# Se connecter à l'ACI via SSH
ssh aci-dev

# Dans l'ACI, aller au workspace
cd /workspace

# Tester SharePoint
python3 test_sharepoint_aci.py
```

### Option 2 : VS Code Remote-SSH (Recommandé)

1. **Ouvrir VS Code**
2. **Installer l'extension "Remote - SSH"**
3. **Connecter à l'ACI** :
   - Ctrl+Shift+P → "Remote-SSH: Connect to Host"
   - Sélectionner `aci-dev`
   - Ouvrir le dossier `/workspace`

4. **Configuration automatique** :
   - VS Code détectera le devcontainer
   - Les extensions Python seront installées automatiquement
   - L'environnement sera configuré selon `.devcontainer/devcontainer-aci.json`

### Option 3 : Commande directe

```bash
# Ouvrir VS Code directement dans l'ACI
code --remote ssh-remote+aci-dev /workspace
```

## 📁 Structure de fichiers dans l'ACI

```
/workspace/                          # Votre projet synchronisé
├── config.env                      # Configuration SharePoint
├── test_sharepoint_aci.py          # Script de test pour ACI
├── test_sharepoint_with_ids.py     # Script optimisé local
├── extract_sharepoint_ids_ddasys.py # Extraction d'IDs
├── .devcontainer/
│   ├── devcontainer.json           # Config devcontainer local
│   └── devcontainer-aci.json       # Config devcontainer ACI
├── setup_*.sh                      # Scripts de configuration
└── requirements.txt                # Dépendances Python
```

## 🔄 Workflow de développement

### 1. Développement local → ACI

```bash
# Modifier votre code localement
vim test_sharepoint_aci.py

# Synchroniser vers l'ACI
./sync_to_aci.sh

# Tester dans l'ACI
ssh aci-dev 'cd /workspace && python3 test_sharepoint_aci.py'
```

### 2. Développement direct dans l'ACI

```bash
# Ouvrir VS Code dans l'ACI
code --remote ssh-remote+aci-dev /workspace

# Développer directement dans l'environnement cloud
# Vos modifications sont automatiquement dans l'ACI
```

### 3. Récupérer les modifications ACI → Local

```bash
# Synchroniser depuis l'ACI vers local (si modifications dans l'ACI)
scp -r aci-dev:/workspace/ ./
```

## 🧪 Test SharePoint dans l'ACI

### Test simple

```bash
# Se connecter à l'ACI
ssh aci-dev

# Aller au workspace
cd /workspace

# Tester SharePoint avec User Assigned Identity
python3 test_sharepoint_aci.py
```

### Test avec debugging

```bash
# Dans l'ACI, activer le mode verbose
ssh aci-dev
cd /workspace

# Test avec plus de détails
python3 -c "
import os
print('🔑 AZURE_CLIENT_ID:', os.getenv('AZURE_CLIENT_ID'))
print('📍 SHAREPOINT_SITE_ID:', os.getenv('SHAREPOINT_SITE_ID')[:50] + '...')
print('📁 SHAREPOINT_DRIVE_ID:', os.getenv('SHAREPOINT_DRIVE_ID')[:50] + '...')
"
```

## 🛠️ Commandes utiles

### Gestion de l'ACI

```bash
# Voir le statut de l'ACI
az container show --resource-group rg-sharepoint-test --name aci-sharepoint-dev --query instanceView.state -o tsv

# Redémarrer l'ACI
az container restart --resource-group rg-sharepoint-test --name aci-sharepoint-dev

# Voir les logs de l'ACI
az container logs --resource-group rg-sharepoint-test --name aci-sharepoint-dev

# Supprimer l'ACI
az container delete --resource-group rg-sharepoint-test --name aci-sharepoint-dev --yes
```

### Synchronisation

```bash
# Synchronisation rapide (fichiers modifiés seulement)
rsync -avz --progress . aci-dev:/workspace/

# Synchronisation complète
./sync_to_aci.sh

# Copier un seul fichier
scp test_sharepoint_aci.py aci-dev:/workspace/
```

### SSH et connexion

```bash
# Test de connexion SSH
ssh -o ConnectTimeout=5 aci-dev "echo 'SSH OK'"

# Se connecter avec redirection de port
ssh -L 8080:localhost:8080 aci-dev

# Copier la clé SSH publique (si problème de connexion)
ssh-copy-id -i ~/.ssh/id_rsa.pub aci-dev
```

## 🔍 Troubleshooting

### Problème de connexion SSH

```bash
# Vérifier l'IP de l'ACI
az container show --resource-group rg-sharepoint-test --name aci-sharepoint-dev --query ipAddress.ip -o tsv

# Reconfigurer SSH
./setup_aci_dev_environment.sh
```

### Problème de permissions

```bash
# Dans l'ACI, corriger les permissions
ssh aci-dev "sudo chown -R vscode:vscode /workspace"
```

### Variables d'environnement manquantes

```bash
# Vérifier les variables dans l'ACI
ssh aci-dev 'env | grep -E "(AZURE|SHAREPOINT)"'

# Redémarrer l'ACI si nécessaire
az container restart --resource-group rg-sharepoint-test --name aci-sharepoint-dev
```

## 🎯 Résultat attendu

Quand tout fonctionne, vous devriez pouvoir :

1. ✅ Vous connecter à l'ACI via SSH ou VS Code Remote-SSH
2. ✅ Développer dans `/workspace` avec toutes vos extensions VS Code
3. ✅ Exécuter `python3 test_sharepoint_aci.py` avec succès
4. ✅ Créer des fichiers dans SharePoint DDASYS depuis l'ACI
5. ✅ Utiliser la User Assigned Identity sans configuration supplémentaire

## 🚀 Next Steps

Une fois votre environnement de développement ACI fonctionnel, vous pouvez :
- Développer vos scripts SharePoint directement dans le cloud
- Tester avec des permissions réalistes (User Assigned Identity)
- Préparer vos solutions pour la production
- Utiliser l'ACI comme environnement de staging

---

**🎉 Votre environnement de développement cloud est prêt !** 