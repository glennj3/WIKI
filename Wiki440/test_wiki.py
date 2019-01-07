

import pytest
from wiki.web.user import *
import Riki
import os
from flask import Flask

from config import UPLOAD_FOLDER, USER_DIR, ALLOWED_EXTENSIONS

@pytest.fixture
def client():

    Riki.app.config['TESTING'] = True
    client = Riki.app.test_client()

    yield client

def test_allowedFile(client):
    assert allowed_file('pass.txt') == True
    assert allowed_file('fail.bleb') == False

def test_addUser(client):
    app = Flask(__name__)
    with app.app_context():
        #Making a mock user
        username = "TestUser"
        password = "TestPassword"
        #Adding mock user to database
        UserManager(USER_DIR).add_user(username, password)
        #retrieving mockuser by username
        mockuser = UserManager(USER_DIR).get_user(username)
        #Testing to see if retrieved mockuser has same name and password that we started with
        assert username == mockuser.get_id()
        assert mockuser.check_password(password) == True
        #Deleting our mockuser to preserve memory of Json file
        UserManager(USER_DIR).delete_user(username)


def test_profileedit(client):
    assert client.get('/profile/edit').status_code == 302

def test_profile(client):
    assert client.get('/profile/').status_code == 302

def test_profileUser(client):
    assert client.get('/profile/<string:username>').status_code == 302

def test_register(client):
    assert client.get('/register/').status_code == 200


def test_upload(client):
    assert client.get('/upload/').status_code == 302


def test_uploadFile(client):
    assert client.get('/uploads/<path:filename>').status_code == 302

def test_upload_file(client):
    os.chdir(UPLOAD_FOLDER)
    file = open("file.txt", "w")
    file.write("TEST")
    file.close()
    fd = os.open(UPLOAD_FOLDER + "/file.txt", os.O_RDONLY)
    text = os.read(fd, 14)
    os.close(fd)
    assert True == os.path.isfile(UPLOAD_FOLDER + '/file.txt')
    assert b'TEST' == text
    os.remove(UPLOAD_FOLDER + "/file.txt")


def test_downloads(client):
    assert client.get('/downloads/').status_code == 302