Last login: Sun Apr 20 12:53:17 on ttys003
➜  ~ ssh -i ~/.ssh/id_ed25519 user1@213.171.25.85
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 5.15.0-133-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

 System information as of Sun Apr 20 01:38:22 PM MSK 2025

  System load:  0.0                Processes:               161
  Usage of /:   44.5% of 29.42GB   Users logged in:         1
  Memory usage: 64%                IPv4 address for enp3s0: 213.171.25.85
  Swap usage:   0%

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

33 updates can be applied immediately.
To see these additional updates run: apt list --upgradable

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status

New release '24.04.2 LTS' available.
Run 'do-release-upgrade' to upgrade to it.


*** System restart required ***
Last login: Sun Apr 20 12:53:23 2025 from 46.8.6.167
user1@testttq:~$ docker exec -it rag_service2 /bin/bash
root@afff837f5472:/app# cd src/main_version/
root@afff837f5472:/app/src/main_version# nano telegram_bot.py 
root@afff837f5472:/app/src/main_version# exit
exit
user1@testttq:~$ docker exec -it rag_service2 /bin/bash
root@afff837f5472:/app# python3.12 telegram_bot.py
python3.12: can't open file '/app/telegram_bot.py': [Errno 2] No such file or directory
root@afff837f5472:/app# venv/bin/python3.12 src/main_version/telegram_bot.py
bash: venv/bin/python3.12: No such file or directory
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
Traceback (most recent call last):
  File "/app/src/main_version/telegram_bot.py", line 106, in <module>
    init_db()
  File "/app/src/main_version/telegram_bot.py", line 58, in init_db
    conn = sqlite3.connect(DATABASE_URL)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: unable to open database file
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
Traceback (most recent call last):
  File "/app/src/main_version/telegram_bot.py", line 106, in <module>
    init_db()
  File "/app/src/main_version/telegram_bot.py", line 58, in init_db
    conn = sqlite3.connect(DATABASE_URL)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: unable to open database file
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
Текущий часовой пояс: ('UTC', 'UTC')
Текущий часовой пояс:13:44
^Croot@afff837f5472:/appnano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
Системный часовой пояс: ('UTC', 'UTC')
Московское время: 2025-04-20 13:54:21
Traceback (most recent call last):
  File "/app/src/main_version/telegram_bot.py", line 1305, in <module>
    print(f"Текущий часовой пояс:{current_timenow}")
                                  ^^^^^^^^^^^^^^^
NameError: name 'current_timenow' is not defined
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
Системный часовой пояс: ('UTC', 'UTC')
Московское время: 2025-04-20 13:56:03
Traceback (most recent call last):
  File "/app/src/main_version/telegram_bot.py", line 1305, in <module>
    print(f"Текущий часовой пояс:{current_timenow}")
                                  ^^^^^^^^^^^^^^^
NameError: name 'current_timenow' is not defined
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
Системный часовой пояс: ('UTC', 'UTC')
Московское время: 2025-04-20 13:58:01
Текущий часовой пояс:13:58
^Croot@afff837f5472:/appnano12 src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
TELEGRAM_API_KEY установлен: Да
FEEDBACK_BOT_TOKEN установлен: Да
FEEDBACK_CHAT_ID установлен: Да
Системный часовой пояс: ('UTC', 'UTC')
Московское время: 2025-04-20 14:00:45
Текущий часовой пояс:14:00
^Croot@afff837f5472:/appnano12 src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
  File "/app/src/main_version/telegram_bot.py", line 67
    print(f"Ошибка подключения к API Telegram: {e}")print("Подключение к API Telegram...")
                                                    ^^^^^
SyntaxError: invalid syntax
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
  File "/app/src/main_version/telegram_bot.py", line 67
    print(f"Ошибка подключения к API Telegram: {e}")print("Подключение к API Telegram...")
                                                    ^^^^^
SyntaxError: invalid syntax
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
TELEGRAM_API_KEY установлен: Да
FEEDBACK_BOT_TOKEN установлен: Да
FEEDBACK_CHAT_ID установлен: Да
Traceback (most recent call last):
  File "/app/src/main_version/telegram_bot.py", line 111, in <module>
    init_db()
  File "/app/src/main_version/telegram_bot.py", line 64, in init_db
    cursor = conn.cursor()
             ^^^^
NameError: name 'conn' is not defined
root@afff837f5472:/app# nano src/main_version/telegram_bot.py
root@afff837f5472:/app# python3.12 src/main_version/telegram_bot.py
TELEGRAM_API_KEY установлен: Да
FEEDBACK_BOT_TOKEN установлен: Да
FEEDBACK_CHAT_ID установлен: Да
Системный часовой пояс: ('UTC', 'UTC')
Московское время: 2025-04-20 14:09:44
Текущий часовой пояс:14:09
Подключение к API Telegram...
Бот подключен успешно! ID: 8159061414, Имя: mygigabot
Пользователь с ID 191136151 уже существует в базе данных.
Текущие пользователи в базе данных:
ID: 70735394, Username: openm1ke, Имя: Michael @quarkron, Напоминания: 1, Время создания: 2025-04-08 17:55:44
ID: 191136151, Username: Mplusk, Имя: Max Сossomoj, Напоминания: 0, Время создания: 2025-04-06 13:35:01
ID: 191383351, Username: zebracon, Имя: Dmitry Li, Напоминания: 1, Время создания: 2025-04-08 08:37:28
ID: 194412572, Username: jmabel42, Имя: Maria Korshunova, Напоминания: 1, Время создания: 2025-04-08 08:47:28
ID: 232386950, Username: avoreshin, Имя: 𝔸ℕ𝔻ℝ𝔼𝕐 • 𝕆ℝ𝔼𝕊ℍ𝕀ℕ, Напоминания: 1, Время создания: 2025-04-08 09:19:51
ID: 243416466, Username: inmakhmutov, Имя: Ильнур, Напоминания: 1, Время создания: 2025-04-08 09:00:45
ID: 259804081, Username: sparrvio, Имя: Vladimir, Напоминания: 1, Время создания: 2025-04-08 08:54:52
ID: 273551240, Username: Spvcefvrer, Имя: R, Напоминания: 1, Время создания: 2025-04-08 16:29:23
ID: 284304930, Username: kvther1ne, Имя: Катя, Напоминания: 1, Время создания: 2025-04-08 16:47:16
ID: 327976753, Username: dradns, Имя: Nikita, Напоминания: 1, Время создания: 2025-04-06 16:44:03
ID: 337092929, Username: avsolon, Имя: Andrey | ayeshacy, Напоминания: 1, Время создания: 2025-04-10 07:42:25
ID: 339193247, Username: litteralIy, Имя: Даниил 🖇, Напоминания: 1, Время создания: 2025-04-10 03:55:38
ID: 353457323, Username: moses_maxim, Имя: Максим Л, Напоминания: 1, Время создания: 2025-04-10 03:44:37
ID: 356947158, Username: bosmc, Имя: Sergei Bostan, Напоминания: 1, Время создания: 2025-04-10 04:45:33
ID: 373914836, Username: engineerAlekseev, Имя: Антон Алексеев, Напоминания: 1, Время создания: 2025-04-10 03:46:29
ID: 384867395, Username: shefdan, Имя: Даниил Шевченко(S21), Напоминания: 1, Время создания: 2025-04-11 10:33:00
ID: 398019362, Username: roman_barr, Имя: Роман, Напоминания: 1, Время создания: 2025-04-08 16:51:37
ID: 401194952, Username: bwl_lvv, Имя: Lev U, Напоминания: 1, Время создания: 2025-04-07 10:43:24
ID: 412270239, Username: neshin_nikita, Имя: Никита Нешин, Напоминания: 1, Время создания: 2025-04-10 03:50:05
ID: 416006204, Username: SergeyMech, Имя: Сергей, Напоминания: 1, Время создания: 2025-04-09 06:41:11
ID: 424140717, Username: alexr_home, Имя: Alexander [redavero], Напоминания: 1, Время создания: 2025-04-06 06:27:07
ID: 429718895, Username: LanaLebedeva2021, Имя: Светлана, Напоминания: 1, Время создания: 2025-04-09 08:19:22
ID: 442150121, Username: AndreyKaliushka, Имя: Andrew Kaliushka, Напоминания: 1, Время создания: 2025-04-10 04:06:30
ID: 480183049, Username: maxim_ilenkov, Имя: Max Ilyenkov, Напоминания: 1, Время создания: 2025-04-09 08:06:44
ID: 511174105, Username: betonnnnnnnn, Имя: 8eton, Напоминания: 1, Время создания: 2025-04-05 19:19:39
ID: 664996649, Username: vldo_osic, Имя: Vlad, Напоминания: 1, Время создания: 2025-04-08 09:38:12
ID: 692107490, Username: biryukovaoly, Имя: Оля, Напоминания: 1, Время создания: 2025-04-06 08:35:04
ID: 717704958, Username: leanorac, Имя: Наталия leanorac @leanorac, Напоминания: 1, Время создания: 2025-04-07 08:44:04
ID: 718840622, Username: flematico, Имя: Elizaveta, Напоминания: 1, Время создания: 2025-04-07 09:39:48
ID: 724372646, Username: kirikova_k, Имя: Ксю, Напоминания: 1, Время создания: 2025-04-09 05:19:28
ID: 732984495, Username: raif10, Имя: Raif s21:mirmulnb, Напоминания: 1, Время создания: 2025-04-08 16:44:52
ID: 826130249, Username: leygoodb, Имя: Василий Денисов, Напоминания: 1, Время создания: 2025-04-08 09:33:31
ID: 905373213, Username: mari_a_step, Имя: Мария С Lady Bug, Напоминания: 1, Время создания: 2025-04-09 07:59:43
ID: 932436423, Username: mikhailrotar2707, Имя: Михаил Ротарь, Напоминания: 1, Время создания: 2025-04-08 16:46:39
ID: 934573696, Username: bronzeX2, Имя: Матвей, Напоминания: 1, Время создания: 2025-04-10 10:21:11
ID: 969679947, Username: winonale_21, Имя: Esenbekov, Напоминания: 1, Время создания: 2025-04-08 08:52:40
ID: 1071674964, Username: marryyapplepie, Имя: Мария Стенина, Напоминания: 1, Время создания: 2025-04-09 09:16:27
ID: 1130799107, Username: glossuvi, Имя: Кристина Тихонова s21_glossuvi, Напоминания: 1, Время создания: 2025-04-08 09:04:53
ID: 1184717128, Username: vagra348, Имя: Оля, Напоминания: 1, Время создания: 2025-04-11 07:10:10
ID: 1259984067, Username: accordij, Имя: Dmitry Middle Coffee ☕️, Напоминания: 1, Время создания: 2025-04-10 05:37:53
ID: 1274133093, Username: granceti, Имя: СИЯЙ, Напоминания: 1, Время создания: 2025-04-10 03:50:54
ID: 5375925178, Username: veeerzh, Имя: алина, Напоминания: 1, Время создания: 2025-04-06 19:46:25
ID: 5484157606, Username: Slava20011, Имя: Vyacheslav, Напоминания: 1, Время создания: 2025-04-10 04:00:56
ID: 7188178658, Username: gerriom, Имя: Никита, Напоминания: 1, Время создания: 2025-04-10 07:35:24
ID: 7320836542, Username: ZM23GlzhmyoW, Имя: Sharon Kent, Напоминания: 1, Время создания: 2025-04-08 12:48:57
ID: 8121021851, Username: Igorm_job, Имя: Игорь М, Напоминания: 1, Время создания: 2025-04-08 16:44:10
Что я могу ожидать от специалиста
191136151
/app/src/main_version/telegram_bot.py:183: DeprecationWarning: The default datetime adapter is deprecated as of Python 3.12; see the sqlite3 documentation for suggested replacement recipes
  cursor.execute('''
Получено пустое сообщение от WebSocket.
Получено пустое сообщение от WebSocket.
Получено пустое сообщение от WebSocket.

^[[A^C^Croot@afff837f547nanothon3.12 src/main_version/telegram_bot.py

  GNU nano 7.2                                    src/main_version/telegram_bot.py                                              
import telebot
from dotenv import load_dotenv
from telebot import types
import asyncio
import websockets
import requests
import json
import time
import os
import sqlite3
import schedule
from datetime import datetime, UTC, timedelta
import threading
import pytz
import pytz
from datetime import datetime

load_dotenv()

DATABASE_URL = "/app/src/main_version/AI_agent.db"    

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

dialogue_context = {}
count_questions_users = {}

secret_key = os.getenv("TELEGRAM_API_KEY")
FEEDBACK_BOT_TOKEN = os.getenv("FEEDBACK_BOT_TOKEN")
FEEDBACK_CHAT_ID = os.getenv("FEEDBACK_CHAT_ID")

print(f"TELEGRAM_API_KEY установлен: {'Да' if os.getenv('TELEGRAM_API_KEY') else 'Нет'}")
                                                      [ Read 1322 lines ]
^G Help         ^O Write Out    ^W Where Is     ^K Cut          ^T Execute      ^C Location     M-U Undo        M-A Set Mark
^X Exit         ^R Read File    ^\ Replace      ^U Paste        ^J Justify      ^/ Go To Line   M-E Redo        M-6 Copy
