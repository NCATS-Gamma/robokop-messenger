#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
$DIR/startup_redis.sh
$DIR/startup_postgres.sh
$DIR/startup_neo4j.sh