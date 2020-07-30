#!/usr/bin/env bash

export $(egrep -v '^#' .env | xargs)
export ROBOKOP_HOME=/Users/patrick/Documents/CoVar/projects/ncats/robokop-messenger
# export PYTHONPATH=/home/murphy/robokop-messenger

gunicorn messenger.server:APP --bind 0.0.0.0:4868 -w 4 -k uvicorn.workers.UvicornWorker -t 600 
