#!/bin/bash

# Fix permissions for mounted volumes
chown -R app:app /config /music 2>/dev/null || true
chmod -R 777 /config /music 2>/dev/null || true

# Switch to app user and start the application
exec gosu app "$@"
