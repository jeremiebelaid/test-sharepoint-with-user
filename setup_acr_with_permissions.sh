#!/bin/bash
#
# Script de configuration Azure Container Registry (ACR)
# avec permissions pour User Assigned Identity
#

set -e  # Arrêter en cas d'erreur

# Variables de configuration
RESOURCE_GROUP="rg-sharepoint-test"
LOCATION="West Europe"
USER_IDENTITY_NAME="id-sharepoint-test"
ACR_NAME="acrsharepointtest$(date +%s)"  # Nom unique avec timestamp
ACR_SKU="Basic"  # Basic, Standard, Premium

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Configuration Azure Container Registry avec permissions${NC}"
echo -e "${BLUE}=====================================================${NC}"

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

# 2. Vérification du Resource Group
echo -e "\n${YELLOW}2. Vérification du Resource Group...${NC}"
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo -e "${RED}❌ Resource Group '$RESOURCE_GROUP' non trouvé${NC}"
    echo -e "${BLUE}💡 Créez d'abord le Resource Group avec: ./setup_aci_with_identity.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Resource Group '$RESOURCE_GROUP' trouvé${NC}"

# 3. Vérification de la User Assigned Identity
echo -e "\n${YELLOW}3. Vérification de la User Assigned Identity...${NC}"
if ! az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" >/dev/null 2>&1; then
    echo -e "${RED}❌ User Assigned Identity '$USER_IDENTITY_NAME' non trouvée${NC}"
    echo -e "${BLUE}💡 Créez d'abord l'identité avec: ./setup_aci_with_identity.sh${NC}"
    exit 1
fi

IDENTITY_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query id -o tsv)
IDENTITY_CLIENT_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query clientId -o tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query principalId -o tsv)

echo -e "${GREEN}✅ User Assigned Identity trouvée${NC}"
echo -e "   Identity ID: ${IDENTITY_ID}"
echo -e "   Client ID: ${IDENTITY_CLIENT_ID}"
echo -e "   Principal ID: ${IDENTITY_PRINCIPAL_ID}"

# 4. Vérification du fournisseur Microsoft.ContainerRegistry
echo -e "\n${YELLOW}4. Vérification du fournisseur Container Registry...${NC}"
PROVIDER_STATUS=$(az provider show -n Microsoft.ContainerRegistry --query "registrationState" -o tsv)
if [ "$PROVIDER_STATUS" != "Registered" ]; then
    echo -e "${YELLOW}⚠️  Fournisseur Microsoft.ContainerRegistry non enregistré (Status: $PROVIDER_STATUS)${NC}"
    echo -e "${BLUE}🔧 Enregistrement du fournisseur...${NC}"
    az provider register --namespace Microsoft.ContainerRegistry
    
    # Attendre l'enregistrement
    echo -e "${BLUE}⏳ Attente de l'enregistrement (peut prendre 1-2 minutes)...${NC}"
    while [ "$(az provider show -n Microsoft.ContainerRegistry --query 'registrationState' -o tsv)" != "Registered" ]; do
        echo -e "   Status: $(az provider show -n Microsoft.ContainerRegistry --query 'registrationState' -o tsv)"
        sleep 10
    done
    echo -e "${GREEN}✅ Fournisseur Microsoft.ContainerRegistry enregistré${NC}"
else
    echo -e "${GREEN}✅ Fournisseur Microsoft.ContainerRegistry déjà enregistré${NC}"
fi

# 5. Création de l'Azure Container Registry
echo -e "\n${YELLOW}5. Création de l'Azure Container Registry...${NC}"

# Vérifier si l'ACR existe déjà
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ ACR '$ACR_NAME' existe déjà${NC}"
else
    echo -e "${BLUE}🏗️  Création de l'ACR '$ACR_NAME'...${NC}"
    az acr create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$ACR_NAME" \
        --sku "$ACR_SKU" \
        --admin-enabled true \
        --location "$LOCATION"
    echo -e "${GREEN}✅ ACR créé${NC}"
fi

# Récupération des informations de l'ACR
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
ACR_ID=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query id -o tsv)

echo -e "   ACR Name: ${ACR_NAME}"
echo -e "   Login Server: ${ACR_LOGIN_SERVER}"
echo -e "   ACR ID: ${ACR_ID}"

# 6. Attribution des permissions à la User Assigned Identity
echo -e "\n${YELLOW}6. Attribution des permissions ACR à l'identité...${NC}"

# Rôles nécessaires pour l'ACR
declare -a ACR_ROLES=(
    "AcrPush"      # Permet de pousser des images
    "AcrPull"      # Permet de tirer des images
    "AcrDelete"    # Permet de supprimer des images
)

echo -e "${BLUE}🔑 Attribution des rôles ACR...${NC}"
for role in "${ACR_ROLES[@]}"; do
    echo -e "${BLUE}📝 Attribution du rôle: ${role}${NC}"
    
    # Vérifier si le rôle est déjà attribué
    if az role assignment list --assignee "$IDENTITY_PRINCIPAL_ID" --scope "$ACR_ID" --query "[?roleDefinitionName=='$role']" --output table | grep -q "$role"; then
        echo -e "${GREEN}✅ Rôle ${role} déjà attribué${NC}"
    else
        az role assignment create \
            --assignee "$IDENTITY_PRINCIPAL_ID" \
            --role "$role" \
            --scope "$ACR_ID"
        echo -e "${GREEN}✅ Rôle ${role} attribué${NC}"
    fi
done

# 7. Configuration de l'authentification ACR
echo -e "\n${YELLOW}7. Configuration de l'authentification ACR...${NC}"

# Récupérer les credentials admin
echo -e "${BLUE}🔐 Récupération des credentials admin...${NC}"
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)

echo -e "${GREEN}✅ Credentials récupérés${NC}"
echo -e "   Username: ${ACR_USERNAME}"
echo -e "   Password: ${ACR_PASSWORD}"

# 8. Instructions pour utiliser l'ACR
echo -e "\n${BLUE}=================================================================${NC}"
echo -e "${GREEN}🎉 Azure Container Registry configuré avec succès!${NC}"
echo -e "${BLUE}=================================================================${NC}"

echo -e "\n${YELLOW}📋 Informations de votre ACR:${NC}"
echo -e "   Resource Group: ${RESOURCE_GROUP}"
echo -e "   ACR Name: ${ACR_NAME}"
echo -e "   Login Server: ${ACR_LOGIN_SERVER}"
echo -e "   SKU: ${ACR_SKU}"
echo -e "   Identity: ${USER_IDENTITY_NAME}"

echo -e "\n${YELLOW}🔑 Credentials ACR:${NC}"
echo -e "   Username: ${ACR_USERNAME}"
echo -e "   Password: ${ACR_PASSWORD}"

echo -e "\n${YELLOW}🔗 Commandes pour utiliser l'ACR:${NC}"
echo -e "${BLUE}# Se connecter à l'ACR${NC}"
echo -e "az acr login --name ${ACR_NAME}"

echo -e "\n${BLUE}# Tagger une image pour l'ACR${NC}"
echo -e "docker tag ubuntu:22.04 ${ACR_LOGIN_SERVER}/ubuntu:22.04"

echo -e "\n${BLUE}# Pousser une image vers l'ACR${NC}"
echo -e "docker push ${ACR_LOGIN_SERVER}/ubuntu:22.04"

echo -e "\n${BLUE}# Tirer une image depuis l'ACR${NC}"
echo -e "docker pull ${ACR_LOGIN_SERVER}/ubuntu:22.04"

echo -e "\n${YELLOW}🚀 Prochaines étapes:${NC}"
echo -e "1. ${BLUE}Créez une image Ubuntu personnalisée avec SSH${NC}"
echo -e "2. ${BLUE}Poussez l'image vers votre ACR${NC}"
echo -e "3. ${BLUE}Modifiez le script ACI pour utiliser votre image ACR${NC}"
echo -e "4. ${BLUE}Testez le déploiement avec votre image personnalisée${NC}"

echo -e "\n${YELLOW}📝 Variables à utiliser dans vos scripts:${NC}"
echo -e "export ACR_NAME=\"${ACR_NAME}\""
echo -e "export ACR_LOGIN_SERVER=\"${ACR_LOGIN_SERVER}\""
echo -e "export ACR_USERNAME=\"${ACR_USERNAME}\""
echo -e "export ACR_PASSWORD=\"${ACR_PASSWORD}\""

echo -e "\n${GREEN}✅ Setup ACR terminé!${NC}" 