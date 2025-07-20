#!/bin/bash
#
# Script de configuration Azure pour créer un Container Instance (ACI)
# avec User Assigned Identity pour tester SharePoint DDASYS
#

set -e  # Arrêter en cas d'erreur

# Variables de configuration
RESOURCE_GROUP="rg-sharepoint-test"
LOCATION="West Europe"
USER_IDENTITY_NAME="id-sharepoint-test"
CONTAINER_NAME="aci-sharepoint-test"
ACR_NAME="${ACR_NAME:-acrsharepointtest1752842614}" # Utilise la variable d'environnement ou une valeur par défaut
IMAGE_NAME="$ACR_NAME.azurecr.io/aci-dev:latest"

# Configuration SSH
SSH_USER="developer"
SSH_PASSWORD="AzureDev2024!"
SSH_PORT="22"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Configuration Azure Container Instance avec User Assigned Identity${NC}"
echo -e "${BLUE}=================================================================${NC}"

# 1. Vérification de la connexion Azure
echo -e "\n${YELLOW}1. Vérification de la connexion Azure...${NC}"
if ! az account show >/dev/null 2>&1; then
    echo -e "${RED}❌ Vous n'êtes pas connecté à Azure${NC}"
    echo -e "${BLUE}💡 Connectez-vous avec: az login${NC}"
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)
USER_EMAIL=$(az account show --query user.name -o tsv)

echo -e "${GREEN}✅ Connecté à Azure${NC}"
echo -e "   Subscription: ${SUBSCRIPTION_ID}"
echo -e "   Tenant: ${TENANT_ID}"
echo -e "   User: ${USER_EMAIL}"

# 2. Création du Resource Group
echo -e "\n${YELLOW}2. Création du Resource Group...${NC}"
if az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Resource Group '$RESOURCE_GROUP' existe déjà${NC}"
else
    echo -e "${BLUE}📁 Création du Resource Group '$RESOURCE_GROUP'...${NC}"
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION"
    echo -e "${GREEN}✅ Resource Group créé${NC}"
fi

# 3. Création de la User Assigned Identity
echo -e "\n${YELLOW}3. Création de la User Assigned Identity...${NC}"
if az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ User Assigned Identity '$USER_IDENTITY_NAME' existe déjà${NC}"
else
    echo -e "${BLUE}🔐 Création de la User Assigned Identity '$USER_IDENTITY_NAME'...${NC}"
    az identity create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$USER_IDENTITY_NAME"
    echo -e "${GREEN}✅ User Assigned Identity créée${NC}"
fi

# Récupération des informations de l'identité
IDENTITY_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query id -o tsv)
IDENTITY_CLIENT_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query clientId -o tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query principalId -o tsv)

echo -e "   Identity ID: ${IDENTITY_ID}"
echo -e "   Client ID: ${IDENTITY_CLIENT_ID}"
echo -e "   Principal ID: ${IDENTITY_PRINCIPAL_ID}"

# 4. Vérification du fournisseur Microsoft.ContainerInstance
echo -e "\n${YELLOW}4. Vérification du fournisseur Container Instance...${NC}"
PROVIDER_STATUS=$(az provider show -n Microsoft.ContainerInstance --query "registrationState" -o tsv)
if [ "$PROVIDER_STATUS" != "Registered" ]; then
    echo -e "${YELLOW}⚠️  Fournisseur Microsoft.ContainerInstance non enregistré (Status: $PROVIDER_STATUS)${NC}"
    echo -e "${BLUE}🔧 Enregistrement du fournisseur...${NC}"
    az provider register --namespace Microsoft.ContainerInstance
    
    # Attendre l'enregistrement
    echo -e "${BLUE}⏳ Attente de l'enregistrement (peut prendre 1-2 minutes)...${NC}"
    while [ "$(az provider show -n Microsoft.ContainerInstance --query 'registrationState' -o tsv)" != "Registered" ]; do
        echo -e "   Status: $(az provider show -n Microsoft.ContainerInstance --query 'registrationState' -o tsv)"
        sleep 10
    done
    echo -e "${GREEN}✅ Fournisseur Microsoft.ContainerInstance enregistré${NC}"
else
    echo -e "${GREEN}✅ Fournisseur Microsoft.ContainerInstance déjà enregistré${NC}"
fi

# 5. Attribution des permissions SharePoint à l'identité
echo -e "\n${YELLOW}5. Attribution des permissions SharePoint...${NC}"
echo -e "${BLUE}🔑 Attribution des rôles Microsoft Graph API...${NC}"

# Obtenir l'ID de l'application Microsoft Graph
GRAPH_APP_ID="00000003-0000-0000-c000-000000000000"

# Permissions nécessaires pour SharePoint
declare -a PERMISSIONS=(
    "Sites.ReadWrite.All"
    "Files.ReadWrite.All"
    "User.Read"
)

echo -e "${BLUE}📝 Permissions à attribuer:${NC}"
for permission in "${PERMISSIONS[@]}"; do
    echo -e "   - ${permission}"
done

# Note: L'attribution des permissions API nécessite des droits d'administrateur
echo -e "\n${RED}⚠️  IMPORTANT: Attribution des permissions API${NC}"
echo -e "${YELLOW}Les permissions Microsoft Graph doivent être attribuées par un administrateur Azure AD.${NC}"
echo -e "${YELLOW}Exécutez le script setup_graph_permissions.sh avec des droits d'administrateur:${NC}"
echo -e "${BLUE}./setup_graph_permissions.sh${NC}"

# 6. Création du Container Instance
echo -e "\n${YELLOW}6. Création du Container Instance...${NC}"

# Vérifier si le container existe déjà
if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Container '$CONTAINER_NAME' existe déjà${NC}"
    echo -e "${BLUE}🗑️  Suppression du container existant...${NC}"
    az container delete \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --yes
    echo -e "${GREEN}✅ Container supprimé${NC}"
fi

echo -e "${BLUE}🐳 Création du Container Instance '$CONTAINER_NAME'...${NC}"

# Créer le container avec l'identité assignée et SSH configuré
az container create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$CONTAINER_NAME" \
    --image "$IMAGE_NAME" \
    --os-type Linux \
    --assign-identity "$IDENTITY_ID" \
    --acr-identity "$IDENTITY_ID" \
    --ip-address Public \
    --dns-name-label "$CONTAINER_NAME-$RANDOM" \
    --cpu 1 \
    --memory 2 \
    --restart-policy Never \
    --ports "$SSH_PORT" \
    --environment-variables \
        AZURE_CLIENT_ID="$IDENTITY_CLIENT_ID" \
        SHAREPOINT_SITE_ID="ddasys.sharepoint.com,90022be8-5b4d-437e-b7b8-428a5b4a9d75,dfdecd9e-4cd3-470d-a08f-e0b602bf8390" \
        SHAREPOINT_DRIVE_ID="b!6CsCkE1bfkO3uEKKW0qddZ7N3t_TTA1HoI_gtgK_g5BfZDakrgbgT4Irvjj_zI02" \
        SHAREPOINT_FOLDER_PATH="Documents partages/General/Test-user-assigned-identity"

echo -e "${GREEN}✅ Container Instance créé${NC}"

# 7. Vérification du status du container
echo -e "\n${YELLOW}7. Vérification du status du container...${NC}"
sleep 10

CONTAINER_STATE=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query instanceView.state -o tsv)
echo -e "   Status: ${CONTAINER_STATE}"

if [ "$CONTAINER_STATE" = "Running" ]; then
    echo -e "${GREEN}✅ Container en cours d'exécution${NC}"
else
    echo -e "${YELLOW}⏳ Container en cours de démarrage...${NC}"
fi

# 8. Instructions de connexion
echo -e "\n${BLUE}=================================================================${NC}"
echo -e "${GREEN}🎉 Configuration terminée avec succès!${NC}"
echo -e "${BLUE}=================================================================${NC}"

echo -e "\n${YELLOW}📋 Informations de votre environnement:${NC}"
echo -e "   Resource Group: ${RESOURCE_GROUP}"
echo -e "   Container Name: ${CONTAINER_NAME}"
echo -e "   Identity Name: ${USER_IDENTITY_NAME}"
echo -e "   Client ID: ${IDENTITY_CLIENT_ID}"

echo -e "\n${YELLOW}🔗 Informations de connexion SSH:${NC}"
echo -e "${BLUE}# Récupérer l'IP publique du container${NC}"
echo -e "az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.ip -o tsv"

echo -e "\n${BLUE}# Connexion SSH (remplacez IP_ADDRESS par l'IP obtenue ci-dessus)${NC}"
echo -e "ssh $SSH_USER@IP_ADDRESS"

echo -e "\n${YELLOW}🔑 Identifiants SSH:${NC}"
echo -e "   Utilisateur: ${SSH_USER}"
echo -e "   Mot de passe: ${SSH_PASSWORD}"
echo -e "   Port: ${SSH_PORT}"

echo -e "\n${YELLOW}🔗 Commandes de gestion du container:${NC}"
echo -e "${BLUE}# Se connecter au container via Azure CLI${NC}"
echo -e "az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command /bin/bash"

echo -e "\n${BLUE}# Voir les logs du container${NC}"
echo -e "az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"

echo -e "\n${BLUE}# Redémarrer le container${NC}"
echo -e "az container restart --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"

echo -e "\n${BLUE}# Supprimer le container (si nécessaire)${NC}"
echo -e "az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes"

echo -e "\n${YELLOW}🚀 Prochaines étapes:${NC}"
echo -e "1. ${BLUE}Configurez les permissions Microsoft Graph avec: ./setup_graph_permissions.sh${NC}"
echo -e "2. ${BLUE}Récupérez l'IP publique du container${NC}"
echo -e "3. ${BLUE}Connectez-vous en SSH depuis Cursor avec Remote SSH${NC}"
echo -e "4. ${BLUE}Installez Python et les dépendances nécessaires${NC}"
echo -e "5. ${BLUE}Testez votre script SharePoint${NC}"

echo -e "\n${YELLOW}📝 Configuration Remote SSH dans Cursor:${NC}"
echo -e "${BLUE}1. Ouvrez Cursor${NC}"
echo -e "${BLUE}2. Appuyez sur Ctrl+Shift+P (ou Cmd+Shift+P sur Mac)${NC}"
echo -e "${BLUE}3. Tapez 'Remote-SSH: Connect to Host'${NC}"
echo -e "${BLUE}4. Entrez: $SSH_USER@IP_ADDRESS${NC}"
echo -e "${BLUE}5. Choisissez 'Linux' comme plateforme${NC}"
echo -e "${BLUE}6. Entrez le mot de passe: $SSH_PASSWORD${NC}"

echo -e "\n${GREEN}✅ Setup terminé!${NC}" 