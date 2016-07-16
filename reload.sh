#!/bin/bash

cd "$(dirname "$0")"

pip3 install -r requirements.txt

python3 updater.py

cp proxy_server_list.conf /etc/squid3/

service squid3 reload
