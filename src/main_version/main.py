import subprocess
import sys
import time

# Пути к скриптам, которые нужно запустить
script1 = 'rag_service.py'
script2 = 'telegram_bot.py'

# Функция для запуска скрипта в фоновом режиме
def run_script_in_background(script_path):
    try:
        # Запуск скрипта в фоновом режиме с использованием Popen
        process = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Скрипт {script_path} запущен в фоновом режиме с PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Ошибка при запуске скрипта {script_path}: {e}")
        return None

# Запуск скриптов в фоновом режиме
if __name__ == "__main__":
    process1 = run_script_in_background(script1)
    time.sleep(30)
    process2 = run_script_in_background(script2)