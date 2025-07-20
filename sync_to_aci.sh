#!/bin/bash
#
# Script pour synchroniser les fichiers du projet vers l'ACI de développement
#

set -e

# Configuration
ACI_HOST="aci-dev"
REMOTE_WORKSPACE="/workspace"
LOCAL_DIR="."

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📁 Synchronisation des fichiers vers l'ACI${NC}"
echo -e "${BLUE}==========================================${NC}"

# Vérifier la connexion SSH
echo -e "\n${YELLOW}1. Test de connexion SSH...${NC}"
if ! ssh -o ConnectTimeout=5 "$ACI_HOST" "echo 'SSH OK'" >/dev/null 2>&1; then
    echo -e "${RED}❌ Impossible de se connecter à $ACI_HOST${NC}"
    echo -e "${YELLOW}💡 Exécutez d'abord: ./setup_aci_dev_environment.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Connexion SSH OK${NC}"

# Créer le dossier de destination s'il n'existe pas
echo -e "\n${YELLOW}2. Préparation du workspace distant...${NC}"
ssh "$ACI_HOST" "mkdir -p $REMOTE_WORKSPACE && chown vscode:vscode $REMOTE_WORKSPACE"
echo -e "${GREEN}✅ Workspace distant prêt${NC}"

# Synchroniser les fichiers (exclusions intelligentes)
echo -e "\n${YELLOW}3. Synchronisation des fichiers...${NC}"

# Créer un fichier .rsync-exclude temporaire
cat > .rsync-exclude << 'EOF'
.git/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage
.env
node_modules/
.DS_Store
.vscode/
.idea/
*.log
.rsync-exclude
EOF

# Synchroniser avec rsync via SSH
rsync -avz --progress \
    --exclude-from=.rsync-exclude \
    --delete \
    "$LOCAL_DIR/" \
    "$ACI_HOST:$REMOTE_WORKSPACE/"

# Nettoyer le fichier temporaire
rm -f .rsync-exclude

echo -e "${GREEN}✅ Synchronisation terminée${NC}"

# Vérifier la synchronisation
echo -e "\n${YELLOW}4. Vérification de la synchronisation...${NC}"
FILE_COUNT=$(ssh "$ACI_HOST" "find $REMOTE_WORKSPACE -type f | wc -l")
echo -e "${GREEN}✅ $FILE_COUNT fichiers synchronisés${NC}"

# Installer les dépendances si requirements.txt existe
if [ -f "requirements.txt" ]; then
    echo -e "\n${YELLOW}5. Installation des dépendances Python...${NC}"
    ssh "$ACI_HOST" "cd $REMOTE_WORKSPACE && pip3 install -r requirements.txt"
    echo -e "${GREEN}✅ Dépendances installées${NC}"
fi

# Rendre les scripts exécutables
echo -e "\n${YELLOW}6. Configuration des permissions...${NC}"
ssh "$ACI_HOST" "cd $REMOTE_WORKSPACE && find . -name '*.sh' -exec chmod +x {} \;"
ssh "$ACI_HOST" "cd $REMOTE_WORKSPACE && find . -name '*.py' -exec chmod +x {} \;"
echo -e "${GREEN}✅ Permissions configurées${NC}"

echo -e "\n${BLUE}==========================================${NC}"
echo -e "${GREEN}🎉 Synchronisation réussie !${NC}"
echo -e "${BLUE}==========================================${NC}"

echo -e "\n${YELLOW}🔗 Prochaines étapes:${NC}"
echo -e "${BLUE}# Se connecter à l'ACI${NC}"
echo -e "ssh $ACI_HOST"

echo -e "\n${BLUE}# Ouvrir avec VS Code Remote-SSH${NC}"
echo -e "code --remote ssh-remote+$ACI_HOST $REMOTE_WORKSPACE"

echo -e "\n${BLUE}# Tester SharePoint depuis l'ACI${NC}"
echo -e "ssh $ACI_HOST 'cd $REMOTE_WORKSPACE && python3 test_sharepoint_aci.py'"

echo -e "\n${GREEN}✅ Votre code est maintenant dans l'ACI !${NC}" 