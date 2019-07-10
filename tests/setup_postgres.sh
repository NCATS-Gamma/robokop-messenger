#!/bin/bash
cd postgres
docker-compose up -d
echo "Waiting for Postgres to start..."
until echo $(docker logs messenger_postgres 2>&1) | grep -q "ready to accept connections"; do sleep 1; done
echo "Postgres started."
docker exec messenger_postgres mkdir -p /data
docker cp ../tests/data/omnicorp_mondo.csv messenger_postgres:/data/omnicorp_mondo.csv
docker cp ../tests/data/omnicorp_hgnc.csv messenger_postgres:/data/omnicorp_hgnc.csv
python ../tests/init_omnicorp.py
echo "Postgres initialized."