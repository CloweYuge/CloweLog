from flask import render_template, jsonify, Blueprint
from flask_login import current_user

from clowelog.models import User, Blog, Notification
from clowelog.notifications import push_collect_notification, push_follow_notification

ajax_bp = Blueprint('ajax', __name__)


@ajax_bp.route('/notifications-count')
def notifications_count():
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
    return jsonify(count=count)


@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)


@ajax_bp.route('/followers-count/<int:user_id>')
def followers_count(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1  # minus user self
    return jsonify(count=count)


@ajax_bp.route('/<int:blog_id>/followers-count')
def collectors_count(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    count = len(blog.collectors)
    return jsonify(count=count)


@ajax_bp.route('/collect/<int:blog_id>', methods=['POST'])
def collect(blog_id):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    if not current_user.confirmed:
        return jsonify(message='Confirm account required.'), 400
    if not current_user.can('COLLECT'):
        return jsonify(message='No permission.'), 403

    blog = Blog.query.get_or_404(blog_id)
    if current_user.is_collecting(blog):
        return jsonify(message='Already collected.'), 400

    current_user.collect(blog)
    if current_user != blog.user and blog.user.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=blog_id, receiver=blog.user)
    return jsonify(message='Photo collected.')


@ajax_bp.route('/uncollect/<int:blog_id>', methods=['POST'])
def uncollect(blog_id):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    blog = Blog.query.get_or_404(blog_id)
    if not current_user.is_collecting(blog):
        return jsonify(message='Not collect yet.'), 400

    current_user.uncollect(blog)
    return jsonify(message='Collect canceled.')


@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    if not current_user.confirmed:
        return jsonify(message='Confirm account required.'), 400
    if not current_user.can('FOLLOW'):
        return jsonify(message='No permission.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        return jsonify(message='Already followed.'), 400

    current_user.follow(user)
    if user.receive_collect_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return jsonify(message='User followed.')


@ajax_bp.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        return jsonify(message='Not follow yet.'), 400

    current_user.unfollow(user)
    return jsonify(message='Follow canceled.')