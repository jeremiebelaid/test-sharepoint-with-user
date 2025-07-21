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
    gosu \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation de l'Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash && \
    az upgrade

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

# Passer à l'utilisateur developer pour les installations spécifiques
USER developer
WORKDIR /home/developer

ENV PATH="/home/developer/.asdf/bin:/home/developer/.asdf/shims:/home/linuxbrew/.linuxbrew/bin:/home/developer/.local/bin:${PATH}"

# Installation de Homebrew et des outils
RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && \
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
    brew install asdf uv && \
    asdf plugin add python && \
    asdf plugin add terraform && \
    asdf plugin add direnv && \
    asdf install python 3.13.5 && \
    asdf install terraform latest && \
    asdf install direnv latest && \
    asdf set global python 3.13.5 && \
    asdf set global terraform $(asdf latest terraform) && \
    asdf set global direnv $(asdf latest direnv)

# Configuration du shell
RUN echo '' >> ~/.bashrc && \
    echo '# Homebrew & asdf setup' >> ~/.bashrc && \
    echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc && \
    echo 'export ASDF_DIR="$(brew --prefix asdf)"' >> ~/.bashrc && \
    echo '. "$ASDF_DIR/libexec/asdf.sh"' >> ~/.bashrc && \
    echo 'eval "$(asdf exec direnv hook bash)"' >> ~/.bashrc && \
    echo '[[ -f ~/.bashrc ]] && . ~/.bashrc' > ~/.bash_profile

# Installation de uv et des dépendances du projet
COPY --chown=developer:developer pyproject.toml .
RUN eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && \
    export ASDF_DIR="$(brew --prefix asdf)" && \
    . "$ASDF_DIR/libexec/asdf.sh" && \
    uv venv && \
    uv pip install .

# Configuration globale du PATH
USER root
ENV PATH="/home/developer/.asdf/bin:/home/developer/.asdf/shims:/home/linuxbrew/.linuxbrew/bin:/home/developer/.local/bin:${PATH}"

# Création du répertoire de travail
RUN mkdir -p /workspace && chown developer:developer /workspace

# Exposition du port SSH
EXPOSE 22

# Script de démarrage
COPY --chown=developer:developer --chmod=755 docker/start.sh /start.sh

# Commande par défaut
ENTRYPOINT ["/start.sh"]
CMD ["/bin/bash", "-c", "while true; do sleep 30; done"]
