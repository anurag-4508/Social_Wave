import secrets
from datetime import datetime, timedelta
# from PIL import Image
from flask import request, redirect, url_for, render_template, flash, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from social_wave import app
from social_wave.db import save_user, user_collection, get_user_by_email, get_user_by_username, save_post, \
    get_posts, get_posts_by_username, follow_someone, get_follower_count, get_following_count, is_following, \
    unfollow_someone, like_post, unlike_post
import os
from social_wave import config
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Cloudinary Configuration
cloudinary.config(
    cloud_name=config.CLOUDINARY_URL.split('@')[1],
    api_key=config.CLOUDINARY_URL.split(':')[1][2:],
    api_secret=config.CLOUDINARY_URL.split(':')[2].split('@')[0]
)


@app.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        input_username = request.form.get('username')
        input_email = request.form.get('email')
        input_password = request.form.get('password')

        user_found = user_collection.find_one({"username": input_username})
        email_found = user_collection.find_one({"email": input_email})

        if user_found:
            flash(f"Username already taken. Try different username ", "info")
            return render_template('authenticate.html')

        if email_found:
            flash(f"Email already associated with a account. Try different username or email ", "info")
            return render_template('authenticate.html')
        else:
            save_user(username=input_username, password=input_password, email=input_email)
            flash(f"User registered successfully ", "success")
            return redirect(url_for('login'))

    return render_template('authenticate.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        input_email = request.form.get('email')
        input_password = request.form.get('password')

        user = get_user_by_email(email=input_email)

        if user and user.check_password(input_password):
            flash(f"Welcome {user.username}", "success")
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash(f"Failed", "success")
            return redirect(url_for('auth'))

    return render_template('authenticate.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/auth')
def auth():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    return render_template('authenticate.html')


def calculate_time_difference(post_timestamp):
    current_time = datetime.now()
    time_difference = current_time - post_timestamp
    return time_difference


def format_time_difference(time_difference):
    if time_difference < timedelta(minutes=1):
        return "just now"
    elif time_difference < timedelta(hours=1):
        minutes = int(time_difference.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif time_difference < timedelta(days=1):
        hours = int(time_difference.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif time_difference < timedelta(weeks=1):
        days = time_difference.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    elif time_difference < timedelta(weeks=4):
        weeks = int(time_difference.days / 7)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        return "more than a month ago"


@app.route('/home')
@app.route('/')
def home():
    all_posts = get_posts()
    print(all_posts)

    for post in all_posts:
        post_timestamp = post.createdAt
        time_difference = calculate_time_difference(post_timestamp)
        formatted_time = format_time_difference(time_difference)

        post.createdAt = formatted_time

    return render_template('home.html', all_posts=all_posts)


# def save_profile_picture(form_picture):
#     random_hex = secrets.token_hex(8)
#     _, f_ext = os.path.splitext(form_picture.filename)
#     picture_fn = random_hex + f_ext
#     picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
#
#     output_size = (200, 200)
#     i = Image.open(form_picture)
#     i.thumbnail(output_size)
#     i.save(picture_path)
#
#     return picture_fn


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    image_file = current_user.profile_pic
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        status = request.form.get('status')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        profile_pic = request.files['image']

        if not username or not email or not phone or not status or not gender or not dob:
            flash('Please fill all the fields, before proceeding', 'info')
            return render_template('account.html', image_file=image_file)

        if username != current_user.username:
            flash('Username cannot be changed', 'info')
            return render_template('account.html', image_file=image_file)

        if email != current_user.email:
            flash('Email cannot be changed', 'info')
            return render_template('account.html', image_file=image_file)

        if not profile_pic:
            user_collection.update_one({'username': current_user.username}, {'$set': {'username': username,
                                                                                      'email': email,
                                                                                      'phone': phone,
                                                                                      'status': status,
                                                                                      'gender': gender,
                                                                                      'dob': dob}})
        else:
            upload_profile_pic = cloudinary.uploader.upload(profile_pic)
            profile_pic_url = upload_profile_pic.get('url')

            # picture_file = save_profile_picture(profile_pic)
            user_collection.update_one({'username': current_user.username}, {'$set': {'username': username,
                                                                                      'email': email,
                                                                                      'phone': phone,
                                                                                      'status': status,
                                                                                      'gender': gender,
                                                                                      'dob': dob,
                                                                                      'profile_pic': profile_pic_url}})

        flash(f"Account details updated successfully", "success")
        return render_template('account.html', image_file=image_file)

    return render_template('account.html', image_file=current_user.profile_pic)


@app.route('/user/<string:username>')
@login_required
def profile(username):
    user = get_user_by_username(username)

    posts = get_posts_by_username(username=username)

    for post in posts:
        post_timestamp = post.createdAt
        time_difference = calculate_time_difference(post_timestamp)
        formatted_time = format_time_difference(time_difference)

        post.createdAt = formatted_time

    # image_file = url_for('static', filename='profile_pics/' + user.profile_pic)
    followers_count = get_follower_count(username)
    following_count = get_following_count(username)
    is_follow = is_following(current_user.username, username)

    return render_template('profile_page.html', image_file=user.profile_pic, user=user,
                           posts=posts, followers_count=followers_count, following_count=following_count
                           , is_following=is_follow)


# def save_post_picture(form_picture):
#     random_hex = secrets.token_hex(8)
#     _, f_ext = os.path.splitext(form_picture.filename)
#     picture_fn = random_hex + f_ext
#     picture_path = os.path.join(app.root_path, 'static/post_pics', picture_fn)
#
#     output_size = (500, 500)
#     i = Image.open(form_picture)
#     i.thumbnail(output_size)
#     i.save(picture_path)
#
#     return picture_fn


@app.route('/create_post', methods=['POST'])
@login_required
def create_post():
    if request.method == 'POST':
        caption = request.form.get('caption')
        image = request.files['image']

        # picture_file = save_post_picture(image)

        upload_image = cloudinary.uploader.upload(image)
        image_url = upload_image.get('url')

        # Save to MongoDB
        # photo_record = {"url": url}
        # photos.insert_one(photo_record)

        save_post(author=current_user.username, caption=caption, image=image_url)
        flash('Post published successfully', 'success')
        return redirect(f'/user/{current_user.username}')
    else:
        flash('Some error occurred', 'danger')
        return redirect('home')


@app.route('/follow/<string:other_user>', methods=['POST'])
@login_required
def follow(other_user):
    try:
        follow_someone(current_user.username, other_user)
        flash(f'You are now following {other_user}', 'info')
        return redirect(f'/user/{other_user}')
    except:
        flash('Some error occurred. Try again', 'danger')


@app.route('/unfollow/<string:other_user>', methods=['POST'])
@login_required
def unfollow(other_user):
    try:
        unfollow_someone(current_user.username, other_user)
        flash(f'You have unfollowed {other_user}', 'info')
        return redirect(f'/user/{other_user}')
    except:
        flash('Some error occurred. Try again', 'danger')


@app.route("/search", methods=["GET"])
def search_users():
    search_query = request.args.get("username")
    if search_query:
        # Use a MongoDB query to find matching users
        # In this example, we perform a case-insensitive search
        matching_users = list(
            user_collection.find(
                {"username": {"$regex": search_query, "$options": "i"}}
            )
        )
        return jsonify(users=[user["username"] for user in matching_users],
                       profile_pics=[user["profile_pic"] for user in matching_users])
    else:
        return jsonify(users=[], profile_pics=[])


@app.route('/like/<post_author>/<post_id>', methods=["POST"])
@login_required
def like_single_post(post_author, post_id):
    if like_post(current_user.username, post_id):
        flash('You liked the post', 'success')
        return redirect(f'/user/{post_author}')
    else:
        flash('Some error occurred. Please like again', 'danger')
        return redirect(f'/user/{post_author}')


@app.route('/unlike/<post_author>/<post_id>', methods=["POST"])
@login_required
def unlike_single_post(post_author, post_id):
    if unlike_post(current_user.username, post_id):
        flash('You unliked the post', 'success')
        return redirect(f'/user/{post_author}')
    else:
        flash('Some error occurred. Please unlike again', 'danger')
        return redirect(f'/user/{post_author}')
