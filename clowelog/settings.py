import os
import sys

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))       # 程序运行根目录

# SQLite 数据库在win系统中的路径，已经更换为MYSQL数据库
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class Operations:
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class BaseConfig(object):           # 公共的配置，在任何环境都有效
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev key')    # 加密字符串，写在环境变量中，保证安全

    BLOG_ABOUT = {
        'blog_title': '的博客站',
        'blog_sub_title': '的博客介绍',
        'about': '<p>非常感谢访问本站<br>'
                 '如果还未注册的话，仅可以浏览<br>'
                 '注册之后，首先你会拥有基本的发布图片的权限<br>'
                 '邮箱验证还未开启，需要激活请联系管理员<br>'
                 '同时，你可以向管理员申请开通发布文章的权限<br>'
                 '本站目前还在测试之中，若有BUG可以联系管理员！！！</p>'
    }

    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')              # 邮箱
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Bluelog Admin', MAIL_USERNAME)
    CLOWELOG_MAIL_SUBJECT_PREFIX = os.getenv('CLOWELOG_EMAIL')

    CLOWELOG_BLOG_PER_PAGE = 9
    CLOWELOG_PHOTO_PER_PAGE = 9
    CLOWELOG_COMMENT_PER_PAGE = 15
    CLOWELOG_NOTIFICATION_PER_PAGE = 10
    CLOWELOG_USER_PER_PAGE = 9

    CLOWELOG_MANAGE_USER_PER_PAGE = 15
    # CLOWELOG_MANAGE_PHOTO_PER_PAGE = 15
    CLOWELOG_MANAGE_TAG_PER_PAGE = 15
    CLOWELOG_MANAGE_COMMENT_PER_PAGE = 15
    CLOWELOG_MANAGE_BLOG_PER_PAGE = 15
    CLOWELOG_SEARCH_RESULT_PER_PAGE = 12

    # ('theme name', 'display name')
    BLUELOG_THEMES = {'perfect_blue': 'Perfect Blue', 'black_swan': 'Black Swan'}
    BLUELOG_SLOW_QUERY_THRESHOLD = 1
    ADMIN_ROOT = {
        'username': 'admin-root',
        'password': 'helloflask',
        'name': 'clowe'
    }
    CLOWELOG_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    CLOWELOG_PHOTO_SIZE = {'small': 400,
                         'medium': 800}
    CLOWELOG_PHOTO_SUFFIX = {
        CLOWELOG_PHOTO_SIZE['small']: '_s',  # thumbnail
        CLOWELOG_PHOTO_SIZE['medium']: '_m',  # display
    }

    DROPZONE_SERVE_LOCAL = True
    DROPZONE_ALLOWED_FILE_CUSTOM = True        # 允许自定义类型文件
    DROPZONE_ALLOWED_FILE_TYPE = 'image/*, video/*'
    DROPZONE_MAX_FILE_SIZE = 15             # 文件体积
    DROPZONE_MAX_FILES = 9                 # 单次上传最大数量
    DROPZONE_ENABLE_CSRF = True
    DROPZONE_REDIRECT_VIEW = 'main.upload_edit'
    DROPZONE_UPLOAD_MULTIPLE = True      # 是否在一个请求中发送多个文件。
    DROPZONE_PARALLEL_UPLOADS = 9        # 有多少上传会在处理时，每个请求到。DROPZONE_UPLOAD_MULTIPLE setTrue
    DROPZONE_DEFAULT_MESSAGE = "拖动文件或点击上传，jpg或png格式文件"

    WHOOSHEE_MIN_STRING_LEN = 1

    BOOTSTRAP_SERVE_LOCAL = True

    MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 服务器允许的最大值，超出返回413错误

    AVATARS_SAVE_PATH = os.path.join(CLOWELOG_UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)


class DevelopmentConfig(BaseConfig):
    # SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data-dev.db')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost:3306/clowelog?charset=utf8'


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # in-memory database


class ProductionConfig(BaseConfig):     # 生产环境的配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))    # 生产环境的数据库
    # ADMIN_ROOT = {
    #     'username': '',
    #     'password': '',
    #     'name': ''
    # }


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

