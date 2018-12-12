from clowelog.extensions import db
from flask import current_app
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from clowelog import settings

admin_category = db.Table('admincategory', db.Column('category_id', db.Integer, db.ForeignKey('category.id')),
                          db.Column('admin_id', db.Integer, db.ForeignKey('admin.id')))


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    blog_title = db.Column(db.String(60))
    blog_sub_title = db.Column(db.String(100))
    blog_theme = db.Column(db.String(20))
    about = db.Column(db.Text)  # 说明

    categorys = db.relationship('Category', back_populates='admin', secondary=admin_category)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 开通时间

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='admin', foreign_keys=[user_id])

    posts = db.relationship('Post', back_populates='admin')
    comments = db.relationship('Comment', back_populates='admin', lazy='dynamic')

# 权限与角色关联表
roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
                             )


class Permission(db.Model):        # 权限
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions')


class Role(db.Model):               # 角色
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    users = db.relationship('User', back_populates='role')
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles')

    @staticmethod
    def init_role():
        roles_permissions_map = {
            'Locked': ['FOLLOW', 'COLLECT'],    # 锁定用户
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPOST'],         # 普通用户
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPOST', 'MODERATE'],        # 协管理
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPOST', 'MODERATE', 'ADMINISTER']   # 管理员
        }

        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
        db.session.commit()



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))                                     # 昵称
    username = db.Column(db.String(20), unique=True, index=True)         # 登录名

    email = db.Column(db.String(254), unique=True, index=True)            # 邮件
    password_hash = db.Column(db.String(128))                   # 密码
    site = db.Column(db.String(255))                            # 主页
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 注册时间

    bio = db.Column(db.String(120))                         # 个人简介
    location = db.Column(db.String(50))                     # 所在地

    avatar_s = db.Column(db.String(64))                     # 头像
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    avatar_raw = db.Column(db.String(64))

    admin_root = db.Column(db.Boolean, default=False)       # 超级管理员状态
    confirmed = db.Column(db.Boolean, default=True)        # 确认注册状态
    locked = db.Column(db.Boolean, default=False)           # 封禁状态
    active = db.Column(db.Boolean, default=True)            # 活跃状态

    # public_collections = db.Column(db.Boolean, default=True)
    # receive_comment_notification = db.Column(db.Boolean, default=True)
    # receive_follow_notification = db.Column(db.Boolean, default=True)
    # receive_collect_notification = db.Column(db.Boolean, default=True)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

    role = db.relationship('Role', back_populates='users', foreign_keys=[role_id])
    admin = db.relationship('Admin', back_populates='user', uselist=False)
    comments = db.relationship('Comment', back_populates='user')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # self.generate_avatar()
        # self.follow(self)  # follow self
        self.set_role()

    def set_role(self):
        if self.role is None:
            if self.username == current_app.config['ADMIN_ROOT'].get('username'):
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
            db.session.commit()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)

    def open_admin(self):
        admin = Admin(
            blog_title=settings.ADMIN_USER.get('blog_title'),
            blog_sub_title=settings.ADMIN_USER.get('blog_sub_title'),
            about=settings.ADMIN_USER.get('about')
        )
        admin.user = self
        db.session.add(admin)
        db.session.commit()

    @property
    def is_admin(self):
        return self.role.name == 'Administrator'

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions


class Category(db.Model):
    '''
    分类数据模型
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)            # 将不允许重复参数设置为True
    posts = db.relationship('Post', back_populates='category')          # 标量关系属性，此为一对多关系

    # admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    admin = db.relationship('Admin', back_populates='categorys', secondary=admin_category)

    def delete(self):
        default_category = Category.query.get(1)
        posts = self.posts[:]
        for post in posts:
            post.category = default_category
        db.session.delete(self)
        db.session.commit()


class Post(db.Model):
    '''
    文章数据模型，其外键指向Categroy模型中的id主键值
    '''
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    can_comment = db.Column(db.Boolean, default=True)

    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    admin = db.relationship('Admin', back_populates='posts', foreign_keys=[admin_id])

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))   # 设置外键，当查询时以此查找对应数据
    category = db.relationship('Category', back_populates='posts', foreign_keys=[category_id])      # 标量关系属性，此为多一侧，所以需要设置外键
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')    # 设置了级联操作，也就是删除

class Comment(db.Model):
    '''
    评论数据模型
    '''
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String(30))
    # email = db.Column(db.String(254))
    # site = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='comments', foreign_keys=[user_id])

    body = db.Column(db.Text)
    from_admin = db.Column(db.Boolean, default=False)
    reviewed = db.Column(db.Boolean, default=False)
    remind = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)         # 设置index参数表示将以此字段建立索引

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))           # 设置外键指向post的id
    post = db.relationship('Post', back_populates='comments', foreign_keys=[post_id])

    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 设置外键指向admin的id
    admin = db.relationship('Admin', back_populates='comments', foreign_keys=[admin_id])

    # 设置外键指向自身id值，
    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    # 当设置remote_side为id，表示无法区分多对一关系时，以id值为多的侧（远程侧），replied_id为一的侧（本地侧）
    # 设置replied为标量属性，对应的是replies属性，查询参数相应的设置为id值
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])
    # 设置replies标量属性，与replied对应，并设置级联操作
    replies = db.relationship('Comment', back_populates='replied', cascade='all, delete-orphan')


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    url = db.Column(db.String(255))
