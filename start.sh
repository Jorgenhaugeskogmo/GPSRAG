#!/bin/bash

# Replace PORT in nginx config
envsubst '$PORT' < /etc/nginx/sites-available/gpsrag > /tmp/gpsrag.conf
mv /tmp/gpsrag.conf /etc/nginx/sites-available/gpsrag

# Remove default nginx config
rm -f /etc/nginx/sites-enabled/default

# Enable our config
ln -sf /etc/nginx/sites-available/gpsrag /etc/nginx/sites-enabled/

# Create log directories
mkdir -p /var/log/supervisor

# Start supervisord
exec supervisord -c /etc/supervisor/conf.d/gpsrag.conf 