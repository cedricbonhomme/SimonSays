#! /usr/bin/env python
# -*- coding: utf-8 -*-

from flask import session, request, g
from flask.ext.socketio import SocketIO, emit, join_room,  \
                                leave_room, close_room, disconnect

from flask.ext.login import LoginManager, login_user, logout_user, \
                            login_required, current_user, AnonymousUserMixin

from web import socketio, USERS
from models import User, Game
from games import *

NAMESPACE = "/test"
current_game = None
from models import Game
from games.utils import WaitGame
from random import choice
from threading import Timer
import copy
import time

def unload_game():
    global current_game
    if current_game.get_time_left() >0:
        print ("achtung achtung!")
    send_game_message("")
    print("finalized")
    winner = current_game.finalize()
    if winner != "":
        send_game_message(winner + " wins!")
    else:
        send_game_message("nobody wins...")
    load_game(copy.copy(choice(game_list)))

def load_game(game):
    global current_game
    socketio.emit('countdown', {'count': "3"},namespace="/test")
    time.sleep(1)
    socketio.emit('countdown', {'count': "2"},namespace="/test")
    time.sleep(1)
    socketio.emit('countdown', {'count': "1"},namespace="/test")
    time.sleep(1)
    current_game = game
    current_game.__init__()
    current_game.stime = time.time()
    send_game_message(current_game.get_data())
    print("loading "+current_game.game_id,current_game.get_time_left())
    socketio.emit('game id', {'id': current_game.game_id, 'message': current_game.message,'start_script':current_game.start_script,'finish_script':current_game.finish_script,'data':current_game.get_data()},namespace="/test")
    t = Timer(current_game.get_time_left(),unload_game)
    t.start()

def send_game_message(message):
    socketio.emit('game message', {'data': message},namespace="/test")

@socketio.on('get game id', namespace='/test')
def get_current_game(msg):
    global current_game

    #emit('game id',
    #     {'id': current_game.game_id,'param' : current_game.param})

@socketio.on('get game data', namespace='/test')
def get_game_data(msg):
    global current_game
    emit('game data',
         {'data': current_game.get_data(),'start_script':current_game.start_script,'finish_script':current_game.finish_script,'message':current_game.message,'time_left': current_game.get_time_left()})

@socketio.on('nic', namespace='/test')
def change_nic(message):
    usr = User(message['data'],0)
    if 'user' in session:
        del_user(session['user'])
    if add_user(usr):
        session['user']=usr

@socketio.on('game', namespace='/test')
def receive_game(message):
    current_game.user_input(current_user.nic, message)

@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    emit('my response',
         {'data': message['data']},
         broadcast=True)

@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms)})

@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms)})

@socketio.on('close room', namespace='/test')
def close(message):
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.'},
         room=message['room'])
    close_room(message['room'])

@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    emit('my response',
         {'data': message['data']},
         room=message['room'])

@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    emit('my response',
         {'data': 'Disconnected!'})
    disconnect()

@socketio.on('connect', namespace='/test')
def test_connect():
    add_user(current_user)
    #print "current_user = "+current_user.nic
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')
    print(session)
    if 'user' in session:
        emit('my response',
         {'data': session['user'].nic+" has left", 'count': session['receive_count']},
         broadcast=True)
        #del_user(session['user'])



def add_user(user):
    """
    Add a user.
    """
    #if user.nic in USERS:
    #    return False
    #else:
        #USERS[user.nic]=user
    #print(nic)
    join_room(user.nic)
    emit('user list', {'data': ",".join([k for k in USERS])},broadcast=True)
    return True

def del_user(user):
    """
    Delete a user.
    """
    if user.nic not in USERS:
        return False
    else:
        close_room(user.nic)
        del USERS[user.nic]
        emit('user list', {'data': ",".join([k for k in USERS])},broadcast=True)
        return True

