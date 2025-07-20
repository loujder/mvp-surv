# PowerShell скрипт для настройки SSL сертификатов

Write-Host "Настройка SSL сертификатов для домена..." -ForegroundColor Green

# Проверяем, существует ли .env файл
if (-not (Test-Path ".env")) {
    Write-Host "Ошибка: Файл .env не найден. Сначала запустите setup-env.ps1" -ForegroundColor Red
    exit 1
}

# Загружаем переменные из .env
$envContent = Get-Content ".env"
foreach ($line in $envContent) {
    if ($line -match '^([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

# Проверяем, что DOMAIN установлен
$domain = $env:DOMAIN
if (-not $domain -or $domain -eq "your-domain.com") {
    Write-Host "Ошибка: DOMAIN не настроен в .env файле" -ForegroundColor Red
    Write-Host "Укажите ваш реальный домен в переменной DOMAIN" -ForegroundColor Yellow
    exit 1
}

Write-Host "Настройка SSL для домена: $domain" -ForegroundColor Cyan

# Проверяем, установлен ли certbot
if (-not (Get-Command certbot -ErrorAction SilentlyContinue)) {
    Write-Host "Установка certbot..." -ForegroundColor Yellow
    
    # Для Windows используем Chocolatey или winget
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Установка через Chocolatey..." -ForegroundColor Yellow
        choco install certbot -y
    } elseif (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Установка через winget..." -ForegroundColor Yellow
        winget install certbot
    } else {
        Write-Host "Ошибка: Не удалось установить certbot автоматически" -ForegroundColor Red
        Write-Host "Установите certbot вручную с https://certbot.eff.org/" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Для Windows рекомендуется использовать внешний сервер для получения SSL сертификатов." -ForegroundColor Yellow
Write-Host ""
Write-Host "Альтернативные варианты:" -ForegroundColor Cyan
Write-Host "1. Использовать Let's Encrypt на Linux сервере" -ForegroundColor White
Write-Host "2. Использовать Cloudflare SSL (бесплатно)" -ForegroundColor White
Write-Host "3. Купить SSL сертификат у провайдера" -ForegroundColor White
Write-Host ""
Write-Host "Для настройки Cloudflare SSL:" -ForegroundColor Green
Write-Host "1. Зарегистрируйтесь на cloudflare.com" -ForegroundColor White
Write-Host "2. Добавьте ваш домен $domain" -ForegroundColor White
Write-Host "3. Измените DNS записи на Cloudflare" -ForegroundColor White
Write-Host "4. Включите 'Always Use HTTPS' в настройках SSL/TLS" -ForegroundColor White
Write-Host "5. Установите 'Full (strict)' режим SSL" -ForegroundColor White
Write-Host ""
Write-Host "После настройки SSL запустите: docker compose up --build" -ForegroundColor Green 