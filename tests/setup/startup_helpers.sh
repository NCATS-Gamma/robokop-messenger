#!/bin/bash

cd $ROBOKOP_HOME/robokop-messenger/tests/helpers
docker-compose up -d

echo "Waiting for Postgres to start..."
until echo $(docker logs omnicorp_postgres 2>&1) | grep -q "ready to accept connections"; do sleep 1; done
echo "Postgres started."
docker exec omnicorp_postgres mkdir -p /data
docker cp ../data/omnicorp_mondo.csv omnicorp_postgres:/data/omnicorp_mondo.csv
docker cp ../data/omnicorp_hgnc.csv omnicorp_postgres:/data/omnicorp_hgnc.csv
python ../setup/init_omnicorp.py
echo "Postgres initialized."

echo "Waiting for Neo4j to start..."
until echo $(docker logs remote_neo4j 2>&1) | grep -q "Bolt enabled"; do sleep 1; done
echo "Neo4j started."
export PYTHONPATH=$ROBOKOP_HOME/robokop-messenger
python ../setup/init_neo4j.py
echo "Neo4j initialized."