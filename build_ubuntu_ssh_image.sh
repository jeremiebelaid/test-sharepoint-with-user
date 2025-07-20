#!/bin/bash
#
# Script pour construire une image Ubuntu personnalisée avec SSH
# et la pousser vers Azure Container Registry
#

set -e  # Arrêter en cas d'erreur

# Variables de configuration
RESOURCE_GROUP="rg-sharepoint-test"
ACR_NAME="acrsharepointtest$(date +%s)"  # Doit correspondre à celui créé par setup_acr_with_permissions.sh
IMAGE_NAME="ubuntu-ssh"
IMAGE_TAG="latest"

# Configuration SSH
SSH_USER="developer"
SSH_PASSWORD="AzureDev2024!"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Construction d'une image Ubuntu avec SSH pour ACR${NC}"
echo -e "${BLUE}=================================================${NC}"

# 1. Vérification de Docker
echo -e "\n${YELLOW}1. Vérification de Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas installé${NC}"
    echo -e "${BLUE}💡 Installez Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas démarré${NC}"
    echo -e "${BLUE}💡 Démarrez Docker et relancez ce script${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker est disponible${NC}"

# 2. Récupération des informations ACR
echo -e "\n${YELLOW}2. Récupération des informations ACR...${NC}"

# Essayer de récupérer l'ACR existant
ACR_LIST=$(az acr list --resource-group "$RESOURCE_GROUP" --query "[].name" -o tsv)
if [ -z "$ACR_LIST" ]; then
    echo -e "${RED}❌ Aucun ACR trouvé dans le Resource Group '$RESOURCE_GROUP'${NC}"
    echo -e "${BLUE}💡 Créez d'abord l'ACR avec: ./setup_acr_with_permissions.sh${NC}"
    exit 1
fi

# Prendre le premier ACR trouvé
ACR_NAME=$(echo "$ACR_LIST" | head -n 1)
ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)

echo -e "${GREEN}✅ ACR trouvé${NC}"
echo -e "   ACR Name: ${ACR_NAME}"
echo -e "   Login Server: ${ACR_LOGIN_SERVER}"

# 3. Connexion à l'ACR
echo -e "\n${YELLOW}3. Connexion à l'ACR...${NC}"
echo -e "${BLUE}🔐 Connexion à l'ACR...${NC}"
az acr login --name "$ACR_NAME"
echo -e "${GREEN}✅ Connecté à l'ACR${NC}"

# 4. Création du Dockerfile
echo -e "\n${YELLOW}4. Création du Dockerfile...${NC}"

cat > Dockerfile << EOF
# Image de base Ubuntu 22.04
FROM ubuntu:22.04

# Variables d'environnement
ENV DEBIAN_FRONTEND=noninteractive
ENV SSH_USER=${SSH_USER}
ENV SSH_PASSWORD=${SSH_PASSWORD}

# Mise à jour du système et installation des packages
RUN apt-get update && apt-get install -y \\
    openssh-server \\
    sudo \\
    curl \\
    wget \\
    git \\
    vim \\
    nano \\
    python3 \\
    python3-pip \\
    python3-venv \\
    && rm -rf /var/lib/apt/lists/*

# Configuration SSH
RUN mkdir -p /var/run/sshd \\
    && echo 'root:${SSH_PASSWORD}' | chpasswd \\
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \\
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Création de l'utilisateur developer
RUN useradd -m -s /bin/bash ${SSH_USER} \\
    && echo "${SSH_USER}:${SSH_PASSWORD}" | chpasswd \\
    && echo "${SSH_USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Création du répertoire de travail
RUN mkdir -p /workspace && chown ${SSH_USER}:${SSH_USER} /workspace

# Exposition du port SSH
EXPOSE 22

# Script de démarrage
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Commande par défaut
CMD ["/start.sh"]
EOF

echo -e "${GREEN}✅ Dockerfile créé${NC}"

# 5. Création du script de démarrage
echo -e "\n${YELLOW}5. Création du script de démarrage...${NC}"

cat > start.sh << 'EOF'
#!/bin/bash

# Démarrage du service SSH
service ssh start

# Affichage des informations de connexion
echo "=========================================="
echo "🚀 Container Ubuntu avec SSH démarré"
echo "=========================================="
echo "Utilisateur: developer"
echo "Mot de passe: AzureDev2024!"
echo "Port SSH: 22"
echo "=========================================="

# Boucle infinie pour maintenir le container actif
while true; do
    sleep 30
done
EOF

chmod +x start.sh
echo -e "${GREEN}✅ Script de démarrage créé${NC}"

# 6. Construction de l'image
echo -e "\n${YELLOW}6. Construction de l'image Docker...${NC}"
echo -e "${BLUE}🔨 Construction de l'image...${NC}"

# Tagger l'image pour l'ACR
FULL_IMAGE_NAME="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${IMAGE_TAG}"

# Construire l'image
docker build -t "$FULL_IMAGE_NAME" .

echo -e "${GREEN}✅ Image construite${NC}"
echo -e "   Image: ${FULL_IMAGE_NAME}"

# 7. Test local de l'image
echo -e "\n${YELLOW}7. Test local de l'image...${NC}"
echo -e "${BLUE}🧪 Test de l'image en local...${NC}"

# Démarrer un container de test
TEST_CONTAINER_NAME="test-ubuntu-ssh"
docker run -d --name "$TEST_CONTAINER_NAME" -p 2222:22 "$FULL_IMAGE_NAME"

# Attendre que le container démarre
sleep 10

# Vérifier que le container fonctionne
if docker ps | grep -q "$TEST_CONTAINER_NAME"; then
    echo -e "${GREEN}✅ Container de test démarré avec succès${NC}"
    echo -e "   Test SSH: ssh developer@localhost -p 2222"
    echo -e "   Mot de passe: ${SSH_PASSWORD}"
else
    echo -e "${RED}❌ Échec du démarrage du container de test${NC}"
    docker logs "$TEST_CONTAINER_NAME"
    exit 1
fi

# Arrêter et supprimer le container de test
echo -e "${BLUE}🧹 Nettoyage du container de test...${NC}"
docker stop "$TEST_CONTAINER_NAME" 2>/dev/null || true
docker rm "$TEST_CONTAINER_NAME" 2>/dev/null || true

# 8. Push de l'image vers l'ACR
echo -e "\n${YELLOW}8. Push de l'image vers l'ACR...${NC}"
echo -e "${BLUE}📤 Push de l'image vers ${ACR_LOGIN_SERVER}...${NC}"

docker push "$FULL_IMAGE_NAME"

echo -e "${GREEN}✅ Image poussée vers l'ACR${NC}"

# 9. Vérification dans l'ACR
echo -e "\n${YELLOW}9. Vérification dans l'ACR...${NC}"
echo -e "${BLUE}🔍 Vérification des images dans l'ACR...${NC}"

az acr repository list --name "$ACR_NAME" --output table

echo -e "\n${BLUE}📋 Détails de l'image:${NC}"
az acr repository show-tags --name "$ACR_NAME" --repository "$IMAGE_NAME" --output table

# 10. Instructions finales
echo -e "\n${BLUE}=================================================================${NC}"
echo -e "${GREEN}🎉 Image Ubuntu avec SSH créée et poussée avec succès!${NC}"
echo -e "${BLUE}=================================================================${NC}"

echo -e "\n${YELLOW}📋 Informations de l'image:${NC}"
echo -e "   ACR: ${ACR_NAME}"
echo -e "   Image: ${FULL_IMAGE_NAME}"
echo -e "   Tag: ${IMAGE_TAG}"

echo -e "\n${YELLOW}🔑 Identifiants SSH:${NC}"
echo -e "   Utilisateur: ${SSH_USER}"
echo -e "   Mot de passe: ${SSH_PASSWORD}"
echo -e "   Port: 22"

echo -e "\n${YELLOW}🔗 Utilisation dans ACI:${NC}"
echo -e "${BLUE}# Image à utiliser dans votre script ACI:${NC}"
echo -e "${FULL_IMAGE_NAME}"

echo -e "\n${YELLOW}🚀 Prochaines étapes:${NC}"
echo -e "1. ${BLUE}Modifiez votre script ACI pour utiliser cette image${NC}"
echo -e "2. ${BLUE}Testez le déploiement avec l'image personnalisée${NC}"
echo -e "3. ${BLUE}Connectez-vous en SSH depuis Cursor${NC}"

echo -e "\n${YELLOW}📝 Variables pour vos scripts:${NC}"
echo -e "export ACR_NAME=\"${ACR_NAME}\""
echo -e "export ACR_LOGIN_SERVER=\"${ACR_LOGIN_SERVER}\""
echo -e "export IMAGE_NAME=\"${IMAGE_NAME}\""
echo -e "export IMAGE_TAG=\"${IMAGE_TAG}\""
echo -e "export FULL_IMAGE_NAME=\"${FULL_IMAGE_NAME}\""

echo -e "\n${GREEN}✅ Construction terminée!${NC}" 