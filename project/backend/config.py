import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Domain Configuration
DOMAIN = os.getenv('DOMAIN', 'localhost')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8080')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000/api')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
ADMIN_CHAT_IDS = [int(x.strip()) for x in os.getenv('ADMIN_CHAT_IDS', '508246426').split(',')]
TELEGRAM_WEBAPP_SECRET = os.getenv('TELEGRAM_WEBAPP_SECRET', 'your_webapp_secret_here')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://auth_user:auth_password@postgres:5432/auth_db')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'auth_db')
POSTGRES_USER = os.getenv('POSTGRES_USER', 'auth_user')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'auth_password')

# Port Configuration
FRONTEND_PORT = int(os.getenv('FRONTEND_PORT', '8080'))
BACKEND_PORT = int(os.getenv('BACKEND_PORT', '5000'))
POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))

# Environment Configuration
NODE_ENV = os.getenv('NODE_ENV', 'production')
FLASK_ENV = os.getenv('FLASK_ENV', 'production') 