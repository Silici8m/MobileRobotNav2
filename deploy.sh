#!/bin/bash
# scripts/deploy.sh


echo "Synchronisation du code vers le Pi ($ROBOT_IP)..."

rsync -avz --delete \
    --exclude='build/' \
    --exclude='install/' \
    --exclude='log/' \
    --exclude='.git/' \
    --exclude='.vscode/' \
    ./ ${ROBOT_USER}@${ROBOT_IP}:${TARGET_DIR}/

echo "✅ Code à jour sur le Pi."

#!/bin/bash
# Usage: ./deploy.sh [hostname_ou_ip]

TARGET=${1:-pcb-pi4}
TARGET_USER="pcb"
TARGET_DIR="~/MobileRobotNav2"

echo "📦 Déploiement vers ${TARGET_USER}@${TARGET}..."

# On utilise une liste d'exclusion pour ne pas envoyer les dossiers de build PC
rsync -avz --progress \
    --exclude='build/' \
    --exclude='install/' \
    --exclude='log/' \
    --exclude='.git/' \
    --exclude='.vscode/' \
    ./ ${TARGET_USER}@${TARGET}:${TARGET_DIR}/

echo "✅ Fichiers synchronisés."