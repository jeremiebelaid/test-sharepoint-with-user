 # Image de base Ubuntu 24.04 (dernière version)
FROM ubuntu:24.04

# Variables d'environnement
ENV DEBIAN_FRONTEND=noninteractive
ENV SSH_USER=developer

# Mise à jour du système et installation des packages avec Nala
RUN apt-get update && apt-get install -y nala && nala install -y \
    openssh-server \
    sudo \
    curl \
    wget \
    git \
    vim \
    nano \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Configuration SSH
RUN --mount=type=secret,id=dev_password \
    mkdir -p /var/run/sshd \
    && echo "root:$(cat /run/secrets/dev_password)" | chpasswd \
    && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config \
    && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Création de l'utilisateur developer
RUN --mount=type=secret,id=dev_password \
    --mount=type=secret,id=dev_ssh_public_key \
    useradd -m -s /bin/bash developer \
    && echo "developer:$(cat /run/secrets/dev_password)" | chpasswd \
    && echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && mkdir -p /home/developer/.ssh \
    && cat /run/secrets/dev_ssh_public_key >> /home/developer/.ssh/authorized_keys \
    && chmod 700 /home/developer/.ssh \
    && chmod 600 /home/developer/.ssh/authorized_keys \
    && chown -R developer:developer /home/developer/.ssh

# Installation de Homebrew et asdf
USER developer
WORKDIR /home/developer

# Installer Homebrew. Le script ajoute la configuration au fichier .profile de l'utilisateur.
RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Configurer l'environnement, installer asdf, Python, et Terraform
RUN export PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH" && \
    brew install asdf && \
    export ASDF_DIR="$(brew --prefix asdf)" && \
    echo -e "\n. ${ASDF_DIR}/libexec/asdf.sh" >> /home/developer/.bashrc && \
    . "${ASDF_DIR}/libexec/asdf.sh" && \
    asdf plugin add python && \
    asdf install python 3.13.5 && \
    asdf set global python 3.13.5 && \
    asdf plugin add terraform && \
    asdf install terraform latest && \
    asdf set global terraform $(asdf latest terraform) && \
    asdf plugin add direnv && \
    asdf install direnv latest && \
    asdf set global direnv $(asdf latest direnv) && \
    echo 'eval "$(asdf exec direnv hook bash)"' >> /home/developer/.bashrc

# Copier le fichier de projet avant d'installer les dépendances
COPY --chown=developer:developer pyproject.toml /home/developer/pyproject.toml

# Installer uv, créer un venv et installer les dépendances du projet
RUN eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
    export PATH="/home/developer/.local/bin:$PATH" && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    uv venv /home/developer/venv && \
    . /home/developer/venv/bin/activate && \
    uv pip install .

# Revenir à l'utilisateur root pour les commandes suivantes
USER root

# Création du répertoire de travail
RUN mkdir -p /workspace && chown developer:developer /workspace

# Exposition du port SSH
EXPOSE 22

# Script de démarrage
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# Commande par défaut
ENTRYPOINT ["/start.sh"]
CMD ["/bin/bash", "-c", "while true; do sleep 30; done"]
