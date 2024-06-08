from flask import Flask
from flask_login import LoginManager
from social_wave import config
import cloudinary
import cloudinary.uploader
import cloudinary.api


UPLOAD_FOLDER = 'social_wave/static/uploads'
app = Flask(__name__)

app.config['SECRET_KEY'] = 'a6b43a461a7231ee71ce4f7be308b6a0'

app.app_context().push()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Cloudinary Configuration
cloudinary.config(
    cloud_name=config.CLOUDINARY_URL.split('@')[1],
    api_key=config.CLOUDINARY_URL.split(':')[1][2:],
    api_secret=config.CLOUDINARY_URL.split(':')[2].split('@')[0]
)


from social_wave import routes
