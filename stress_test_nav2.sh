#!/bin/bash

SERVICE_NAME="/global_costmap/virtual_layer/add_polygon"
SERVICE_TYPE="nav2_virtual_layer/srv/AddPolygon"

echo "Lancement de 20 appels simultanés au service AddPolygon..."

for i in {1..20}
do
  # Calcul sans 'bc' (on utilise des entiers pour simuler des flottants)
  # i=1 -> 1.10, i=2 -> 1.20, etc.
  X1="1.$((i))"
  X2="1.$((i))5"

  # Appel du service en arrière-plan
  ros2 service call $SERVICE_NAME $SERVICE_TYPE "{
    points: [
      {x: $X1, y: 1.0, z: 0.0},
      {x: $X2, y: 1.0, z: 0.0},
      {x: $X2, y: 1.1, z: 0.0},
      {x: $X1, y: 1.1, z: 0.0}
    ],
    frame_id: 'map',
    cost_level: 254
  }" > /dev/null &

  echo "Requête $i envoyée (x=$X1)..."
done

# Attendre que tous les appels soient terminés
wait
echo "Tous les appels ont été traités."