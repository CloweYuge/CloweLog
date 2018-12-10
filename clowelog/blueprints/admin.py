from flask import Blueprint, render_template, request, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from clowelog.models import Post, Category, Comment, Link, Admin, User
from clowelog.forms import PostForm, CategoryForm, LinkForm, SettingForm
from clowelog.extensions import db
from clowelog.utils import redirect_back


admin_bp = Blueprint('admin', __name__)


@admin_bp.before_request
@login_required
def login_protect():
    pass


@admin_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingForm()
    admin = Admin.query.with_parent(User.query.get(current_user.id)).one()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.blog_title = form.blog_title.data
        current_user.blog_sub_title = form.blog_sub_title.data
        current_user.about = form.about.data
        db.session.commit()
        flash('设置已更新~', 'success')
        return redirect(url_for('blog.index'))
    form.name.data = current_user.name
    form.blog_title.data = admin.blog_title
    form.blog_sub_title.data = admin.blog_sub_title
    form.about.data = admin.about
    return render_template('admin/settings.html', form=form)


@admin_bp.route('/post/mange')
def manage_post():
    page = request.args.get('page', 1, type=int)
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    pagination = Post.query.with_parent(admin).order_by(
        Post.timestamp.desc()).paginate(page, per_page=current_app.config['BLUELOG_MANAGE_POST_PER_PAGE'])
    posts = pagination.items
    return render_template('admin/manage_post.html', pagination=pagination, posts=posts)


@admin_bp.route('/post/new', methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        category = Category.query.get(form.category.data)
        post = Post(title=title, body=body, category=category, admin=admin)
        # same with:
        # category_id = form.category.data
        # post = Post(title=title, body=body, category_id=category_id)
        db.session.add(post)
        db.session.commit()
        flash('文章已发布', 'success')
        return redirect(url_for('blog.show_post', post_id=post.id))
    return render_template('admin/new_post.html', form=form)


@admin_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    form = PostForm()
    post = Post.query.get_or_404(post_id)
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.category = Category.query.get(form.category.data)
        db.session.commit()
        flash('文章修改成功~', 'success')
        return redirect(url_for('blog.show_post', post_id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    form.category.data = post.category_id
    return render_template('admin/edit_post.html', form=form)


@admin_bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('文章已删除！', 'success')
    return redirect_back()


@admin_bp.route('/post/<int:post_id>/set-comment', methods=['POST'])
def set_comment(post_id):
    post = Post.query.get_or_404(post_id)
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


@admin_bp.route('/comment/manage')
def manage_comment():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    filter_rule = request.args.get('filter', 'all')  # 'all', 'unreviewed', 'admin'
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_COMMENT_PER_PAGE']
    if filter_rule == 'unread':
        filtered_comments = Comment.query.with_parent(admin).filter_by(reviewed=False)
    elif filter_rule == 'admin':
        filtered_comments = Comment.query.with_parent(admin).filter_by(from_admin=True)
    else:
        filtered_comments = Comment.query.with_parent(admin)

    pagination = filtered_comments.order_by(Comment.timestamp.desc()).paginate(page, per_page=per_page)
    comments = pagination.items
    return render_template('admin/manage_comment.html', comments=comments, pagination=pagination)


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


@admin_bp.route('/category/new', methods=['GET', 'POST'])
def new_category():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data
        category = Category(name=name, admin=admin)
        db.session.add(category)
        db.session.commit()
        flash('分类已创建', 'success')
        return redirect(url_for('.manage_category'))
    return render_template('admin/new_category.html', form=form)


@admin_bp.route('/category/manage')
@login_required
def manage_category():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    return render_template('admin/manage_category.html')


@admin_bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    form = CategoryForm()
    category = Category.query.get_or_404(category_id)
    if category.id == 1:
        flash('你不能修改默认分类的名称', 'warning')
        return redirect(url_for('blog.index'))
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('分类名称已更新！', 'success')
        return redirect(url_for('.manage_category'))

    form.name.data = category.name
    return render_template('admin/edit_category.html', form=form)


@admin_bp.route('/link/new', methods=['GET', 'POST'])
def new_link():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    form = LinkForm()
    if form.validate_on_submit():
        name = form.name.data
        url = form.url.data
        link = Link(name=name, url=url)
        db.session.add(link)
        db.session.commit()
        flash('Link created.', 'success')
        return redirect(url_for('.manage_link'))
    return render_template('admin/new_link.html', form=form)


@admin_bp.route('/link/manage')
def manage_link():
    admin = User.query.get(current_user.id).admin
    if admin is None:
        flash('对不起，您还未能开通博客权限！', 'success')
        return redirect_back()
    return render_template('admin/manage_link.html')
