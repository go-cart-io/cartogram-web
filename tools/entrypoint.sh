#!/bin/sh

# Your "wait for DB" logic goes here
echo "Waiting for database..."
until python3 -c "
from web import create_app, db
app = create_app()
with app.app_context():
    print('Database connection check passed')
" 2>/dev/null; do
  sleep 1
done
echo "Database ready! Applying migrations..."
flask db upgrade
echo "Migrations completed!"

# Check the first argument passed to the entrypoint
if [ "$1" = "production" ]; then
  echo "Running in production mode: starting Gunicorn/Cron..."
  exec sh -c "cron & gunicorn --bind $CARTOGRAM_HOST:$CARTOGRAM_PORT -w $CARTOGRAM_GUNICORN_WORKERS $CARTOGRAM_GUNICORN_OPTIONS \"web:create_app()\""
elif [ "$1" = "development" ]; then
  echo "Running in development mode: sleeping indefinitely..."
  exec sleep infinity
else
  echo "No specific mode provided. Executing given command directly: $*"
  exec "$@"
fi