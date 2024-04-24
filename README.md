<h1 align="center">Marks</h1>
<br>

Marks - это бот для получения оценок с [schools](https://schools.by/) на Python.

 - **Оригинальный репозиторий**: https://github.com/IronGunYT/marks

Возможности
----------------------
- Просмотр оценок по предмету одной строкой
- Подсчёт среднего балла по предмету
- Просмотр оценок за текущую и предыдущую неделю
- Получение домашнего задания

Пример оценки
----------------------
<img src="https://i.ibb.co/G5PPY79/2bc52a58be.png" height=500>

Как установить с Docker
----------------------
`make build`

ЛИБО:
1. Билдим
`docker build . -t marks_bot`
2. Запускаем в фоновом режиме (bot_vol – для сохранения базы паролей)
`docker run -d -v bot_vol:/usr/src/app/bd --name marks_bot marks_bot`

Установка локально на комп
----------------------

 1. Клонируем репозиторий
 2. Устанавливаем необходимые библиотеки через cmd
`pip3 install -r requirements.txt`
 3. Создаём файл `config.py`
 4. Настраиваем запуск бота через systemctl([гайд](https://help.sprintbox.ru/perl-python-nodejs/python-telegram-bots#bot-launch)) или используем `start.py`
 `python3 start.py`

Содержание config.py
----------------------
BOT_TOKEN = "Токен бота"\
LOG_CHAT_ID = <ID группы с ботом, для логов>\
Q_NUM = "Номер текущей четверти (найти на сайте)"\
PREV_Q_NUM = "Номер прошлой четверти"\
START_FROM = "Дата начала четверти (Например: "2023-08-28")"\
PREV_START_FROM = "Аналогично с START_FROM, но для прошлой четверти"\
OWNER_ID = <ID владельца>\
API_ID = <Api приложения телеграма>\
API_HASH = <Hash приложения телеграма>



