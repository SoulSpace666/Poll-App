LIGHT_GREEN='\033[1;32m'
NC='\033[0m' # No Color

color_print () {
  echo -e "${LIGHT_GREEN}===========================================${NC}"
  echo -e "${LIGHT_GREEN}$1${NC}"
  echo -e "${LIGHT_GREEN}===========================================${NC}"
}

if [ "$ENVIRONMENT" = "DEV" ]; then

color_print "Starting development server"
exec uvicorn backend.main:app --host $BACKEND_HOST --reload --port $BACKEND_PORT --log-config=log_conf.yaml

elif [ "$ENVIRONMENT" = "PROD" ]; then

color_print "Starting production server"
exec gunicorn --bind 0.0.0.0:8000 settings.wsgi:application --workers $(($(nproc) * 2 + 1)) --timeout 1600 -k uvicorn.workers.UvicornWorker

fi

