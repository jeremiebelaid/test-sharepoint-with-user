#!/bin/bash

# Configuration Azure CLI pour le projet
echo "🔧 Configuration Azure CLI pour SharePoint Auth"

# Variables de configuration
RESOURCE_GROUP="sharepoint-test-rg"
LOCATION="westeurope"
IDENTITY_NAME="sharepoint-auth-identity"

# Vérification de la connexion Azure
echo "🔍 Vérification de la connexion Azure..."
az account show

if [ $? -ne 0 ]; then
    echo "❌ Non connecté à Azure. Veuillez vous connecter avec 'az login'"
    exit 1
fi

# Affichage des informations de l'identity
echo "🆔 Informations de l'User Assigned Identity..."
az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP

# Affichage des permissions
echo "🔐 Permissions de l'identity..."
PRINCIPAL_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
az ad app permission list --id $PRINCIPAL_ID

echo "✅ Configuration terminée" 