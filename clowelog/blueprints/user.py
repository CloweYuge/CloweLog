from flask import Blueprint, render_template, request, current_app, url_for, flash, redirect, abort, make_response
from flask_login import current_user, logout_user, login_required, fresh_login_required
from clowelog.forms.blog import CategoryForm
from clowelog.forms.user import UploadAvatarForm, CropAvatarForm, EditProfileForm, ChangePasswordForm, \
    ChangeEmailForm, NotificationSettingForm, PrivacySettingForm, DeleteAccountForm
from clowelog.emails import send_confirm_email
from clowelog.models import Blog, Category, User, Collect, Notification
from clowelog.extensions import db, avatars
from clowelog.decorators import confirm_required, permission_required
from clowelog.settings import Operations
from clowelog.utils import redirect_back, flash_errors, validate_token, generate_token
from clowelog.notifications import push_follow_notification


user_bp = Blueprint('user', __name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user and user.locked:
        flash('你的账号已被锁定，请尽快联系管理员恢复', 'danger')

    if user == current_user and not user.active:
        logout_user()
    if not user.can('UPPOST'):
        return redirect(url_for('.show_photo', username=user.username))
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_BLOG_PER_PAGE']
    pagination = Blog.query.with_parent(user).filter_by(type=1).order_by(Blog.timestamp.desc()).paginate(page, per_page)
    blogs = pagination.items
    categorys = Category.query.with_parent(user).order_by(Category.name.desc())

    category_form = CategoryForm()
    return render_template('user/index.html', user=user, pagination=pagination, category_form=category_form,
                           blogs=blogs, categorys=categorys)


@user_bp.route('/<username>/photos')
def show_photo(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_BLOG_PER_PAGE']
    pagination = Blog.query.with_parent(user).filter_by(type=2).order_by(Blog.timestamp.desc()).paginate(page, per_page)
    blogs = pagination.items
    return render_template('user/photos.html', user=user, pagination=pagination, blogs=blogs)


@user_bp.route('/<username>/collections')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_BLOG_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.desc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)


@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@confirm_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('已关注', 'info')
        return redirect(url_for('.index', username=username))

    current_user.follow(user)
    flash('关注成功', 'success')
    if user.receive_follow_notification:
        push_follow_notification(follower=current_user, receiver=user)
    return redirect_back()


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('不再关注', 'info')
        return redirect(url_for('.index', username=username))

    current_user.unfollow(user)
    flash('并没有关注', 'info')
    return redirect_back()


@user_bp.route('/<username>/followers')
def show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_USER_PER_PAGE']
    pagination = user.followers.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/followers.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/<username>/following')
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_USER_PER_PAGE']
    pagination = user.following.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/following.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/settings/avatar/<upload>')
@login_required
@confirm_required
def change_avatar(upload='l'):
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/settings/change_avatar.html', upload_form=upload_form,
                           crop_form=crop_form, upload=upload)


@user_bp.route('/settings/avatar/upload', methods=['POST'])
@login_required
@confirm_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('现在可以剪裁了。', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar', upload='r'))


@user_bp.route('/settings/avatar/crop', methods=['POST'])
@login_required
@confirm_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        current_user.avatar_s = filenames[0]
        current_user.avatar_m = filenames[1]
        current_user.avatar_l = filenames[2]
        db.session.commit()
        flash('头像已更新.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar', upload='l'))


@user_bp.route('/notifications')
@login_required
def show_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_NOTIFICATION_PER_PAGE']
    notifications = Notification.query.with_parent(current_user)
    filter_rule = request.args.get('filter')
    if filter_rule == 'unread':
        notifications = notifications.filter_by(is_read=False)

    pagination = notifications.order_by(Notification.timestamp.desc()).paginate(page, per_page)
    notifications = pagination.items
    return render_template('user/notifications.html', pagination=pagination, notifications=notifications)


@user_bp.route('/notification/read/<int:notification_id>', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if current_user != notification.receiver:
        abort(403)

    notification.is_read = True
    db.session.commit()
    flash('消息已读', 'success')
    return redirect(url_for('.show_notifications'))


@user_bp.route('/notifications/read/all', methods=['POST'])
@login_required
def read_all_notification():
    for notification in current_user.notifications:
        notification.is_read = True
    db.session.commit()
    flash('所有消息已读', 'success')
    return redirect(url_for('.show_notifications'))


@user_bp.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data
        current_user.location = form.location.data
        db.session.commit()
        flash('资料已更新', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.bio.data = current_user.bio
    form.website.data = current_user.site
    form.location.data = current_user.location
    return render_template('user/settings/edit_profile.html', form=form)


@user_bp.route('/settings/change-password', methods=['GET', 'POST'])
@fresh_login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit() and current_user.validate_password(form.old_password.data):
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('密码已更新', 'success')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_password.html', form=form)

@user_bp.route('/settings/change-email', methods=['GET', 'POST'])
@fresh_login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = generate_token(user=current_user, operation=Operations.CHANGE_EMAIL, new_email=form.email.data.lower())
        send_confirm_email(to=form.email.data, user=current_user, token=token)
        flash('请检查邮箱，确认邮件是改变生效', 'info')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_email.html', form=form)


@user_bp.route('/change-email/<token>')
@login_required
def change_email(token):
    if validate_token(user=current_user, token=token, operation=Operations.CHANGE_EMAIL):
        flash('邮箱已更新', 'success')
        return redirect(url_for('.index', username=current_user.username))
    else:
        flash('Invalid or expired token.', 'warning')
        return redirect(url_for('.change_email_request'))


@user_bp.route('/settings/notification', methods=['GET', 'POST'])
@login_required
def notification_setting():
    form = NotificationSettingForm()
    if form.validate_on_submit():
        current_user.receive_collect_notification = form.receive_collect_notification.data
        current_user.receive_comment_notification = form.receive_comment_notification.data
        current_user.receive_follow_notification = form.receive_follow_notification.data
        db.session.commit()
        flash('提醒设置已生效', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.receive_collect_notification.data = current_user.receive_collect_notification
    form.receive_comment_notification.data = current_user.receive_comment_notification
    form.receive_follow_notification.data = current_user.receive_follow_notification
    return render_template('user/settings/edit_notification.html', form=form)


@user_bp.route('/settings/privacy', methods=['GET', 'POST'])
@login_required
def privacy_setting():
    form = PrivacySettingForm()
    if form.validate_on_submit():
        current_user.public_collections = form.public_collections.data
        db.session.commit()
        flash('隐私设置已生效', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.public_collections.data = current_user.public_collections
    return render_template('user/settings/edit_privacy.html', form=form)


@user_bp.route('/settings/account/delete', methods=['GET', 'POST'])
@fresh_login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('Your are dagman, goodbye!', 'success')
        return redirect(url_for('blog.index'))
    return render_template('user/settings/delete_account.html', form=form)


@user_bp.route('/category/new', methods=['POST'])
@permission_required('UPPOST')
def new_category():
    user = User.query.get_or_404(current_user.id)
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.category.data
        category = Category(name=name)
        category.user.append(user)
        db.session.add(category)
        db.session.commit()
        flash('分类已创建', 'success')
    return redirect_back()


@user_bp.route('/category/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    user = User.query.get_or_404(current_user.id)
    if category.id == 1:
        flash('你不能删除掉默认的分类', 'warning')
        return redirect_back()
    blogs = Blog.query.with_parent(user).filter_by(category=category)
    if blogs.count():
        blogs.update({'category': Category.query.get(1)})
    user.categorys.remove(category)
    db.session.commit()
    flash('分类已删除，该分类下的文章已移动到默认分类下！', 'success')
    return redirect_back()
