FROM python:3.12-slim

# Устанавливаем git, ssh, supervisor, nginx, openssl для SSL (certbot установим через pip)
RUN apt-get update && apt-get install -y git openssh-client supervisor nginx openssl cron curl && rm -rf /var/lib/apt/lists/*

# Устанавливаем последнюю версию certbot через pip (избегаем баг с AttributeError)
RUN pip install --upgrade certbot

# Создаем директории для SSL сертификатов и webroot
RUN mkdir -p /etc/nginx/ssl /var/www/html

# Создаем временный самоподписанный SSL сертификат (будет заменен на Let's Encrypt)
RUN openssl req -x509 -nodes -days 1 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/nginx.key \
    -out /etc/nginx/ssl/nginx.crt \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=RestoCorp/OU=IT/CN=restocorp.ru"

# Устанавливаем правильные права на SSL файлы
RUN chmod 600 /etc/nginx/ssl/nginx.key
RUN chmod 644 /etc/nginx/ssl/nginx.crt

# Создаём рабочую директорию
WORKDIR /app

# Создаём .ssh директорию и устанавливаем права
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Копируем SSH-ключи (если вам действительно нужно клонировать по SSH)
COPY id_ed25519 /root/.ssh/id_rsa
COPY id_ed25519.pub /root/.ssh/id_rsa.pub

# Устанавливаем права доступа для SSH-ключей
RUN chmod 600 /root/.ssh/id_rsa /root/.ssh/id_rsa.pub

# Добавляем GitHub в known_hosts, отключаем проверку
RUN ssh-keyscan -H github.com >> /root/.ssh/known_hosts

# Клонируем репозиторий во временную директорию и переходим в ветку develop
RUN git clone git@github.com:Cossomoj/RAG_agent.git /app && git checkout MVP_2

# ВАЖНО: Копируем наш nginx.conf ПОСЛЕ клонирования, чтобы перезаписать версию из Git
COPY nginx.conf /etc/nginx/sites-available/ragapp
RUN ln -s /etc/nginx/sites-available/ragapp /etc/nginx/sites-enabled/
RUN rm /etc/nginx/sites-enabled/default

# Тестируем конфигурацию nginx
RUN nginx -t

# Создаём и активируем виртуальное окружение
RUN python3.12 -m venv /venv

# Обновляем pip и устанавливаем зависимости через `venv`
RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install --no-cache-dir -r src/main_version/requirements.txt
RUN /venv/bin/pip install --no-cache-dir -r admin/requirements.txt
RUN /venv/bin/pip install --no-cache-dir -r webapp/api/requirements.txt

# Устанавливаем переменные окружения для работы с виртуальным окружением
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"

# Устанавливаем права на исполнение для Python-скриптов
RUN chmod +x /app/src/main_version/*.py
RUN chmod +x /app/admin/*.py
RUN chmod +x /app/webapp/api/*.py

# Создаем улучшенный скрипт для получения SSL сертификата
RUN echo '#!/bin/bash\n\
echo "🔐 Получение SSL сертификата от Let'\''s Encrypt..."\n\
# Запускаем nginx в фоне для получения сертификата\n\
nginx\n\
sleep 3\n\
# Проверяем доступность домена\n\
if curl -s --max-time 10 http://restocorp.ru/.well-known/acme-challenge/test >/dev/null 2>&1; then\n\
    echo "✅ Домен доступен, пробуем получить сертификат..."\n\
else\n\
    echo "⚠️ Домен недоступен или есть проблемы с сетью"\n\
fi\n\
# Получаем сертификат от Let'\''s Encrypt используя webroot метод\n\
certbot certonly --webroot \\\n\
    --webroot-path=/var/www/html \\\n\
    --email admin@restocorp.ru \\\n\
    --agree-tos \\\n\
    --no-eff-email \\\n\
    --domains restocorp.ru \\\n\
    --non-interactive \\\n\
    --quiet\n\
if [ $? -eq 0 ] && [ -f "/etc/letsencrypt/live/restocorp.ru/fullchain.pem" ]; then\n\
    echo "✅ SSL сертификат успешно получен! Обновляем конфигурацию nginx..."\n\
    # Обновляем пути к сертификатам в конфигурации nginx\n\
    sed -i "s|ssl_certificate /etc/nginx/ssl/nginx.crt;|ssl_certificate /etc/letsencrypt/live/restocorp.ru/fullchain.pem;|g" /etc/nginx/sites-available/ragapp\n\
    sed -i "s|ssl_certificate_key /etc/nginx/ssl/nginx.key;|ssl_certificate_key /etc/letsencrypt/live/restocorp.ru/privkey.pem;|g" /etc/nginx/sites-available/ragapp\n\
    # Тестируем новую конфигурацию\n\
    if nginx -t; then\n\
        echo "✅ Конфигурация nginx обновлена успешно"\n\
    else\n\
        echo "❌ Ошибка в конфигурации nginx, возвращаем самоподписанные сертификаты"\n\
        sed -i "s|ssl_certificate /etc/letsencrypt/live/restocorp.ru/fullchain.pem;|ssl_certificate /etc/nginx/ssl/nginx.crt;|g" /etc/nginx/sites-available/ragapp\n\
        sed -i "s|ssl_certificate_key /etc/letsencrypt/live/restocorp.ru/privkey.pem;|ssl_certificate_key /etc/nginx/ssl/nginx.key;|g" /etc/nginx/sites-available/ragapp\n\
    fi\n\
else\n\
    echo "⚠️ Не удалось получить SSL сертификат, используем самоподписанный"\n\
    echo "   Возможные причины: домен недоступен извне, проблемы с DNS, лимиты Let'\''s Encrypt"\n\
fi\n\
# Останавливаем nginx\n\
nginx -s quit\n\
sleep 2' > /usr/local/bin/get-ssl.sh && chmod +x /usr/local/bin/get-ssl.sh

# Создаем скрипт запуска контейнера
RUN echo '#!/bin/bash\n\
echo "🚀 Запуск RAG сервиса..."\n\
# Получаем SSL сертификат\n\
/usr/local/bin/get-ssl.sh\n\
# Запускаем supervisor\n\
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/services.conf' > /usr/local/bin/start.sh && chmod +x /usr/local/bin/start.sh

# Настраиваем автообновление сертификата через cron (только если Let's Encrypt сертификат существует)
RUN echo "0 12 * * * [ -f /etc/letsencrypt/live/restocorp.ru/fullchain.pem ] && /usr/bin/certbot renew --quiet && supervisorctl restart nginx" > /etc/cron.d/certbot-renew
RUN chmod 0644 /etc/cron.d/certbot-renew
RUN crontab /etc/cron.d/certbot-renew

# Создаем конфигурацию для supervisor с добавлением cron
RUN echo '[supervisord]\nnodaemon=true\nlogfile=/var/log/supervisord.log\nlogfile_maxbytes=50MB\nlogfile_backups=10\nloglevel=info\n\n\
[program:cron]\ncommand=/usr/sbin/cron -f\nautostart=true\nautorestart=true\npriority=50\n\n\
[program:rag_service]\ncommand=/venv/bin/python3.12 /app/src/main_version/rag_service.py\nautostart=true\nautorestart=true\nstdout_logfile=/var/log/rag_service.log\nstderr_logfile=/var/log/rag_service_err.log\n\n\
[program:telegram_bot]\ncommand=/venv/bin/python3.12 /app/src/main_version/telegram_bot.py\nautostart=true\nautorestart=true\nstdout_logfile=/var/log/telegram_bot.log\nstderr_logfile=/var/log/telegram_bot_err.log\nstartretries=5\nstopasgroup=true\nkillasgroup=true\npriority=900\ndepends_on=rag_service\n\n\
[program:admin_app]\ncommand=/venv/bin/python3.12 /app/admin/app.py\nautostart=true\nautorestart=true\nstdout_logfile=/var/log/admin_app.log\nstderr_logfile=/var/log/admin_app_err.log\npriority=800\n\n\
[program:nginx]\ncommand=/usr/sbin/nginx -g "daemon off;"\nautostart=true\nautorestart=true\npriority=100\n\n\
[program:flask_api]\ncommand=/venv/bin/python3.12 /app/webapp/api/app.py\nenvironment=DATABASE_URL="/app/src/main_version/AI_agent.db"\nautostart=true\nautorestart=true\nstdout_logfile=/var/log/flask_api.log\nstderr_logfile=/var/log/flask_api_err.log\npriority=200\n' > /etc/supervisor/conf.d/services.conf

# Создаем каталог для логов
RUN mkdir -p /var/log

# Запускаем через наш стартовый скрипт
CMD ["/usr/local/bin/start.sh"]