#!/bin/sh

set -e

echo "Waiting for DB to be ready..."
# Add a delay to ensure the database container is fully up and running
sleep 5

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting Static files..."
python manage.py collectstatic --noinput

echo "Seeding database ..."
python manage.py seed_database

# Check if transactions were successful
if [ $? -ne 0 ]; then
  echo "Setup failed. Exiting..."
  exit 1
fi

# Start the server
echo "Starting server..."
exec "$@"
