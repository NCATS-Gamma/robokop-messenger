#!/bin/bash
cd $ROBOKOP_HOME/robokop-messenger/tests/helpers/postgres
docker-compose up -d
echo "Waiting for Postgres to start..."
until echo $(docker logs messenger_postgres 2>&1) | grep -q "ready to accept connections"; do sleep 1; done
echo "Postgres started."
docker exec messenger_postgres mkdir -p /data
docker cp ../../data/omnicorp_mondo.csv messenger_postgres:/data/omnicorp_mondo.csv
docker cp ../../data/omnicorp_hgnc.csv messenger_postgres:/data/omnicorp_hgnc.csv
python ../../setup/init_omnicorp.py
echo "Postgres initialized."