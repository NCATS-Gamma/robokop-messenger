#!/bin/bash
cd $ROBOKOP_HOME/robokop-messenger/tests/helpers/redis
docker-compose up -d
echo "Redis started."