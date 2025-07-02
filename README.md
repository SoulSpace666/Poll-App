# Запуск
## Docker-compose
### В DEV
docker compose --file compose-dev.yml up --watch
### В PROD 
docker compose -f compose-prod.yml up --build 

## Docker
WIP
## Вручную
_предполагая наличие окружения с установленными зависимостями_

1. cd polls_library
2. python polls_library/backend/main.py

# Настройка окружения
## Скопируйте шаблон окружения:
cp env.example .env

## Генерация SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

## Настройка Google OAuth
1. Создайте OAuth 2.0 Client ID в Google Cloud Console
2. В "Authorized redirect URIs" укажите: https://ваш-домен/auth/google/callback
3. Скопируйте значения в .env