#!/bin/bash
cd neo4j
mkdir -p logs
echo "" > logs/debug.log
docker-compose up -d
echo "Waiting for Neo4j to start..."
until echo $(docker logs messenger_neo4j 2>&1) | grep -q "Bolt enabled"; do sleep 1; done
echo "Neo4j started."
export PYTHONPATH=$(pwd)/..
python ../tests/setup_neo4j.py
echo "Neo4j initialized."