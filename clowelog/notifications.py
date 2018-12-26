from flask import url_for

from clowelog.extensions import db
from clowelog.models import Notification


def push_follow_notification(follower, receiver):
    message = '用户 <a href="%s">%s</a> 关注了你.' % \
              (url_for('user.index', username=follower.username), follower.username)
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_comment_notification(blog_id, receiver, page=1):
    message = '<a href="%s#comments">分享</a> 有了新的评论/回复.' % \
              (url_for('blog.show_photo', blog_id=blog_id, page=page))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()


def push_collect_notification(collector, photo_id, receiver):
    message = '用户 <a href="%s">%s</a> 收藏 <a href="%s">photo</a>' % \
              (url_for('user.index', username=collector.username),
               collector.username,
               url_for('blog.show_photo', photo_id=photo_id))
    notification = Notification(message=message, receiver=receiver)
    db.session.add(notification)
    db.session.commit()