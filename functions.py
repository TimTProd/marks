from datetime import datetime, date, time, timedelta, timezone
from time import sleep
import math
import json
import locale
import requests
from bs4 import BeautifulSoup
from config import *


def get_time():
    delta = timedelta(hours=3, minutes=0)
    return datetime.now(timezone.utc) + delta


def my_round(i):
    return math.ceil(i) if math.modf(i)[0] == 0.5 else round(i)


def normalize(s) -> str:
    return str(s).replace('  ', '').replace('\n', '')


def log_in(login, password):
    r"""Log in on schools.by. Returns: string if Error else tuple(user_url: string, class:`Session`).

    :param login: String with login.
    :param password: String with password.
    """
    s = requests.session()
    # response
    r = None

    # twice get
    try:
        r = s.get('https://schools.by/login')
    except requests.exceptions.ConnectionError as e:
        try:
            r = s.get('https://schools.by/login')
        except requests.exceptions.ConnectionError as e:
            return 'Ошибка соединения, попробуйте ещё раз или напишите @irongun. Возможно, schools.by временно не работает'

    csrf = r.cookies['csrftoken']

    # request description
    data = {
        'csrfmiddlewaretoken': csrf,
        'username': login,
        'password': password
    }
    headers = sample_headers
    cookies = sample_cookies
    cookies.update({'csrftoken': csrf})
    sleep(.5)

    # link to user's profile
    user_url = 'https://schools.by/login'
    try:
        # redirection to user's profile
        r = s.post('https://schools.by/login', data=data, headers=headers, cookies=cookies)
        user_url = r.url
    except requests.exceptions.ConnectionError as e:
        return 'Ошибка соединения/получения данных, попробуйте ещё раз или напишите @irongun'
    if user_url == 'https://schools.by/login':
        return 'Неверные данные авторизации'
    sleep(.5)
    return user_url, s

def get_marks(login, password, previous_quarter=False) -> list:
    r"""Getting marks. Returns: list of strings with messages to send.

    :param login: String with login.
    :param password: String with password.
    :param previous_quarter: Bool. True if you need to get info about previous quarter.
    """
    c_num = PREV_C_NUM if previous_quarter else C_NUM
    start_from = PREV_START_FROM if previous_quarter else START_FROM
    data = log_in(login, password)

    # error check
    if type(data) == str:
        return [data]
    # link to user's profile, requests.session()
    user_url, s = data
    r = None

    try:
        r = s.get(user_url + '/dnevnik/quarter/' + c_num + '/week/' + start_from)
    except requests.exceptions.ConnectionError as e:
        return ['Ошибка соединения E4, попробуйте ещё раз или напишите @irongun']

    # {'lesson': [9,9,10]}
    marks = {}
    lessons = set()

    while True:
        soup = BeautifulSoup(r.text, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            # checking if it's lesson
            if row.find(class_='mark_box'):
                # checking for a mark
                if row.find(class_='mark_box').find('strong'):
                    mark = normalize(row.find(class_='mark_box').find('strong').text)
                    normalize_mark = ''
                    for letter in mark:
                        if letter.isdigit() or letter == '/':
                            normalize_mark += letter
                    mark = str(normalize_mark)
                    if mark:
                        # double mark
                        if '/' in mark:
                            mark = mark.split('/')
                        else:
                            mark = [mark]
                        lesson = row.find(class_='lesson')
                        lesson = normalize(lesson.find('span').text)
                        # removing numeration
                        lesson = lesson[lesson.find('.')+1:].strip()
                        for el in mark:
                            if str(el).isdigit():
                                el = int(el)
                                if lesson in marks:
                                    marks[lesson].append(el)
                                else:
                                    marks[lesson] = [el]
                else:
                    lesson = row.find(class_='lesson')
                    lesson = normalize(lesson.find('span').text)
                    # removing numeration
                    lesson = lesson[lesson.find('.') + 1:].strip()
                    lessons.add(lesson)
        # go to next week
        if soup.find(class_='next'):
            next_week = soup.find(class_='next').get('send_to')
            try:
                next_week = next_week[next_week.find('dnevnik')-1:]
                r = s.get(user_url + next_week)
            except requests.exceptions.ConnectionError as e:
                return ['Ошибка соединения E5, попробуйте ещё раз или напишите @irongun']
        else:
            break

    print(marks)
    print(lessons)
    messages = []

    s = 'Оценки:\n'
    for lesson in sorted(marks.keys()):
        s += lesson + ': '
        for mark in marks[lesson]:
            s += str(mark)+', '
        s = s[:-2]
        s += '\n'
    s += 'Нету оценок по: '
    for lesson in lessons:
        if (lesson not in marks) and lesson:
            s += lesson.lower()
            s += ', '
    s = s[:-2]
    messages.append(s)

    s = 'Средний балл:\n'
    for lesson in sorted(marks.keys()):
        s += lesson + ': '
        mean = sum(marks[lesson]) / max(len(marks[lesson]), 1)
        s += str(mean)[:5]
        s += ' ('+str(my_round(mean))+')'
        s += '\n'
    messages.append(s)

    return messages


def get_timetable(login, password) -> str:
    r"""Getting timetable of current week. Returns: string of message to send.

    :param login: String with login.
    :param password: String with password.
    """
    result_message = 'Расписание:\n'
    data = log_in(login, password)

    # error check
    if type(data) == str:
        return data

    # link to user's profile, requests.session()
    user_url, s = data
    r = s.get(user_url+'/dnevnik/quarter/'+C_NUM)
    soup = BeautifulSoup(r.text, 'html.parser')

    # sunday or saturday and link to next week => send link to next week
    if get_time().weekday() > 4 and soup.find(class_='next'):
        next_week_link = soup.find(class_='next').get('send_to')
        r = s.get(user_url + next_week_link[next_week_link.find('/dnevnik'):])
        # changing info
        soup = BeautifulSoup(r.text, 'html.parser')

    rows = soup.find_all('tr')
    for row in rows:
        # lesson
        if row.find(class_='mark_box'):
            lesson = normalize(row.find(class_='lesson').text)
            # removing numeration
            lesson = str(lesson[lesson.find('.')+1:]).strip()
            # if the string consists of more than just spaces
            if lesson.replace(' ', ''):
                # deleting duplicate lessons
                if result_message[-len(lesson)-1:] != lesson+'\n':
                    result_message += lesson+'\n'
        # date
        else:
            weekday = normalize(row.find(class_='lesson').text)
            result_message += '-->'+weekday+'<--'+'\n'
    return result_message

