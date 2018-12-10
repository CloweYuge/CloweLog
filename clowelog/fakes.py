from faker import Faker
from clowelog.models import Admin, Category, Post, Comment, User
from clowelog.extensions import db
from sqlalchemy.exc import IntegrityError
from random import randint

fake = Faker()


def fake_admin():
    admin = Admin(
        blog_title='CloweLog',
        blog_sub_title="欢迎来到clowe的博文站。",
        about='Um, l, you ,love me',
        user=User.query.get(1)
    )

    db.session.add(admin)
    db.session.commit()


def fake_user(count=5):
    user = User(username='admin-root', name='Clowe')
    user.set_password('helloflask')
    db.session.add(user)
    for i in range(count):
        user = User(
            username=fake.name(),
        )
        user.name = user.username
        user.set_password(user.name)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_categories(count=5):
    category = Category(name='默认')
    category.admin = Admin.query.all()
    db.session.add(category)

    for i in range(count):
        category = Category(
            name=fake.word(),
        )
        category.admin = Admin.query.all()
        db.session.add(category)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_posts(count=10):
    for i in range(count):
        post = Post(
            title=fake.sentence(),
            body=fake.text(2000),
            category=Category.query.get(randint(1, Category.query.count())),
            timestamp=fake.date_time_this_year(),
            admin=Admin.query.first()
        )
        db.session.add(post)
    db.session.commit()


def fake_comments(count=50):
    for i in range(count):
        comment = Comment(
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            reviewed=True,
            admin=Admin.query.first(),
            post=Post.query.get(randint(1, Post.query.count())),
            user=User.query.get(randint(1, User.query.count()))
        )
        db.session.add(comment)

    salt = int(count * 0.1)
    for i in range(salt):
        # 未审核的评论
        comment = Comment(
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            reviewed=False,
            admin=Admin.query.first(),
            post=Post.query.get(randint(1, Post.query.count())),
            user=User.query.get(randint(1, User.query.count()))
        )
        db.session.add(comment)

        # 管理员发表的评论
        comment = Comment(
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            admin=Admin.query.first(),
            user=User.query.get(1),
            from_admin=True,
            reviewed=True,
            post=Post.query.get(randint(1, Post.query.count()))
        )
        db.session.add(comment)
    db.session.commit()

    # 回复
    for i in range(salt):
        comment = Comment(
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            admin=Admin.query.first(),
            user=User.query.get(randint(1, User.query.count())),
            reviewed=True,
            replied=Comment.query.get(randint(1, Comment.query.count())),
            post=Post.query.get(randint(1, Post.query.count()))
        )
        db.session.add(comment)
    db.session.commit()