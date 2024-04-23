import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from math import ceil, modf
from collections import Counter


def get_time():
    delta = timedelta(hours=3, minutes=0)
    return datetime.now(timezone.utc) + delta

def normalize(s) -> str:
    return str(s).replace('  ', '').replace('\n', '')

def my_round(i):
    return ceil(i) if modf(i)[0] == 0.5 else round(i)


async def log_in(login, password):
    # Create an aiohttp ClientSession instance
    session = aiohttp.ClientSession()
    headers = {
        'Referer': 'https://schools.by/login',
        'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15'
    }

    # Open the login page and retrieve the CSRF token
    try:
        async with session.get('https://schools.by/login', headers=headers) as response:
            csrf_token = session.cookie_jar.filter_cookies('https://schools.by').get('csrftoken').value
            if response.status != 200 or not csrf_token:
                return 'Connection error or CSRF token not found, please try again.'
    except:
        return 'Connection error, please try again.'

    # Prepare the payload with login credentials and CSRF token
    payload = {
        'csrfmiddlewaretoken': csrf_token,  # Include the CSRF token in your payload
        'username': login,
        'password': password,
        '|123': '|123'
    }

    # Submit the login form with CSRF token
    try:
        async with session.post('https://schools.by/login', data=payload, headers=headers) as response:
            user_url = str(response.url)
            if user_url == 'https://schools.by/login':
                return 'Invalid login credentials'
    except:
        return 'Error connecting/retrieving data, please try again.'

    # Return the user URL and the session
    return user_url, session

async def get_marks(login, password, q_num, start_from, prev_q_num=0, prev_start_from=0, parse_previous=False, past_marks={}, dict=False):
    data = await log_in(login, password)

    if type(data) == str:
        return data

    user_url, session = data

    if parse_previous:
        single_lessons = await get_single_lessons(user_url, session, q_num)
        previous_quarter_marks = await get_marks(login, password, prev_q_num, prev_start_from, parse_previous=False, dict=True)
        single_lessons_pastmarks = {k: v for k, v in previous_quarter_marks.items() if k in single_lessons} # dict with only marks for single lessons

    try:
        response = await session.get(user_url + '/dnevnik/quarter/' + q_num + '/week/' + start_from)
    except:
        return 'Connection error, please try again.'
    

    # {'lesson': [9,9,10]}
    marks = {}
    lessons = set()

    while True:
        soup = BeautifulSoup(await response.text(), 'html5lib')
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
                    response = await session.get(user_url + next_week)
            except:
                return 'Connection error, please try again.'
        else:
            break                        
    
    if parse_previous:
        for key, value in marks.items():
            single_lessons_pastmarks.setdefault(key, []).extend(value)
        marks = single_lessons_pastmarks
    
    await session.close()

    if dict:
        return marks
    else:
        messages = []

        s = ''
        for lesson in sorted(marks.keys()):
            if lesson[-1] == '.':       # deleting dot in the end of a lesson
                lesson_b = lesson[:-1]
            else:
                lesson_b = lesson
            s += '<b>' + lesson_b + ':</b> '
        
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

async def get_single_lessons(user_url, session, q_num):
    result_message = ''

    response = await session.get(user_url+'/dnevnik/quarter/'+q_num)
    soup = BeautifulSoup(await response.text(), 'html5lib')

    # sunday or saturday and link to next week => send link to next week
    if get_time().weekday() > 4 and soup.find(class_='next'):
        next_week_link = soup.find(class_='next').get('send_to')
        response = await session.get(user_url + next_week_link[next_week_link.find('/dnevnik'):])
        # changing info
        soup = BeautifulSoup(await response.text(), 'html5lib')

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

async def get_hometask(login, password, q_num, scroll="start"):
    result_message = 'Д/з:\n'

    data = await log_in(login, password)

    if type(data) == str:
        return data

    user_url, session = data

    try:
        response = await session.get(user_url+'/dnevnik/quarter/'+q_num)
    except:
        return 'Connection error, please try again.'
    
    soup = BeautifulSoup(await response.text(), 'html5lib')
    
    # sunday or saturday and link to next week => send link to next week
    if get_time().weekday() > 4 and soup.find(class_='next'):
        next_week_link = soup.find(class_='next').get('send_to')
        response = await session.get(user_url + next_week_link[next_week_link.find('/dnevnik'):])
        # changing info
        soup = BeautifulSoup(await response.text(), 'html5lib')
    
    # callbacks
    if scroll == "start":
        pass
    elif scroll.startswith('next_'):
        n = int(scroll.split("_")[1])
        for i in range(n):
            if soup.find(class_='next'):
                next_week_link = soup.find(class_='next').get('send_to')
                response = await session.get(user_url + next_week_link[next_week_link.find('/dnevnik'):])
                soup = BeautifulSoup(await response.text(), 'html5lib')
    elif scroll.startswith('previous_'):
        n = int(scroll.split("_")[1])
        for i in range(n):
            if soup.find(class_='prev'):
                previous_week_link = soup.find(class_='prev').get('send_to')
                response = await session.get(user_url + previous_week_link[previous_week_link.find('/dnevnik'):])
                soup = BeautifulSoup(await response.text(), 'html5lib')

    await session.close()
    
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
