#!/bin/bash
set -e

# Set the default build type
BUILD_TYPE=Release

DEFAULT_IGNORE=(
  "pcb_simulation"
)

SIMULATION_PACKAGES=(
  "pcb_simulation"
  "ldlidar_stl_ros2"
)

colcon build \
  --merge-install \
  --symlink-install \
  --cmake-args "-DCMAKE_BUILD_TYPE=$BUILD_TYPE" "-DCMAKE_EXPORT_COMPILE_COMMANDS=On" \
  -Wall -Wextra -Wpedantic \
  --packages-ignore ${SIMULATION_PACKAGES[@]}
