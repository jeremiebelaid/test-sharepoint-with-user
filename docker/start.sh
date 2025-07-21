#!/bin/bash

# Démarrage du service SSH (exécuté en tant que root)
service ssh start

# Affichage des informations de connexion
echo "=========================================="
echo "🚀 Container Ubuntu avec SSH démarré"
echo "=========================================="
echo "Utilisateur: developer"
echo "Port SSH: 22"
echo "=========================================="

# Afficher le PATH actuel pour le débogage
echo "Current PATH: $PATH"

# Passer à l'utilisateur 'developer' pour le reste de l'exécution
exec gosu developer "$@"
