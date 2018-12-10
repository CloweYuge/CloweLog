import os
import click
from flask import Flask, render_template
from flask_wtf.csrf import CSRFError
from flask_login import current_user

from clowelog.blueprints.auth import auth_bp
from clowelog.blueprints.admin import admin_bp
from clowelog.blueprints.blog import blog_bp
from clowelog.blueprints.user import user_bp
from clowelog.extensions import bootstrap, db, moment, ckeditor, mail, login_manager, csrf
from clowelog.settings import config
from clowelog.models import Admin, Category, Comment, User


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')# 首先查找环境变量，虚拟环境变量在.flaskenv中配置，未找到即使用development为默认

    app = Flask('clowelog')
    app.config.from_object(config[config_name])  # config字典中储存了类对象，由键值获取不同部署环境下的配置类

    register_logging(app)
    register_blueprint(app)
    register_extensions(app)
    register_shell_context(app)
    register_template_context(app)
    register_errors(app)
    register_commands(app)

    return app

def register_logging(app):
    pass

def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    ckeditor.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

def register_blueprint(app):
    app.register_blueprint(blog_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db)

def register_template_context(app):
    @app.context_processor
    def make_template_context():
        admin = Admin.query.first()
        categories = Category.query.order_by(Category.name).all()
        if current_user.is_authenticated:
            admin_user = User.query.get(current_user.id).admin
            if admin_user:
                categorys = admin_user.categorys
                unread_comments = admin_user.comments.filter_by(reviewed=False).count()
            else:
                categorys = None
                unread_comments = None
        else:
            admin_user = None
            categorys = None
            unread_comments = None
        return dict(unread_comments=unread_comments, admin=admin, categories=categories,
                    admin_user=admin_user, categorie_user=categorys)


def register_errors(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 400

def register_commands(app):
    @app.cli.command()
    @click.option('--category', default=10, help='Quantity of categories, default is 10.')
    @click.option('--post', default=50, help='Quantity of posts, default is 50.')
    @click.option('--comment', default=500, help='Quantity of comments, default is 500.')
    def forge(category, post, comment):
        """配置网站虚拟数据，和管理员账户，默认admin-root，密码helloflask"""
        from clowelog.fakes import fake_admin, fake_categories, fake_posts, fake_comments, fake_user

        db.drop_all()
        db.create_all()

        click.echo('生成用户信息')
        fake_user()

        click.echo('生成管理员（Generating the administrator...）')
        fake_admin()

        click.echo('生成分类信息（Generating %d categories...）' % category)
        fake_categories(category)

        click.echo('生成文章（Generating %d posts...）' % post)
        fake_posts(post)

        click.echo('生成评论（Generating %d comments...）' % comment)
        fake_comments(comment)

        click.echo('完成（Done.）')


    @app.cli.command()
    @click.option('--username', prompt=True, help='The username used to login.')
    @click.option('--password', prompt=True, hide_input=True,
                  confirmation_prompt=True, help='The password used to login.')
    def init(username, password):
        """只生成管理员账号(--username 登录名，--password 密码)，并添加默认分类，入已存在管理账号将会更新已存在的。"""

        click.echo('Initializing the database...')
        db.create_all()

        admin = Admin.query.first()
        if admin is not None:
            click.echo('The administrator already exists, updating...')
            admin.username = username
            admin.set_password(password)
        else:
            click.echo('Creating the temporary administrator account...')
            admin = Admin(
                username=username,
                blog_title='Clowelog',
                blog_sub_title="No, I'm the real thing.",
                name='Admin',
                about='Anything about you.'
            )
            admin.set_password(password)
            db.session.add(admin)

        category = Category.query.first()
        if category is None:
            click.echo('生成默认分类（Creating the default category...）')
            category = Category(name='默认')
            db.session.add(category)

        db.session.commit()
        click.echo('完成Done.')