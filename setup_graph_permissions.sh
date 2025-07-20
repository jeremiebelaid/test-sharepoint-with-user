#!/bin/bash
#
# Script d'aide pour configurer les permissions Microsoft Graph
# ⚠️  À EXÉCUTER AVEC DES DROITS D'ADMINISTRATEUR AZURE AD
#

set -e

# Variables (à récupérer depuis le script principal)
RESOURCE_GROUP="rg-sharepoint-test"
USER_IDENTITY_NAME="id-sharepoint-test"

echo "🔑 Configuration des permissions Microsoft Graph pour User Assigned Identity"
echo "==========================================================================="

# Récupération de l'identité
if ! az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" >/dev/null 2>&1; then
    echo "❌ User Assigned Identity '$USER_IDENTITY_NAME' non trouvée dans '$RESOURCE_GROUP'"
    echo "💡 Exécutez d'abord: bash setup_aci_with_identity.sh"
    exit 1
fi

IDENTITY_CLIENT_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query clientId -o tsv)
IDENTITY_PRINCIPAL_ID=$(az identity show --resource-group "$RESOURCE_GROUP" --name "$USER_IDENTITY_NAME" --query principalId -o tsv)

echo "🆔 Identity trouvée:"
echo "   Client ID: $IDENTITY_CLIENT_ID"
echo "   Principal ID: $IDENTITY_PRINCIPAL_ID"

# ID de l'application Microsoft Graph
GRAPH_APP_ID="00000003-0000-0000-c000-000000000000"

echo -e "\n🔧 Configuration des permissions Microsoft Graph..."

# 1. Créer le service principal Microsoft Graph s'il n'existe pas
echo "1. Création du service principal Microsoft Graph..."
if ! az ad sp show --id "$GRAPH_APP_ID" >/dev/null 2>&1; then
    az ad sp create --id "$GRAPH_APP_ID"
    echo "   ✅ Service principal Microsoft Graph créé"
else
    echo "   ✅ Service principal Microsoft Graph existe déjà"
fi

# 2. Obtenir les IDs des permissions nécessaires
echo -e "\n2. Récupération des IDs des permissions..."

# Sites.ReadWrite.All
SITES_PERMISSION_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query "appRoles[?value=='Sites.ReadWrite.All'].id" -o tsv)
echo "   Sites.ReadWrite.All: $SITES_PERMISSION_ID"

# Files.ReadWrite.All  
FILES_PERMISSION_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query "appRoles[?value=='Files.ReadWrite.All'].id" -o tsv)
echo "   Files.ReadWrite.All: $FILES_PERMISSION_ID"

# User.Read (Note: User.Read est souvent dans oauth2PermissionScopes, pas appRoles)
USER_PERMISSION_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query "oauth2PermissionScopes[?value=='User.Read'].id" -o tsv)
if [ -z "$USER_PERMISSION_ID" ]; then
    # Essayer dans appRoles
    USER_PERMISSION_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query "appRoles[?value=='User.Read'].id" -o tsv)
fi
echo "   User.Read: $USER_PERMISSION_ID"

# Obtenir l'ID de ressource Microsoft Graph
GRAPH_RESOURCE_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query id -o tsv)

# 3. Attribution des rôles à l'identité managée
echo -e "\n3. Attribution des permissions à l'identité managée..."

# Attribution Sites.ReadWrite.All
if [ -n "$SITES_PERMISSION_ID" ]; then
    echo "   Attribution Sites.ReadWrite.All..."
    az rest --method POST \
        --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$IDENTITY_PRINCIPAL_ID/appRoleAssignments" \
        --body "{'principalId':'$IDENTITY_PRINCIPAL_ID','resourceId':'$GRAPH_RESOURCE_ID','appRoleId':'$SITES_PERMISSION_ID'}" \
        --headers "Content-Type=application/json" || echo "   ⚠️  Permission peut-être déjà attribuée"
else
    echo "   ❌ ID de permission Sites.ReadWrite.All non trouvé"
fi

# Attribution Files.ReadWrite.All
if [ -n "$FILES_PERMISSION_ID" ]; then
    echo "   Attribution Files.ReadWrite.All..."
    az rest --method POST \
        --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$IDENTITY_PRINCIPAL_ID/appRoleAssignments" \
        --body "{'principalId':'$IDENTITY_PRINCIPAL_ID','resourceId':'$GRAPH_RESOURCE_ID','appRoleId':'$FILES_PERMISSION_ID'}" \
        --headers "Content-Type=application/json" || echo "   ⚠️  Permission peut-être déjà attribuée"
else
    echo "   ❌ ID de permission Files.ReadWrite.All non trouvé"
fi

# Attribution User.Read (optionnelle pour SharePoint)
if [ -n "$USER_PERMISSION_ID" ]; then
    echo "   Attribution User.Read..."
    az rest --method POST \
        --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$IDENTITY_PRINCIPAL_ID/appRoleAssignments" \
        --body "{'principalId':'$IDENTITY_PRINCIPAL_ID','resourceId':'$GRAPH_RESOURCE_ID','appRoleId':'$USER_PERMISSION_ID'}" \
        --headers "Content-Type=application/json" || echo "   ⚠️  Permission peut-être déjà attribuée"
else
    echo "   ⚠️  User.Read ignoré (non critique pour SharePoint)"
fi

# 4. Vérification des permissions attribuées
echo -e "\n4. Vérification des permissions attribuées..."
az rest --method GET \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$IDENTITY_PRINCIPAL_ID/appRoleAssignments" \
    --query "value[].{Permission:appRoleId,Resource:resourceDisplayName}" \
    --output table

echo -e "\n✅ Configuration des permissions terminée!"
echo -e "\n💡 Prochaines étapes:"
echo "1. Attendez 5-10 minutes pour la propagation des permissions"
echo "2. Connectez-vous à votre ACI et testez le script SharePoint"
echo "3. Si vous obtenez des erreurs 403, attendez un peu plus longtemps"

echo -e "\n🔗 Commandes pour tester dans l'ACI:"
echo "az container exec --resource-group $RESOURCE_GROUP --name aci-sharepoint-test --exec-command /bin/bash" 