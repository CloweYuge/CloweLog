from clowelog.extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


admin_category = db.Table('admincategory', db.Column('category_id', db.Integer, db.ForeignKey('category.id')),
                          db.Column('admin_id', db.Integer, db.ForeignKey('admin.id')))


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # username = db.Column(db.String(20))
    # password_hash = db.Column(db.String(128))
    blog_title = db.Column(db.String(60))
    blog_sub_title = db.Column(db.String(100))
    blog_theme = db.Column(db.String(20))
    about = db.Column(db.Text)  # 说明
    # name = db.Column(db.String(30))  # 站点标题
    # about = db.Column(db.Text)
    # category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    categorys = db.relationship('Category', back_populates='admin', secondary=admin_category)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='admin', foreign_keys=[user_id])

    posts = db.relationship('Post', back_populates='admin')
    comments = db.relationship('Comment', back_populates='admin', lazy='dynamic')
    # def set_password(self, password):
    #     self.password_hash = generate_password_hash(password)
    #
    # def validate_password(self, password):
    #     return check_password_hash(self.password_hash, password)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(20))                     # 登录名
    password_hash = db.Column(db.String(128))               # 密码
    name = db.Column(db.String(20))                         # 昵称

    email = db.Column(db.String(254))                       # 邮件
    site = db.Column(db.String(255))                        # 主页

    admin = db.relationship('Admin', back_populates='user', uselist=False)
    comments = db.relationship('Comment', back_populates='user')

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
