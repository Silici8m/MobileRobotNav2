#!/bin/bash
set -e

echo "Installation des utilitaires de base"
sudo apt-get update
sudo apt-get install -y rsync python3-vcstool

echo "Mise à jour et installation des dépendances ROS 2..."
rosdep update --rosdistro=$ROS_DISTRO
rosdep install --from-paths src --ignore-src -y --rosdistro=$ROS_DISTRO

echo "Setup terminé"