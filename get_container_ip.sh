#!/bin/bash
#
# Script pour récupérer l'IP publique du Container Instance
# et afficher les informations de connexion SSH
#

set -e

# Variables de configuration (doivent correspondre à setup_aci_with_identity.sh)
RESOURCE_GROUP="rg-sharepoint-test"
CONTAINER_NAME="aci-sharepoint-test"
SSH_USER="developer"
SSH_PASSWORD="AzureDev2024!"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Récupération de l'IP du Container Instance${NC}"
echo -e "${BLUE}=============================================${NC}"

# Vérification de la connexion Azure
if ! az account show >/dev/null 2>&1; then
    echo -e "${RED}❌ Vous n'êtes pas connecté à Azure${NC}"
    echo -e "${BLUE}💡 Connectez-vous avec: az login${NC}"
    exit 1
fi

# Vérification que le container existe
if ! az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo -e "${RED}❌ Container '$CONTAINER_NAME' non trouvé dans le Resource Group '$RESOURCE_GROUP'${NC}"
    echo -e "${BLUE}💡 Exécutez d'abord: ./setup_aci_with_identity.sh${NC}"
    exit 1
fi

# Récupération de l'IP publique
echo -e "\n${YELLOW}📡 Récupération de l'IP publique...${NC}"
CONTAINER_IP=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query ipAddress.ip -o tsv)

if [ -z "$CONTAINER_IP" ] || [ "$CONTAINER_IP" = "None" ]; then
    echo -e "${RED}❌ Aucune IP publique trouvée pour le container${NC}"
    echo -e "${YELLOW}⏳ Le container est peut-être encore en cours de démarrage...${NC}"
    echo -e "${BLUE}💡 Attendez quelques minutes et relancez ce script${NC}"
    exit 1
fi

# Récupération du status du container
CONTAINER_STATE=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query instanceView.state -o tsv)

echo -e "${GREEN}✅ IP publique récupérée${NC}"
echo -e "\n${BLUE}=================================================================${NC}"
echo -e "${GREEN}🎉 Informations de connexion SSH${NC}"
echo -e "${BLUE}=================================================================${NC}"

echo -e "\n${YELLOW}📋 Détails du container:${NC}"
echo -e "   Resource Group: ${RESOURCE_GROUP}"
echo -e "   Container Name: ${CONTAINER_NAME}"
echo -e "   Status: ${CONTAINER_STATE}"
echo -e "   IP Publique: ${CONTAINER_IP}"

echo -e "\n${YELLOW}🔑 Identifiants SSH:${NC}"
echo -e "   Utilisateur: ${SSH_USER}"
echo -e "   Mot de passe: ${SSH_PASSWORD}"
echo -e "   Port: 22"

echo -e "\n${YELLOW}🔗 Commandes de connexion:${NC}"
echo -e "${BLUE}# Connexion SSH directe${NC}"
echo -e "ssh ${SSH_USER}@${CONTAINER_IP}"

echo -e "\n${BLUE}# Connexion avec port explicite${NC}"
echo -e "ssh -p 22 ${SSH_USER}@${CONTAINER_IP}"

echo -e "\n${YELLOW}📝 Configuration Remote SSH dans Cursor:${NC}"
echo -e "${BLUE}1. Ouvrez Cursor${NC}"
echo -e "${BLUE}2. Appuyez sur Ctrl+Shift+P (ou Cmd+Shift+P sur Mac)${NC}"
echo -e "${BLUE}3. Tapez 'Remote-SSH: Connect to Host'${NC}"
echo -e "${BLUE}4. Entrez: ${SSH_USER}@${CONTAINER_IP}${NC}"
echo -e "${BLUE}5. Choisissez 'Linux' comme plateforme${NC}"
echo -e "${BLUE}6. Entrez le mot de passe: ${SSH_PASSWORD}${NC}"

echo -e "\n${YELLOW}⚠️  Notes importantes:${NC}"
echo -e "${BLUE}• Le container doit être en état 'Running' pour la connexion SSH${NC}"
echo -e "${BLUE}• L'IP peut changer si le container est redémarré${NC}"
echo -e "${BLUE}• Le premier démarrage peut prendre 2-3 minutes${NC}"

if [ "$CONTAINER_STATE" != "Running" ]; then
    echo -e "\n${YELLOW}⏳ Container en cours de démarrage (Status: ${CONTAINER_STATE})${NC}"
    echo -e "${BLUE}💡 Attendez que le status soit 'Running' avant de vous connecter${NC}"
fi

echo -e "\n${GREEN}✅ Script terminé!${NC}" 