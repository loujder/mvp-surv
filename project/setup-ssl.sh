#!/bin/bash

# Скрипт для настройки SSL сертификатов с Let's Encrypt

echo "Настройка SSL сертификатов для домена..."

# Проверяем, существует ли .env файл
if [ ! -f ".env" ]; then
    echo "Ошибка: Файл .env не найден. Сначала запустите setup-env.sh"
    exit 1
fi

# Загружаем переменные из .env
source .env

# Проверяем, что DOMAIN установлен
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "your-domain.com" ]; then
    echo "Ошибка: DOMAIN не настроен в .env файле"
    echo "Укажите ваш реальный домен в переменной DOMAIN"
    exit 1
fi

echo "Настройка SSL для домена: $DOMAIN"

# Проверяем, установлен ли certbot
if ! command -v certbot &> /dev/null; then
    echo "Установка certbot..."
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        sudo apt-get update
        sudo apt-get install -y certbot
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y certbot
    else
        echo "Ошибка: Не удалось установить certbot. Установите его вручную."
        exit 1
    fi
fi

# Создаем временную nginx конфигурацию для получения сертификата
echo "Создание временной nginx конфигурации..."
cat > /tmp/nginx-temp.conf << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}
EOF

# Останавливаем текущие контейнеры
echo "Остановка текущих контейнеров..."
docker compose down

# Запускаем только nginx для получения сертификата
echo "Запуск nginx для получения сертификата..."
docker run -d --name nginx-temp \
    -p 80:80 \
    -v /tmp/nginx-temp.conf:/etc/nginx/conf.d/default.conf \
    -v /var/www/html:/var/www/html \
    nginx:alpine

# Получаем SSL сертификат
echo "Получение SSL сертификата от Let's Encrypt..."
sudo certbot certonly --webroot \
    --webroot-path=/var/www/html \
    --email admin@$DOMAIN \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Останавливаем временный nginx
echo "Остановка временного nginx..."
docker stop nginx-temp
docker rm nginx-temp

# Проверяем, что сертификаты получены
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "SSL сертификаты успешно получены!"
    echo "Сертификаты находятся в: /etc/letsencrypt/live/$DOMAIN/"
    
    # Создаем скрипт для обновления сертификатов
    cat > renew-ssl.sh << EOF
#!/bin/bash
# Скрипт для обновления SSL сертификатов
sudo certbot renew --quiet
docker compose restart frontend
EOF
    
    chmod +x renew-ssl.sh
    
    # Добавляем в crontab для автоматического обновления
    (crontab -l 2>/dev/null; echo "0 12 * * * $(pwd)/renew-ssl.sh") | crontab -
    
    echo "Сертификаты будут автоматически обновляться каждый день в 12:00"
    
else
    echo "Ошибка: Не удалось получить SSL сертификаты"
    echo "Проверьте:"
    echo "1. Домен $DOMAIN указывает на этот сервер"
    echo "2. Порт 80 открыт и доступен"
    echo "3. DNS записи настроены правильно"
    exit 1
fi

echo ""
echo "SSL настройка завершена!"
echo "Теперь запустите: docker compose up --build" 