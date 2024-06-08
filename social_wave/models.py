from bson import ObjectId
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from social_wave import login_manager


@login_manager.user_loader
def load_user(username):
    from social_wave.db import get_user_by_username
    return get_user_by_username(username)


class User(UserMixin):

    def __init__(self, username, email, password, phone, dob, gender, status, profile_pic):
        self.username = username
        self.email = email
        self.password = password
        self.phone = phone
        self.dob = dob
        self.gender = gender
        self.status = status
        self.profile_pic = profile_pic

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active(self):
        return True

    @staticmethod
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def check_password(self, password_input):
        return check_password_hash(self.password, password_input)


class Post:
    def __init__(self, id, author, caption, image, createdAt, likes, comments):
        self.id = id
        self.author = author
        self.caption = caption
        self.image = image
        self.createdAt = createdAt
        self.likes = likes
        self.comments = comments

    def get_id(self):
        return self.author


class Follow:
    def __init__(self, username, follower, following):
        self.username = username
        self.follower = follower
        self.following = following

    def get_id(self):
        return self.username
