FROM python:3.9

WORKDIR /app
COPY monitor.py /app/

RUN pip install requests psutil telebot matplotlib

CMD ["sh", "-c", "sleep 120 && python monitor.py"]
#CMD ["python", "monitor.py"]
