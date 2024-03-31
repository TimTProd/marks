from datetime import datetime, date, time, timedelta, timezone
from time import sleep
import math
import json
import locale
import requests
from bs4 import BeautifulSoup
from config import *
from mechanize import Browser
from collections import Counter



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

    br = Browser()
    br.set_handle_equiv(False)
    br.addheaders = [('User-agent',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                        'Version/11.1.2 Safari/605.1.15')]
    br.set_handle_robots(False)

    # twice get
    try:
        br.open('https://schools.by/login')
    except:
        try:
            br.open('https://schools.by/login')
        except:
            return 'Ошибка соединения, попробуйте ещё раз. Возможно, schools.by временно не работает'

    # sleep(.5)


    # link to user's profile
    user_url = 'https://schools.by/login'
    try:
        # redirection to user's profile
        br.open('https://schools.by/login')
        br.select_form(nr=0)
        br.form["username"] = login
        br.form["password"] = password
        br.submit()
        user_url = br.geturl()
    except:
        return 'Ошибка соединения/получения данных, попробуйте ещё раз, или напишите в компанию TimTProd.'
    if user_url == 'https://schools.by/login':
        return 'Неверные данные авторизации ' 
    sleep(.5)
    return user_url, br

def get_marks(login, password, past_marks, previous_quarter=False) -> list:
    r"""Getting marks. Returns: list of strings with messages to send.

    :param login: String with login.
    :param password: String with password.
    :param past_marks: Dict with past marks
    :param previous_quarter: Bool. True if you need to get info about previous quarter.
    """
    parse_previous = PREVIOUS_QUARTER
    c_num = C_NUM
    start_from = START_FROM
    data = log_in(login, password)

    # error check
    if type(data) == str:
        return [data]
    # link to user's profile, requests.session()
    user_url, br = data
    # r = None


    if parse_previous:
        single_lessons = get_single_lessons(data)
        past_quarter_marks = get_marks_dict(data, True)
        single_lessons_pastmarks = {k: v for k, v in past_quarter_marks.items() if k in single_lessons} # dict with only marks for single lessons

    try:
        br.open(user_url + '/dnevnik/quarter/' + c_num + '/week/' + start_from)
    except:
        return ['Ошибка соединения E4, попробуйте ещё раз или пишите в компанию TimTProd.']

    # {'lesson': [9,9,10]}
    marks = {}
    lessons = set()

    # sleep(1)



    while True:
        soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")
        rows = soup.find_all('tr')
        c = 0 # bruh
        for row in rows:
            if row.find(class_='mark_box'):
                if c > 6: # bruh
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
                            if lesson == "Рус. яз.(урок без даты)":
                                lesson = "Рус. яз."
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
            else:
                c += 1 # bruh
        # go to next week
        if soup.find(class_='next'):
            next_week = soup.find(class_='next').get('send_to')
            try:
                next_week = next_week[next_week.find('dnevnik')-1:]
                next_date = datetime.strptime(next_week[next_week.find('week')+5:], '%Y-%m-%d')
                if next_date > datetime.now():
                    break
                else:
                    br.open(user_url + next_week)
            except:
                return ['Ошибка соединения E5, попробуйте ещё раз или пишите в компанию TimTProd.']
        else:
            break

    print(marks)
    print(lessons)

    if parse_previous:
        for key, value in marks.items():
            single_lessons_pastmarks.setdefault(key, []).extend(value)
        marks = single_lessons_pastmarks
    
    messages = []

    s = ''
    for lesson in sorted(marks.keys()):
        if lesson[-1] == '.':       # deleting dot in the end of a lesson
            lesson_b = lesson[:-1]
        else:
            lesson_b = lesson 
        s += '<b>' + lesson_b + ':</b> '

        # adding marks and making new marks bold
        bypass = False
        try:
            if (lesson not in past_marks):
                a = False
                bypass = True
                new_idx = 0
            else:
                a = (len(marks[lesson]) == past_marks[lesson]) 
        except:
            a = True
        for idx, mark in enumerate(marks[lesson]):
            if a:
                s += str(mark)+', '
            else:
                if not bypass:
                    amount = len(marks[lesson])
                    difference = amount - past_marks[lesson]
                    new_idx = len(marks[lesson]) - difference
                if idx < new_idx:
                    s += str(mark)+', '
                else:
                    s += '<u>' + str(mark) + '</u>, '

        s = s[:-2]
        s += '\n'
    s += 'Нету оценок по: '
    for lesson in lessons:
        if (lesson not in marks) and lesson and lesson != "ЧЗС":
            s += lesson.lower()
            s += ', '
    s = s[:-2]
    messages.append(s)

    s = 'Средний балл:\n'
    c = 0
    mark_sum = 0
    for lesson in sorted(marks.keys()):
        if lesson[-1] == '.':
            lesson_b = lesson[:-1]
        else:
            lesson_b = lesson 
        s += '<b>' + lesson_b + ':</b> '
        mean = sum(marks[lesson]) / max(len(marks[lesson]), 1)
        s += str(mean)[:5]
        rounded = my_round(mean)
        s += ' ('+str(rounded)+')'
        s += '\n'
        c += 1
        mark_sum += rounded
    s += 'Общий средний балл: '
    if c != 0:
        av = mark_sum / c
    else:
        av = 69
    s += '<b>' + str(round(av, 3)) + ' ('+str(my_round(av))+')' + '</b>'
    messages.append(s)

    # saving past marks
    s = {}
    for lesson in sorted(marks.keys()):
        s[lesson] = len(marks[lesson])
    for lesson in lessons:
        if (lesson not in marks) and lesson and lesson != "ЧЗС":
            s[lesson] = 0
    messages.append(s)

    return messages

def get_hometask(login, password):
    result_message = 'Д/з:\n'
    data = log_in(login, password)

    # error check
    if type(data) == str:
        return data

    user_url, br = data
    br.open(user_url+'/dnevnik/quarter/'+C_NUM)
    soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")

     # sunday or saturday and link to next week => send link to next week
    if get_time().weekday() > 4 and soup.find(class_='next'):
        next_week_link = soup.find(class_='next').get('send_to')
        br.open(user_url + next_week_link[next_week_link.find('/dnevnik'):])
        # changing info
        soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")

    rows = soup.find_all('tr')
    c = 0 # bruh
    for row in rows:
        # lesson
        if row.find(class_='mark_box'):
            if c > 6: # bruh
                lesson = normalize(row.find(class_='lesson').text)
                hometask = row.find(class_='ht-text')
                if hometask == None:
                    hometask = '-'
                else:
                    hometask = normalize(hometask.text)
                # removing numeration
                lesson = str(lesson[lesson.find('.')+1:]).strip()
                # if the string consists of more than just spaces
                if lesson.replace(' ', ''):
                    # deleting duplicate lessons
                    if result_message[-len(lesson)-1:] != lesson+'\n':
                        result_message += '<b>' + lesson + ':</b> <i>' + hometask + '</i>'+ '\n'
        # date
        else:
            if c > 5: # bruh
                weekday = normalize(row.find(class_='lesson').text)
                weekdayName = ''.join([i for i in weekday if not i.isdigit()]).replace(',','')
                if weekdayName != "Суббота ":
                    result_message += '\n' + '<b>---&gt'+weekday+'&lt---</b>' + '\n'
            c += 1 # bruh
    return result_message

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
    user_url, br = data
    br.open(user_url+'/dnevnik/quarter/'+C_NUM)
    soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")

    # sunday or saturday and link to next week => send link to next week
    if get_time().weekday() > 4 and soup.find(class_='next'):
        next_week_link = soup.find(class_='next').get('send_to')
        br.open(user_url + next_week_link[next_week_link.find('/dnevnik'):])
        # changing info
        soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")

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


def get_single_lessons(login_data):
    result_message = ''
    data = login_data

    # error check
    if type(data) == str:
        return data

    # link to user's profile, requests.session()
    user_url, br = data
    br.open(user_url+'/dnevnik/quarter/'+C_NUM)
    soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")

    # sunday or saturday and link to next week => send link to next week
    if get_time().weekday() > 4 and soup.find(class_='next'):
        next_week_link = soup.find(class_='next').get('send_to')
        br.open(user_url + next_week_link[next_week_link.find('/dnevnik'):])
        # changing info
        soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")

    rows = soup.find_all('tr')
    c = 0 # bruh
    for row in rows:
        # lesson
        if row.find(class_='mark_box'):
            if c > 6: # bruh
                lesson = normalize(row.find(class_='lesson').text)
                # removing numeration
                lesson = str(lesson[lesson.find('.')+1:]).strip()
                # if the string consists of more than just spaces
                if lesson.replace(' ', ''):
                    # deleting duplicate lessons
                    if result_message[-len(lesson)-1:] != lesson+'\n':
                        result_message += lesson+'\n'
        else:
            c += 1 # bruh
    
    res_list = result_message.split("\n")
    res_dict = dict(Counter(res_list))

    out = []
    for key, value in res_dict.items():
        if value == 1:
            out.append(key)

    return out

def get_marks_dict(login_data, previous_quarter=False):
    c_num = PREV_C_NUM if previous_quarter else C_NUM
    start_from = PREV_START_FROM if previous_quarter else START_FROM
    data = login_data

    # error check
    if type(data) == str:
        return [data]
    # link to user's profile, requests.session()
    user_url, br = data
    # r = None

    try:
        br.open(user_url + '/dnevnik/quarter/' + c_num + '/week/' + start_from)
    except:
        return ['Ошибка соединения E4, попробуйте ещё раз или пишите в компанию TimTProd.']

    # {'lesson': [9,9,10]}
    marks = {}
    lessons = set()

    sleep(1)

    while True:
        print(br.response())
        soup = BeautifulSoup(br.response(), 'html5lib', from_encoding="utf8")
        rows = soup.find_all('tr')
        c = 0 # bruh
        for row in rows:
            # checking if it's lesson
            if row.find(class_='mark_box'):
                if c > 6: # bruh
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
                            if lesson == "Рус. яз.(урок без даты)":
                                    lesson = "Рус. яз."
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
            else:
                c += 1 # bruh
        # go to next week
        if soup.find(class_='next'):
            next_week = soup.find(class_='next').get('send_to')
            try:
                next_week = next_week[next_week.find('dnevnik')-1:]
                br.open(user_url + next_week)
            except:
                return ['Ошибка соединения E5, попробуйте ещё раз или пишите в компанию TimTProd.']
        else:
            break

    print(marks)

    return marks


"""
29-01-2024:
    Сегодня обнаружилось, что сайт schools.by на запрос получения данных недели дневника 
    возвращает данные в двух экземплярах - для первого установлен признак, что его не надо
    отображать, а оценки в нем на два балла ниже. 


    Решил, пропуская первыую, "фальшивую" неделю. 
    Все строчки с комментарием "# bruh" оносятся к этому решению.
"""