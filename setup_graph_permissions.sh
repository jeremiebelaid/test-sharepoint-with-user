#!/bin/bash
#
# Script d'aide pour configurer les permissions Microsoft Graph
# ⚠️  À EXÉCUTER AVEC DES DROITS D'ADMINISTRATEUR AZURE AD
#

set -e

# Variables (à récupérer depuis le script principal ou à adapter)
RESOURCE_GROUP="rg-sharepoint-test"
USER_IDENTITY_NAME="id-sharepoint-test"
# ⬇️ MODIFIÉ: URL du site SharePoint spécifique à autoriser
SHAREPOINT_SITE_URL="https://ddasys.sharepoint.com/sites/DDASYS"


echo "🔑 Configuration des permissions Microsoft Graph RESTREINTES pour User Assigned Identity"
echo "========================================================================================"

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
GRAPH_RESOURCE_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query id -o tsv)

echo -e "\n🔧 Configuration des permissions Microsoft Graph (restreintes)..."

# 1. Obtenir l'ID de la permission Sites.Selected
echo "1. Récupération de l'ID de la permission 'Sites.Selected'..."
SITES_SELECTED_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query "appRoles[?value=='Sites.Selected'].id" -o tsv)
if [ -z "$SITES_SELECTED_ID" ]; then
    echo "❌ Permission 'Sites.Selected' non trouvée pour Microsoft Graph."
    exit 1
fi
echo "   ✅ Sites.Selected: $SITES_SELECTED_ID"

# 2. Attribution de Sites.Selected à l'identité managée
echo -e "\n2. Attribution de la permission 'Sites.Selected' à l'identité..."
az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$IDENTITY_PRINCIPAL_ID/appRoleAssignments" \
    --body "{'principalId':'$IDENTITY_PRINCIPAL_ID','resourceId':'$GRAPH_RESOURCE_ID','appRoleId':'$SITES_SELECTED_ID'}" \
    --headers "Content-Type=application/json" || echo "   ⚠️  Permission API 'Sites.Selected' peut-être déjà attribuée."

# 3. Récupérer l'ID du site SharePoint à partir de l'URL
echo -e "\n3. Récupération de l'ID du site SharePoint..."
SHAREPOINT_HOSTNAME=$(echo "$SHAREPOINT_SITE_URL" | awk -F/ '{print $3}')
SHAREPOINT_SITE_PATH=$(echo "$SHAREPOINT_SITE_URL" | awk -F/ '{s=""; for (i=4; i<=NF; i++) s=s"/"$i; print s}')
SITE_ID=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/sites/$SHAREPOINT_HOSTNAME:$SHAREPOINT_SITE_PATH" --query id -o tsv)
if [ -z "$SITE_ID" ]; then
    echo "❌ Impossible de trouver l'ID du site pour l'URL: $SHAREPOINT_SITE_URL"
    exit 1
fi
echo "   ✅ Site ID trouvé: $SITE_ID"

# 4. Donner la permission 'write' sur le site spécifique
echo -e "\n4. Attribution de la permission 'write' sur le site spécifique..."
PERMISSION_BODY="{'roles': ['write'], 'grantedToIdentities': [{'application': {'id': '$IDENTITY_CLIENT_ID', 'displayName': '$USER_IDENTITY_NAME'}}]}"
az rest --method POST \
    --uri "https://graph.microsoft.com/v1.0/sites/$SITE_ID/permissions" \
    --body "$PERMISSION_BODY" \
    --headers "Content-Type=application/json" || echo "   ⚠️  Permission de site peut-être déjà attribuée."


# 5. Vérification des permissions API attribuées
echo -e "\n5. Vérification des permissions API attribuées à l'identité..."
az rest --method GET \
    --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$IDENTITY_PRINCIPAL_ID/appRoleAssignments" \
    --query "value[].{Permission:appRoleId,Resource:resourceDisplayName}" \
    --output table

echo -e "\n✅ Configuration des permissions restreintes terminée!"
echo -e "\n‼️  ACTION MANUELLE REQUISE ‼️"
echo "Pour finaliser le verrouillage, vous devez MANUELLEMENT révoquer les permissions larges."
echo "1. Allez sur le Portail Azure -> Azure Active Directory -> Applications d'entreprise."
echo "2. Cherchez '$USER_IDENTITY_NAME' (ou par Client ID: $IDENTITY_CLIENT_ID)."
echo "3. Allez dans la section 'Permissions'."
echo "4. Révoquez 'Sites.ReadWrite.All' et 'Files.ReadWrite.All'."
echo -e "\n💡 Attendez 5-10 minutes pour la propagation des nouvelles permissions avant de tester."

echo -e "\n🔗 Commandes pour tester dans l'ACI:"
echo "az container exec --resource-group $RESOURCE_GROUP --name aci-sharepoint-test --exec-command /bin/bash" 