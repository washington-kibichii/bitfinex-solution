#!/bin/bash

#Initialize the project
gcloud init

#Deploy Cloud scheduler
gcloud app deploy cron.yaml

#Deploy Datastore configs
gcloud app deploy index.yaml

#Push to server
gcloud app deploy

#Tail Logs
gcloud app logs tail -s default