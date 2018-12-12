from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_ckeditor import CKEditor
from flask_moment import Moment
from flask_login import LoginManager, AnonymousUserMixin
from flask_wtf import CSRFProtect

bootstrap = Bootstrap()
db = SQLAlchemy()
moment = Moment()
ckeditor = CKEditor()
mail = Mail()
login_manager = LoginManager()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
login_manager.login_message = '请先登录！(Please log in to access this page.)'


@login_manager.user_loader
def load_user(user_id):
    from clowelog.models import User
    user = User.query.get(int(user_id))
    return user


class Guest(AnonymousUserMixin):    # 访客拥有的类与权限，默认全部为False

    def can(self, permission_name):
        return False

    @property
    def is_admin(self):
        return False

login_manager.anonymous_user = Guest
