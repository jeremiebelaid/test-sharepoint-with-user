#!/bin/bash

# Configuration
RESOURCE_GROUP="sharepoint-test-rg"
LOCATION="westeurope"
IDENTITY_NAME="sharepoint-auth-identity"
CONTAINER_APP_NAME="sharepoint-auth-test"
ACR_NAME="sharepointtestacr"
IMAGE_NAME="python-sharepoint"
IMAGE_TAG="latest"

echo "🚀 Déploiement de l'environnement SharePoint avec Managed Identity"
echo "================================================================"

# 1. Création du groupe de ressources
echo "📦 Création du groupe de ressources..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Création du Container Registry
echo "📦 Création du Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# 3. Connexion au Container Registry
echo "🔗 Connexion au Container Registry..."
az acr login --name $ACR_NAME

# 4. Création de la User Assigned Identity
echo "🆔 Création de la User Assigned Identity..."
az identity create --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP

# 5. Récupération des informations de l'identity
IDENTITY_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)
PRINCIPAL_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)

echo "✅ Identity créée: $IDENTITY_ID"

# 6. Attribution des permissions SharePoint (via Microsoft Graph)
echo "🔐 Attribution des permissions SharePoint..."
az ad app permission add --id $PRINCIPAL_ID --api 00000003-0000-0000-c000-000000000000 --api-permissions Sites.Read.All
az ad app permission add --id $PRINCIPAL_ID --api 00000003-0000-0000-c000-000000000000 --api-permissions Files.Read.All

# 7. Build et push de l'image Docker
echo "🏗️ Build de l'image Docker..."
az acr build --registry $ACR_NAME --image $IMAGE_NAME:$IMAGE_TAG .

# 8. Création de l'environnement Container Apps
echo "🌍 Création de l'environnement Container Apps..."
az containerapp env create \
  --name "sharepoint-env" \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 9. Déploiement de l'application
echo "🚀 Déploiement de l'application..."
az containerapp create \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment "sharepoint-env" \
  --image "$ACR_NAME.azurecr.io/$IMAGE_NAME:$IMAGE_TAG" \
  --user-assigned $IDENTITY_ID \
  --env-vars SHAREPOINT_SITE_URL="https://ddasys.sharepoint.com/sites/DDASYS" USE_MANAGED_IDENTITY="true" SHAREPOINT_FOLDER_PATH="Documents partages/General/Test-user-assigned-identity"

echo "✅ Déploiement terminé !"
echo "🔗 URL de l'application: https://$CONTAINER_APP_NAME.azurecontainerapps.io"
echo "🆔 Identity ID: $IDENTITY_ID" 