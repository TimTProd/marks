import numpy as np

users_dict = np.load('./bd/bd.npy', allow_pickle=True).item()
users_dict = dict(users_dict)

pastMarks_dict = np.load('./bd/marks.npy', allow_pickle=True).item()
pastMarks_dict = dict(pastMarks_dict)

def update_marks_database():
    np.save('./bd/marks.npy', pastMarks_dict)

def update_database():
    np.save('./bd/bd.npy', users_dict)

def user_exists(id):
    return id in users_dict

def set_state(id, state):
    users_dict.update({id: [get_login(id), get_password(id), state]})

def get_state(id):
    return users_dict[id][2]

def get_login(id):
    return users_dict[id][0]

def get_password(id):
    return users_dict[id][1]

def set_login(id, login):
    users_dict.update({id: [login, 'None', 0]})

def set_password(id, password):
    users_dict.update({id: [get_login(id), password, 0]})

def get_dict():
    return str(users_dict)

def create_user(id):
    users_dict.update({id: ['None', 'None', 0]})

def create_pastMarks(id):
    pastMarks_dict.update({id: {}})

def set_pastMarks(id, past_marks):
    pastMarks_dict.update({id: past_marks})

def get_pastMarks(id):
    return pastMarks_dict[id]