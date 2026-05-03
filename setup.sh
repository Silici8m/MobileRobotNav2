#!/bin/bash
set -e

# Sur le Pi utiliser 
# ./setup.sh IGNORE_SIM=true


SIMULATION_PACKAGES=(
  "pcb_simulation"
)

IGNORE_SIM=false
for arg in "$@"; do
  if [ "$arg" == "IGNORE_SIM=true" ]; then
    IGNORE_SIM=true
  fi
done

envsubst < src/ros2.repos | vcs import src
sudo apt-get update
rosdep update --rosdistro=$ROS_DISTRO

SKIP_KEYS=""
if [ "$IGNORE_SIM" = true ]; then
  for pkg in "${SIMULATION_PACKAGES[@]}"; do
    KEYS=$(rosdep keys --from-paths src/$pkg 2>/dev/null | tr '\n' ' ')
    SKIP_KEYS="$SKIP_KEYS $KEYS"
  done
fi

rosdep install --from-paths src --ignore-src -y --rosdistro=$ROS_DISTRO --skip-keys="$(echo $SKIP_KEYS | xargs)"