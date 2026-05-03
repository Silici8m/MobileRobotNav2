#!/bin/bash
# deploy.sh


PI_USER="pcb"
PI_IP="192.168.1.130" 
WORKSPACE_NAME="MobileRobotNav2"
DOCKER_IMAGE_NAME="mobilerobot_image"
DOCKER_CONTAINER_NAME="mobilerobot_container"

echo "Déploiement vers ${PI_USER}@${PI_IP}..."

ssh $PI_USER@$PI_IP "mkdir -p ~/$WORKSPACE_NAME"

rsync -avz --progress --delete \
    --exclude='build/' \
    --exclude='install/' \
    --exclude='log/' \
    --exclude='.git/' \
    --exclude='.vscode/' \
    --exclude='pcb_simulation' \
    ./ ${PI_USER}@${PI_IP}:~/${WORKSPACE_NAME}/

echo "Fichiers synchronisés."

echo "Construction de l'image Docker sur le Pi (Cela peut prendre du temps la 1ère fois)..."
ssh $PI_USER@$PI_IP "cd ~/$WORKSPACE_NAME && docker build -t $DOCKER_IMAGE_NAME -f .devcontainer/Dockerfile ."

ssh $PI_USER@$PI_IP "docker rm -f $DOCKER_CONTAINER_NAME 2>/dev/null || true"


ssh -t $PI_USER@$PI_IP "docker run --name $DOCKER_CONTAINER_NAME \
    --network host \
    --ipc host \
    --privileged \
    -v /home/$PI_USER/$WORKSPACE_NAME:/workspaces/$WORKSPACE_NAME \
    -w /workspaces/$WORKSPACE_NAME \
    $DOCKER_IMAGE_NAME \
    bash -c 'rosdep update && rosdep install --from-paths src --ignore-src -y && colcon build --symlink-install --executor sequential -DCMAKE_BUILD_TYPE=Release'"