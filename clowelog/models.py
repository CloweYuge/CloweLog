from clowelog.extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    blog_title = db.Column(db.String(60))
    blog_sub_title = db.Column(db.String(100))
    name = db.Column(db.String(30))
    about = db.Column(db.Text)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(30))
    about = db.Column(db.Text)
    email = db.Column(db.String(254))
    site = db.Column(db.String(255))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    '''
    分类数据模型
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)            # 将不允许重复参数设置为True
    posts = db.relationship('Post', back_populates='category')          # 标量关系属性，此为一对多关系

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
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))   # 设置外键，当查询时以此查找对应数据
    category = db.relationship('Category', back_populates='posts')      # 标量关系属性，此为多一侧，所以需要设置外键
    comments = db.relationship('Comment', back_populates='post', cascade='all, delete-orphan')    # 设置了级联操作，也就是删除

class Comment(db.Model):
    '''
    评论数据模型
    '''
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(30))
    email = db.Column(db.String(254))
    site = db.Column(db.String(255))
    body = db.Column(db.Text)
    from_admin = db.Column(db.Boolean, default=False)
    reviewed = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)         # 设置index参数表示将以此字段为排序
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))           # 设置外键指向post的id
    post = db.relationship('Post', back_populates='comments')

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
