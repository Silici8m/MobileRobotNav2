#!/bin/bash
set -e

# Sur un Pi, on préfère souvent "Release" à "RelWithDebInfo" pour gagner en performance d'exécution
BUILD_TYPE=Release


# Limite la compilation à 2 cœurs en simultané pour éviter le freeze du Pi
export MAKEFLAGS="-j2"

colcon build \
        --merge-install \
        --symlink-install \
        --executor sequential \
        --cmake-args "-DCMAKE_BUILD_TYPE=$BUILD_TYPE" \
        -Wall -Wextra -Wpedantic

echo "Compilation terminée !"