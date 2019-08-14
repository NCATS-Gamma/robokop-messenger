#!/bin/bash
cd $ROBOKOP_HOME/robokop-messenger/tests/helpers/redis
docker-compose down
echo "Redis stopped."
cd $ROBOKOP_HOME/robokop-messenger/tests/helpers/postgres
docker-compose down
echo "Postgres stopped."
cd $ROBOKOP_HOME/robokop-messenger/helpers/neo4j
docker-compose down
echo "Neo4j stopped."