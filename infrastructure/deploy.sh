#!/bin/bash
#NB: need to run this in the infrastructure folder for right now, it's TODO to make that
#   a little easier
source ../.envrc
set -eux

# create top level directories
mkdir -p "${HOST_APPDATA}"
mkdir -p "${HOST_DATA}"

# httpd mountpoint
mkdir -p ${HOST_DATA}/web

#letsencrypt mountpoint
mkdir -p ${HOST_APPDATA}/letsencrypt

#nginx mountpoint
mkdir -p ${HOST_APPDATA}/nginx/data

#ddclient mountpoint
mkdir -p ${HOST_APPDATA}/ddclient/config

# I'd like to do this as a loop, but sadly files all need to go live in different places
# build the docker compose file from it's template, place it in the right spot
cat ./templates/docker-compose-template.yaml | envsubst > docker-compose.yaml
# expand the ddclient template to the config file to use, move it to the right spot
cat ./templates/ddclient-template.conf | envsubst > ${HOST_APPDATA}/ddclient/config/ddclient.conf

# do the thing
sudo docker compose up -d
set +eux