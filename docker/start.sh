#!/bin/bash


# Démarrage du service SSH
service ssh start

# Affichage des informations de connexion
echo "=========================================="
echo "🚀 Container Ubuntu avec SSH démarré"
echo "=========================================="
echo "Utilisateur: developer"
echo "Mot de passe: $(cat /run/secrets/dev_password)"
echo "Port SSH: 22"
echo "=========================================="

# Boucle infinie pour maintenir le container actif
# while true; do
#     sleep 30
# done
exec "$@"
