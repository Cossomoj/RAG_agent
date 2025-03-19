FROM python:3.12-slim

# Устанавливаем git и ssh
RUN apt-get update && apt-get install -y git openssh-client && rm -rf /var/lib/apt/lists/*

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

# Клонируем репозиторий во временную директорию
RUN git clone git@github.com:leanorac/Rag_agent_LLM_Telegram_bot_MY.git /app

# Переходим в ветку develop
#RUN cd src && git checkout develop
#RUN git checkout develop

# Создаём и активируем виртуальное окружение
RUN python3.12 -m venv /venv

# Обновляем pip и устанавливаем зависимости через `venv`
RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install --no-cache-dir -r src/main_version/requirements.txt

# (Опционально) Копируем .env внутрь контейнера
COPY .env /app/.env

# Устанавливаем переменные окружения для работы с виртуальным окружением
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"

# Устанавливаем права на исполнение для Python-скриптов
RUN chmod +x /app/src/main_version/rag_service.py
RUN chmod +x /app/src/main_version/telegram_bot.py

# Создаём директорию для логов
RUN mkdir -p /logs

# Запускаем Python-приложение через `venv`
CMD ["/bin/bash", "-c", "python3.12 src/main_version/rag_service.py & sleep 20 && python3.12 src/main_version/telegram_bot.py"]
#CMD ["/bin/bash", "-c", "python3.12 src/main_version/rag_service.py > /logs/rag_service.log 2>&1 & sleep 20 && python3.12 src/main_version/telegram_bot.py > /logs/telegram_bot.log 2>&1"]
