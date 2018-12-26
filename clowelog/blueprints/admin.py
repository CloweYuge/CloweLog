from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from clowelog.models import Blog, Category, Comment, Link, User, Text, Role, Tag
from clowelog.forms.admin import EditProfileAdminForm
from clowelog.forms.blog import PostForm
from clowelog.extensions import db
from clowelog.decorators import permission_required, admin_required
from clowelog.utils import redirect_back


admin_bp = Blueprint('admin', __name__)


@admin_bp.before_request
@login_required
def login_protect():
    pass


@admin_bp.route('/')
def index():
    user_count = User.query.count()
    locked_user_count = User.query.filter_by(locked=True).count()
    blocked_user_count = User.query.filter_by(active=False).count()
    photo_count = Blog.query.count()
    reported_photos_count = Blog.query.filter(Blog.flag > 0).count()
    tag_count = Tag.query.count()
    comment_count = Comment.query.count()
    reported_comments_count = Comment.query.filter(Comment.flag > 0).count()
    return render_template('admin/index.html', user_count=user_count, photo_count=photo_count,
                           tag_count=tag_count, comment_count=comment_count, locked_user_count=locked_user_count,
                           blocked_user_count=blocked_user_count, reported_comments_count=reported_comments_count,
                           reported_photos_count=reported_photos_count)


@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('用户已删除！', 'success')
    return redirect_back()


@admin_bp.route('/user/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    user.open_admin()
    # db.session.commit()
    flash('已为其开通博客', 'success')
    return redirect_back()


@admin_bp.route('/post/mange')
def manage_post():
    page = request.args.get('page', 1, type=int)
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    pagination = Blog.query.with_parent(admin).order_by(
        Blog.timestamp.desc()).paginate(page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    posts = pagination.items
    return render_template('admin/manage_post.html', pagination=pagination, posts=posts)


@admin_bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = Blog.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除！', 'success')
    return redirect_back()


@admin_bp.route('/post/<int:blog_id>/set-comment', methods=['POST'])
def set_comment(blog_id):
    post = Blog.query.get_or_404(blog_id)
    if post.can_comment:
        post.can_comment = False
        flash('评论已禁止', 'success')
    else:
        post.can_comment = True
        flash('评论已开放', 'success')
    db.session.commit()
    return redirect_back()


@admin_bp.route('/comment/<int:comment_id>/approve', methods=['POST'])
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.reviewed = True
    db.session.commit()
    flash('评论已允许', 'success')
    return redirect_back()


@admin_bp.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除', 'success')
    return redirect_back()


@admin_bp.route('/category/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.id == 1:
        flash('你不能删除掉默认的分类', 'warning')
        return redirect(url_for('blog.index'))
    category.delete()
    flash('分类已删除，包括该分类下的所有文章！', 'success')
    return redirect(url_for('.manage_category'))


@admin_bp.route('/category/manage')
def manage_category():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    return render_template('admin/manage_category.html')


# @admin_bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
# def edit_category(category_id):
#     form = CategoryForm()
#     category = Category.query.get_or_404(category_id)
#     if category.id == 1:
#         flash('你不能修改默认分类的名称', 'warning')
#         return redirect(url_for('blog.index'))
#     if form.validate_on_submit():
#         category.name = form.name.data
#         db.session.commit()
#         flash('分类名称已更新！', 'success')
#         return redirect(url_for('.manage_category'))
#
#     form.name.data = category.name
#     return render_template('admin/edit_category.html', form=form)


# @admin_bp.route('/link/new', methods=['GET', 'POST'])
# def new_link():
#     admin = User.query.get(current_user.id).admin
#     if admin is None:
#         flash('对不起，您还未能开通博客权限！', 'success')
#         return redirect_back()
#     form = LinkForm()
#     if form.validate_on_submit():
#         name = form.name.data
#         url = form.url.data
#         link = Link(name=name, url=url)
#         db.session.add(link)
#         db.session.commit()
#         flash('Link created.', 'success')
#         return redirect(url_for('.manage_link'))
#     return render_template('admin/new_link.html', form=form)


@admin_bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        role = Role.query.get(form.role.data)
        if role.name == 'Locked':
            user.lock()
        user.role = role
        user.bio = form.bio.data
        user.website = form.website.data
        user.confirmed = form.confirmed.data
        user.active = form.active.data
        user.location = form.location.data
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('信息已更改.', 'success')
        return redirect_back()
    form.name.data = user.name
    form.role.data = user.role_id
    form.bio.data = user.bio
    form.website.data = user.site
    form.location.data = user.location
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    form.active.data = user.active
    return render_template('admin/edit_profile.html', form=form, user=user)


@admin_bp.route('/block/user/<int:user_id>', methods=['POST'])
@permission_required('MODERATE')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.block()
    flash('该账户已封禁.', 'info')
    return redirect_back()


@admin_bp.route('/unblock/user/<int:user_id>', methods=['POST'])
@permission_required('MODERATE')
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('解锁.', 'info')
    return redirect_back()


@admin_bp.route('/lock/user/<int:user_id>', methods=['POST'])
@permission_required('MODERATE')
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.lock()
    flash('锁定.', 'info')
    return redirect_back()


@admin_bp.route('/unlock/user/<int:user_id>', methods=['POST'])
@permission_required('MODERATE')
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('解锁.', 'info')
    return redirect_back()


@admin_bp.route('/link/manage')
def manage_link():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    return render_template('admin/manage_link.html')


@admin_bp.route('/delete/tag/<int:tag_id>', methods=['GET', 'POST'])
@permission_required('MODERATE')
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash('Tag deleted.', 'info')
    return redirect_back()


@admin_bp.route('/manage/user')
@permission_required('MODERATE')
def manage_user():
    filter_rule = request.args.get('filter', 'all')  # 'all', 'locked', 'blocked', 'administrator', 'moderator'
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_MANAGE_USER_PER_PAGE']
    administrator = Role.query.filter_by(name='Administrator').first()
    moderator = Role.query.filter_by(name='Moderator').first()

    if filter_rule == 'locked':
        filtered_users = User.query.filter_by(locked=True)
    elif filter_rule == 'blocked':
        filtered_users = User.query.filter_by(active=False)
    elif filter_rule == 'administrator':
        filtered_users = User.query.filter_by(role=administrator)
    elif filter_rule == 'moderator':
        filtered_users = User.query.filter_by(role=moderator)
    else:
        filtered_users = User.query

    pagination = filtered_users.order_by(User.timestamp.desc()).paginate(page, per_page)
    users = pagination.items
    return render_template('admin/manage_user.html', pagination=pagination, users=users)


@admin_bp.route('/manage/blog', defaults={'order': 'flag', 'blogtype': 'all'})
@admin_bp.route('/manage/blog/<order>/<blogtype>')
@permission_required('MODERATE')
def manage_blog(blogtype, order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_MANAGE_BLOG_PER_PAGE']
    order_rule = 'flag'
    blogtype_rule = 'all'
    if order == 'time':
        if blogtype == 'photo':
            pagination = Blog.query.filter(Blog.type == '2').order_by(Blog.timestamp.desc()).paginate(page, per_page)
            blogtype_rule = 'photo'
        elif blogtype == 'post':
            pagination = Blog.query.filter(Blog.type == '1').order_by(Blog.timestamp.desc()).paginate(page, per_page)
            blogtype_rule = 'post'
        else:
            pagination = Blog.query.order_by(Blog.timestamp.desc()).paginate(page, per_page)
        order_rule = 'time'
    else:
        if blogtype == 'photo':
            pagination = Blog.query.filter(Blog.type == '2').order_by(Blog.timestamp.desc()).paginate(page, per_page)
            blogtype_rule = 'photo'
        elif blogtype == 'post':
            pagination = Blog.query.filter(Blog.type == '1').order_by(Blog.timestamp.desc()).paginate(page, per_page)
            blogtype_rule = 'post'
        else:
            pagination = Blog.query.order_by(Blog.timestamp.desc()).paginate(page, per_page)
    blogs = pagination.items
    return render_template('admin/manage_blog.html', pagination=pagination, blogs=blogs, order_rule=order_rule, blogtype=blogtype_rule)


@admin_bp.route('/manage/tag')
@permission_required('MODERATE')
def manage_tag():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_MANAGE_TAG_PER_PAGE']
    pagination = Tag.query.order_by(Tag.id.desc()).paginate(page, per_page)
    tags = pagination.items
    return render_template('admin/manage_tag.html', pagination=pagination, tags=tags)


@admin_bp.route('/manage/comment', defaults={'order': 'by_flag'})
@admin_bp.route('/manage/comment/<order>')
@permission_required('MODERATE')
def manage_comment(order):
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_MANAGE_COMMENT_PER_PAGE']
    order_rule = 'flag'
    if order == 'by_time':
        pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page)
        order_rule = 'time'
    else:
        pagination = Comment.query.order_by(Comment.flag.desc()).paginate(page, per_page)
    comments = pagination.items
    return render_template('admin/manage_comment.html', pagination=pagination, comments=comments, order_rule=order_rule)
