# Запуск
## Docker-compose
docker compose --file compose-dev.yml up --watch
## Docker
WIP
## Вручную
_предполагая наличие окружения с установленными зависимостями_

1. cd polls_library
2. python polls_library/backend/main.py

**ИЛИ**

2. uvicorn polls_library.backend.main:app --reload