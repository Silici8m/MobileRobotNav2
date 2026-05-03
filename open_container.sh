#!/bin/bash
# open_container.sh
CONTAINER=$(docker compose -f docker/docker-compose.yml ps -q robot)

if [ -n "$CONTAINER" ]; then
  docker exec -it $CONTAINER bash
else
  docker compose -f docker/docker-compose.yml run robot bash
fi