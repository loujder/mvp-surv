# Project Name

## Описание

Это веб-приложение с фронтендом на Vue.js и бэкендом на Flask.

## Установка и запуск

### Предварительные требования

- Docker и Docker Compose
- Node.js (для разработки)
- Python 3.11+ (для разработки)

### Настройка переменных окружения

1. Скопируйте файл `env.example` в `.env`:
```bash
cp env.example .env
```

2. Отредактируйте `.env` файл, указав ваши настройки:
```env
# Domain Configuration
DOMAIN=your-domain.com
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://your-domain.com/api

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_IDS=508246426
TELEGRAM_WEBAPP_SECRET=your_webapp_secret_here

# Database Configuration
DATABASE_URL=postgresql://auth_user:auth_password@postgres:5432/auth_db
POSTGRES_DB=auth_db
POSTGRES_USER=auth_user
POSTGRES_PASSWORD=auth_password
```

### Запуск с Docker

```bash
docker compose up --build
```

После запуска приложение будет доступно по адресам:
- Фронтенд: `${FRONTEND_URL}` (по умолчанию http://localhost:8080)
- Бэкенд (API): `${BACKEND_URL}` (по умолчанию http://localhost:5000/api)

### Разработка

Для разработки без Docker:

1. Backend:
```bash
cd backend
pip install -r requirements.txt
python app.py
```

2. Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Структура проекта

```
├── backend/          # Flask backend
├── frontend/         # Vue.js frontend
├── docker-compose.yml
├── .env              # Переменные окружения
└── README.md
```

## Переменные окружения

Основные переменные окружения:

- `DOMAIN` - основной домен приложения
- `FRONTEND_URL` - URL фронтенда
- `BACKEND_URL` - URL бэкенда
- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `ADMIN_CHAT_IDS` - ID администраторов (через запятую)
- `TELEGRAM_WEBAPP_SECRET` - секрет для Telegram Web App
- `DATABASE_URL` - URL базы данных PostgreSQL
