#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
$DIR/setup_redis.sh
$DIR/setup_postgres.sh
$DIR/setup_neo4j.sh