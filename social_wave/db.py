from datetime import datetime
from bson import ObjectId
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from social_wave.models import User, Post, Follow
from social_wave import config


client = MongoClient(config.MONGODB_URI)

SocialWaveDb = client.get_database('SocialWaveDb')
user_collection = SocialWaveDb.get_collection('users')
post_collection = SocialWaveDb.get_collection('posts')
follow_collection = SocialWaveDb.get_collection('follows')


def save_user(username, email, password):
    password_hash = generate_password_hash(password)
    default_value = 'not updated yet'

    user_collection.insert_one(
        {'username': username, 'email': email, 'password': password_hash, 'phone': default_value
            , 'dob': default_value, 'gender': default_value, 'status': 'Doing good', 'profile_pic': 'default.png'
         })

    followers = []
    following = []

    follow_collection.insert_one(
        {'username': username, 'followers': followers, 'following': following
         })


def get_user(user_id):
    user_data = user_collection.find_one({'_id': ObjectId(user_id)})
    return User(user_data['username'], user_data['email'], user_data['password'], user_data['phone']
                , user_data['dob'], user_data['gender'], user_data['status'],
                user_data['profile_pic']) if user_data else None


def get_user_by_email(email):
    user_data = user_collection.find_one({'email': email})
    return User(user_data['username'], user_data['email'], user_data['password'], user_data['phone']
                , user_data['dob'], user_data['gender'], user_data['status'],
                user_data['profile_pic']) if user_data else None


def get_user_by_username(username):
    user_data = user_collection.find_one({'username': username})
    return User(user_data['username'], user_data['email'], user_data['password'], user_data['phone']
                , user_data['dob'], user_data['gender'], user_data['status'],
                user_data['profile_pic']) if user_data else None


def save_post(author, caption, image):
    default_value = '0'
    likes = []
    createdAt = datetime.now()
    comments = [
        {
            'author': author,
            'comment': caption,
            'c_time': createdAt
        }
    ]

    post_collection.insert_one(
        {'author': author, 'caption': caption, 'image': image, 'createdAt': createdAt
            , 'likes': likes, 'comments': comments
         })


def get_posts():
    post_data = post_collection.find().sort('createdAt', -1)
    posts = []
    for post in post_data:
        posts.append(Post(
            post['_id'],
            post['author'],
            post['caption'],
            post['image'],
            post['createdAt'],  # Corrected field name
            len(post['likes']),
            post['comments']
        ))

    return posts


def get_posts_by_username(username):
    post_data = post_collection.find({'author': username}).sort('createdAt', -1)
    posts = []
    for post in post_data:
        posts.append(Post(
            post['_id'],
            post['author'],
            post['caption'],
            post['image'],
            post['createdAt'],  # Corrected field name
            len(post['likes']),
            post['comments']
        ))
    return posts


def get_single_post(user_id):
    post_data = post_collection.find_one({'_id': user_id})
    return Post(
        post_data['_id'],
        post_data['author'],
        post_data['caption'],
        post_data['image'],
        post_data['createdAt'],  # Corrected field name
        len(post_data['likes']),
        post_data['comments']
    ) if post_data else None


def like_post(your_username, post_id):
    try:
        post_collection.update_one({'_id': ObjectId(post_id)},
                                   {'$push': {'likes': your_username}})
        return True
    except:
        return False


def unlike_post(your_username, post_id):
    try:
        post_collection.update_one({'_id': ObjectId(post_id)},
                                   {'$pull': {'likes': your_username}})
        return True
    except:
        return False


def is_liked(your_username, post_id):
    post = post_collection.find_one({'_id': post_id})
    for user in post["likes"]:
        if user == your_username:
            return True

    return False


def get_follower_count(username):
    follow_data = follow_collection.find_one({'username': username})
    followers_count = len(follow_data['followers'])

    return followers_count


def get_following_count(username):
    follow_data = follow_collection.find_one({'username': username})
    following_count = len(follow_data['following'])

    return following_count


def get_followers_list(username):
    follow_data = follow_collection.find_one({'username': username})

    return Follow(
        follow_data['username'],
        follow_data['follower'],
        follow_data['following']
    ) if follow_data else None


def follow_someone(your_username, others_username):
    follow_collection.update_one({'username': your_username},
                                 {'$push': {'following': others_username}})

    follow_collection.update_one({'username': others_username},
                                 {'$push': {'followers': your_username}})


def unfollow_someone(your_username, others_username):
    follow_collection.update_one({'username': your_username},
                                 {'$pull': {'following': others_username}})

    follow_collection.update_one({'username': others_username},
                                 {'$pull': {'followers': your_username}})


def is_following(your_username, others_username):
    follow_data = follow_collection.find_one({'username': your_username})
    for follower in follow_data['following']:
        if follower == others_username:
            return True

    return False
