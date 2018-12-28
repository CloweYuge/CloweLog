import os
from clowelog.extensions import db
from flask import current_app
from flask_login import UserMixin
from flask_avatars import Identicon
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from clowelog.extensions import whooshee


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
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPHOTO'],        # 普通用户
            'Pouser': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPHOTO', 'UPPOST'],        # 博文用户
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPHOTO', 'UPPOST', 'MODERATE'],        # 协管理
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPPHOTO', 'UPPOST', 'MODERATE', 'ADMINISTER']   # 管理员
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


class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')


# relationship object
class Collect(db.Model):
    collector_id = db.Column(db.Integer, db.ForeignKey('user.id'),
                             primary_key=True)
    collected_id = db.Column(db.Integer, db.ForeignKey('blog.id'),
                             primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    collector = db.relationship('User', back_populates='collections', lazy='joined')
    collected = db.relationship('Blog', back_populates='collectors', lazy='joined')


user_category = db.Table('usercategory', db.Column('category_id', db.Integer, db.ForeignKey('category.id')),
                         db.Column('user_id', db.Integer, db.ForeignKey('user.id')))


@whooshee.register_model('name', 'username')
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
    avatar_raw = db.Column(db.String(64))               # 用户上传

    # blog_open = db.Column(db.Boolean, default=False)            # 博文开通状态
    confirmed = db.Column(db.Boolean, default=False)        # 确认注册状态
    locked = db.Column(db.Boolean, default=False)           # 锁定状态，只能关注和收藏，无法发布信息
    active = db.Column(db.Boolean, default=True)            # 封禁状态，不允许登陆

    public_collections = db.Column(db.Boolean, default=True)            # 公开收藏
    receive_comment_notification = db.Column(db.Boolean, default=True)      # 评论提醒
    receive_follow_notification = db.Column(db.Boolean, default=True)       # 关注提醒
    receive_collect_notification = db.Column(db.Boolean, default=True)      # 收藏提醒

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users', foreign_keys=[role_id])

    categorys = db.relationship('Category', back_populates='user', secondary=user_category)
    blog = db.relationship('Blog', back_populates='user')

    comments = db.relationship('Comment', back_populates='user', cascade='all')

    online = db.relationship('Useronline', back_populates='user', uselist=False)

    notifications = db.relationship('Notification', back_populates='receiver', cascade='all')
    collections = db.relationship('Collect', back_populates='collector', cascade='all')
    following = db.relationship('Follow', foreign_keys=[Follow.follower_id], back_populates='follower',
                                lazy='dynamic', cascade='all')
    followers = db.relationship('Follow', foreign_keys=[Follow.followed_id], back_populates='followed',
                                lazy='dynamic', cascade='all')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.generate_avatar()
        self.follow(self)  # follow self
        self.set_role()
        self.set_cateary()

    def set_cateary(self):
        category = Category.query.filter_by(id=1).first()
        category.user.append(self)
        db.session.commit()

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()

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

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:  # when follow self, user.id will be None
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_photos(self):
        return Blog.query.join(Follow, Follow.followed_id == Blog.user_id).filter(Follow.follower_id == self.id)

    def collect(self, photo):
        if not self.is_collecting(photo):
            collect = Collect(collector=self, collected=photo)
            db.session.add(collect)
            db.session.commit()

    def uncollect(self, photo):
        collect = Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def is_collecting(self, photo):
        return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first() is not None

    def lock(self):
        self.locked = True
        self.role = Role.query.filter_by(name='Locked').first()
        db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name='User').first()
        db.session.commit()

    def block(self):
        self.active = False
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()

    @property
    def is_admin(self):
        return self.role.name == 'Administrator'

    @property
    def is_active(self):
        return self.active

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions


@whooshee.register_model('name')
class Category(db.Model):
    '''
    分类数据模型
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)            # 将不允许重复参数设置为True

    blogs = db.relationship('Blog', back_populates='category')          # 标量关系属性，此为一对多关系
    user = db.relationship('User', back_populates='categorys', secondary=user_category)

    def delete(self):
        default_category = Category.query.get(1)
        texts = self.text[:]
        for text in texts:
            text.category = default_category
        db.session.delete(self)
        db.session.commit()


class Comment(db.Model):
    '''
    评论数据模型
    '''
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='comments', foreign_keys=[user_id])

    body = db.Column(db.Text)
    flag = db.Column(db.SmallInteger, default=0)       # 举报

    from_admin = db.Column(db.Boolean, default=False)   # 来自管理
    reviewed = db.Column(db.Boolean, default=False)     # 提醒
    remind = db.Column(db.Boolean, default=False)       # 已读

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)         # 设置index参数表示将以此字段建立索引

    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))  # 设置外键指向admin的id
    blog = db.relationship('Blog', back_populates='comments', foreign_keys=[blog_id])

    # 设置外键指向自身id值，
    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    # 当设置remote_side为id，表示无法区分多对一关系时，以id值为多的侧（远程侧），replied_id为一的侧（本地侧）
    # 设置replied为标量属性，对应的是replies属性，查询参数相应的设置为id值
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])
    # 设置replies标量属性，与replied对应，并设置级联操作
    replies = db.relationship('Comment', back_populates='replied', cascade='all, delete-orphan')


tagging = db.Table('tagging',
                   db.Column('blog_id', db.Integer, db.ForeignKey('blog.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                   )


@whooshee.register_model('description')
class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(250))  # 配文或者标题
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)     # 发表时间
    can_comment = db.Column(db.Boolean, default=True)       # 允许评论
    flag = db.Column(db.SmallInteger, default=0)                 # 举报数
    type = db.Column(db.SmallInteger, default=2)                 # 博文类型  video3 , photos2 , post1

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='blog', foreign_keys=[user_id])

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # 设置外键，储存分类相关信息
    category = db.relationship('Category', back_populates='blogs', foreign_keys=[category_id])  # 标量关系属性，此为多一侧，所以需要设置外键

    text = db.relationship('Text', back_populates='blog', uselist=False,  cascade='all')
    photos = db.relationship('Photo', back_populates='blog', cascade='all')
    video = db.relationship('Video', back_populates='blog', cascade='all')

    comments = db.relationship('Comment', back_populates='blog', cascade='all, delete-orphan')    # 设置了级联操作，也就是删除
    collectors = db.relationship('Collect', back_populates='collected', cascade='all')
    tags = db.relationship('Tag', secondary=tagging, back_populates='blogs')


@whooshee.register_model('body')
class Text(db.Model):
    '''
    文章数据模型，其外键指向Categroy模型中的id主键值
    '''
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)

    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    blog = db.relationship('Blog', back_populates='text', foreign_keys=[blog_id])


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64))  # 原图
    filename_s = db.Column(db.String(64))
    filename_m = db.Column(db.String(64))

    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    blog = db.relationship('Blog', back_populates='video', foreign_keys=[blog_id])


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(64))             # 原图
    filename_s = db.Column(db.String(64))
    filename_m = db.Column(db.String(64))
    type_photo = db.Column(db.String(1))

    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id'))
    blog = db.relationship('Blog', back_populates='photos', foreign_keys=[blog_id])


@whooshee.register_model('name')
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), index=True, unique=True)

    blogs = db.relationship('Blog', secondary=tagging, back_populates='tags')


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver = db.relationship('User', back_populates='notifications')


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    url = db.Column(db.String(255))


class Useronline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15), default='0.0.0.0')

    lasttime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    clike = db.Column(db.SmallInteger, default=1)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='online')

    def ip_required(self, value):
        if self.ip == value:
            return True
        else:
            return False

    @staticmethod
    def ifonline(user_id):
        '''
        会话时间验证，5分钟以内不得超过20次点击，每五分钟重新设置时间和点击次数，若超过30分钟则删除在线信息
        :param user_id: 用户id
        :return: 默认返回True，若超过点击次数则返回False
        '''
        user = User.query.get_or_404(user_id)
        online = Useronline.query.with_parent(user).one()
        if online is None:
            online = Useronline(user=user)
            db.session.add(online)
            db.session.commit()
            return True
        lasttimp = time.mktime(online.lasttime)
        now = datetime.utcnow()
        minute = (now - lasttimp).minute
        if minute >= 5:
            online.lasttime = datetime.utcnow()
            online.clike = 1
        elif minute < 5:
            if online.clike == 20:
                return False
            online.clike += 1
        else:
            online.delete()
        db.session.commit()
        return True

    @staticmethod
    def deleteonline():
        now = datetime.utcnow()
        delta = timedelta(minutes=30)
        minute = now - delta
        user = Useronline.query.filter(Useronline.lasttime < minute).all()
        user.delete()
        db.session.commit()


@db.event.listens_for(User, 'after_delete', named=True)
def delete_avatars(**kwargs):
    target = kwargs['target']
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:  # 如果头像路径不存在的话
            path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
            if os.path.exists(path):  # 如果该文件存在
                os.remove(path)


@db.event.listens_for(Blog, 'after_delete', named=True)
def delete_photos(**kwargs):
    target = kwargs['target']
    for photo in target.photos:
        for filename in [photo.filename, photo.filename_s, photo.filename_m]:
            path = os.path.join(current_app.config['CLOWELOG_UPLOAD_PATH'], filename)
            if os.path.exists(path):  # not every filename map a unique file
                os.remove(path)
