<h1 align="center">Marks</h1>
<br>

Marks - это бот для получения оценок с [schools](https://schools.by/) на Python.

 - **Трейлер**: https://youtu.be/t9WYEowmDxU
 - **Исходный код**: https://github.com/IronGunYT/marks

Возможности
----------------------
- Просмотр оценок по предмету одной строкой
- Подсчёт среднего балла по предмету
- Просмотр оценок за текущую и предыдущую неделю
- Получение расписания на текущую неделю по датам
- Защита от флуда и возможность блокирования пользователей

Пример оценки
----------------------
<img src="https://i.ibb.co/G5PPY79/2bc52a58be.png" height=500>

Установка
----------------------

 1. Клонируем репозиторий
 2. Устанавливаем необходимые библиотеки через cmd
`pip3 install -r requirements.txt`
 3. Создаём файл `config.py`
 4. Настраиваем запуск бота через systemctl([гайд](https://help.sprintbox.ru/perl-python-nodejs/python-telegram-bots#bot-launch)) или используем `start.py`
 `python3 start.py`

Содержание config.py
----------------------
TOKEN = "Токен бота"\
LOG_CHAT_ID = "ID канала с ботом, для логов"\
C_NUM = "Номер текущей четверти (найти на сайте)"\
PREV_C_NUM = "Номер прошлой четверти"\
START_FROM = "Дата начала четверти (Например: "2023-08-28")"\
PREV_START_FROM = "Аналогично с START_FROM, но для прошлой четверти"

Как запустить с Docker
----------------------
1. Билдим
`docker build . -t marks_bot`
2. Запускаем в фоновом режиме (bot_vol – для сохранения базы паролей)
`docker run -d -v bot_vol:/usr/src/app/bd --name marks_bot marks_bot`
