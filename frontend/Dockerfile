FROM node:20 as build-stage

# Рабочая директория для фронтенда
WORKDIR /frontend

# Копируем package.json и package-lock.json
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install --force

# Копируем все файлы фронтенда
COPY frontend/ .

# Собираем проект
RUN npm run build

FROM nginx:alpine
COPY --from=build-stage /frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80