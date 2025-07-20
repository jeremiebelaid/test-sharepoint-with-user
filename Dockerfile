# Image de base Ubuntu 24.04 (dernière version)
FROM ubuntu:24.04

# Variables d'environnement
ENV DEBIAN_FRONTEND=noninteractive
ENV SSH_USER=developer
ENV SSH_PASSWORD=AzureDev2024!

# Mise à jour du système et installation des packages
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    curl \
    wget \
    git \
    vim \
    nano \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Configuration SSH
RUN mkdir -p /var/run/sshd \
    && echo 'root:AzureDev2024!' | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Création de l'utilisateur developer
RUN useradd -m -s /bin/bash developer \
    && echo "developer:AzureDev2024!" | chpasswd \
    && echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && mkdir -p /home/developer/.ssh \
    && echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCtD9sWm6GyKqugtEWd88tv9fPdncPI4d1iY6Xfz2J+N+ixieOzIbUJYAWzpsMSgNeD7k1wp5blPsxTtirtiDtlangs4BjnWzw6ZwtTTZQmQ/tw+jk0uDYW0fUD6PWmhYBQyQzY0T8AT8U2Z/MPk46KCUzrEe3sqGh5K2coYVFULRplpk1Mvc+uoLSaZC+UNeQ9QFFRe6IxlYIj/kvPmxJN/cbGgYOUot1fOdoa/kjWcu4s3gN+2+5MFIZSESXbD8IL9EaWCtFO+zx/eX6xVg324RDCmsmClA/CB32P/IzOBPJawaEt04+jNrDl5biH23l84JBkbh5MqUSsfzm6EqGzF8UGYX3Otrisqhw3BfxwxFD1Z208QQHdzKWXEhAb5aOwL7ldC+nY4xGjUUyUcJj2lpe6yP9WmgC81czclWPqa4i1R14lsJsngSSDHmP8JZAjsHr0Uh/oCwBYWmXjEjERKxQ4h8q+DimdyZOv6hNGkynTMlQCpoPFtL7OhrD3AhJiH1vmmhbykjnwe2vgXOj2HrtSKiw431+LIYkmGjnCb9pPelCuWHkAxRrtBQgfy5dmrJKTLLqL8j09f+FTXjN7QMS/Tmc0fb5F0MHiVssulIHjyYIP4ATD2Rsmdakc+59xvmBozuit+Jwxjme1SxvFj3HbgQxRnEx2/T6dXt+LuQ== developer_aci_key" >> /home/developer/.ssh/authorized_keys \
    && chmod 700 /home/developer/.ssh \
    && chmod 600 /home/developer/.ssh/authorized_keys \
    && chown -R developer:developer /home/developer/.ssh

# Création du répertoire de travail
RUN mkdir -p /workspace && chown developer:developer /workspace

# Exposition du port SSH
EXPOSE 22

# Script de démarrage
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Commande par défaut
ENTRYPOINT ["/start.sh"]
CMD ["/bin/bash", "-c", "while true; do sleep 30; done"]
