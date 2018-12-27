from flask import Blueprint, render_template, request, current_app, url_for, flash, redirect, abort, make_response
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func
from clowelog.forms.blog import DescriptionForm, TagForm, CategoryForm, CommentForm, PhotosForm, PostForm
from clowelog.models import Category, Comment, User, Blog, Follow, Tag, Collect, Text
from clowelog.extensions import db
from clowelog.utils import redirect_back, flash_errors
from clowelog.decorators import permission_required, confirm_required
from clowelog.notifications import push_comment_notification

blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/')
def index():
    if current_user.is_authenticated:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['CLOWELOG_BLOG_PER_PAGE']
        pagination = Blog.query \
            .join(Follow, Follow.followed_id == Blog.user_id) \
            .filter(Follow.follower_id == current_user.id) \
            .order_by(Blog.timestamp.desc()) \
            .paginate(page, per_page)
        blogs = pagination.items
    else:
        pagination = None
        blogs = None
    tags = Tag.query.join(Tag.blogs).group_by(Tag.id).order_by(func.count(Blog.id).desc()).limit(10)
    categorys = Category.query.join(Category.blogs).group_by(Category.id).order_by(func.count(Blog.id).desc()).limit(10)
    return render_template('blog/index.html', pagination=pagination, blogs=blogs, Collect=Collect,
                           tags=tags, categorys=categorys)


@blog_bp.route('/explore')
def explore():
    blogs = Blog.query.order_by(func.rand()).limit(12)
    return render_template('blog/explore.html', blogs=blogs)


@blog_bp.route('/about')
def about():
    return render_template('blog/about.html', about=current_app.config['BLOG_ABOUT'])


@blog_bp.route('/category/<int:category_id>')
def show_category(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_BLOG_PER_PAGE']
    pagination = Blog.query.filter(Blog.category_id == category_id).order_by(Blog.timestamp.desc()).paginate(page, per_page=per_page)
    blogs = pagination.items

    category_form = CategoryForm()
    return render_template('blog/category.html', category=category, user=current_user,category_form=category_form, pagination=pagination, blogs=blogs)


@blog_bp.route('/post/<int:blog_id>')
def show_post(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    blog_user = blog.user
    page = request.args.get('page', default=1, type=int)
    per_page = current_app.config['CLOWELOG_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(blog).order_by(Comment.timestamp.desc()).paginate(page, per_page=per_page)
    comments = pagination.items

    comment_form = CommentForm()
    category_form = CategoryForm()

    return render_template('blog/show_post.html', blog=blog, comment_form=comment_form, user=blog_user,
                           category_form=category_form, pagination=pagination,
                           comments=comments)


@blog_bp.route('/photo/<int:blog_id>')
def show_photo(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    page = request.args.get('page', default=1, type=int)
    per_page = current_app.config['CLOWELOG_COMMENT_PER_PAGE']
    pagination = Comment.query.with_parent(blog).order_by(Comment.timestamp.asc()).paginate(page, per_page)
    comments = pagination.items

    comment_form = CommentForm()
    description_form = DescriptionForm()
    tag_form = TagForm()

    description_form.description.data = blog.description
    return render_template('blog/show_photo.html', blog=blog, comment_form=comment_form,
                           description_form=description_form, tag_form=tag_form,
                           pagination=pagination, comments=comments)


@blog_bp.route('/tag/<int:tag_id>', defaults={'order': 'by_time'})
@blog_bp.route('/tag/<int:tag_id>/<order>')
def show_tag(tag_id, order):
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_PHOTO_PER_PAGE']
    order_rule = 'time'
    pagination = Blog.query.with_parent(tag).order_by(Blog.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items

    if order == 'by_collects':
        photos.sort(key=lambda x: len(x.collectors), reverse=True)
        order_rule = 'collects'
    return render_template('blog/tag.html', tag=tag, pagination=pagination, photos=photos, order_rule=order_rule)


@blog_bp.route('/blog/<int:blog_id>/collectors')
def show_collectors(blog_id):
    photo = Blog.query.get_or_404(blog_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_USER_PER_PAGE']
    pagination = Collect.query.with_parent(photo).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('blog/collectors.html', collects=collects, blog=photo, pagination=pagination)


@blog_bp.route('/delete/blog/<int:blog_id>', methods=['POST'])
@login_required
def delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if current_user != blog.user and not current_user.can('MODERATE'):
        abort(403)

    db.session.delete(blog)
    db.session.commit()
    flash('博文已删除.', 'info')

    blog_n = Blog.query.with_parent(blog.user).filter(Blog.id < blog_id, Blog.type == blog.type).order_by(Blog.id.desc()).first()
    if blog_n is None:
        blog_p = Blog.query.with_parent(blog.user).filter(Blog.id > blog_id, Blog.type == blog.type).order_by(Blog.id.asc()).first()
        if blog_p is None:
            return redirect(url_for('user.index', username=blog.user.username))
        if blog.type == 2:
            return redirect(url_for('.show_photo', blog_id=blog_p))
        elif blog.type == 1:
            return redirect(url_for('.show_post', blog_id=blog_p))
    if blog.type == 2:
        return redirect(url_for('.show_photo', blog_id=blog_n))
    elif blog.type == 1:
        return redirect(url_for('.show_post', blog_id=blog_n))


@blog_bp.route('/photo/n/<int:blog_id>')
def blog_next(blog_id):
    photo = Blog.query.get_or_404(blog_id)
    photo_n = Blog.query.with_parent(photo.user).filter(Blog.id < blog_id, Blog.type == photo.type).order_by(Blog.id.desc()).first()

    if photo_n is None:
        flash('这已经是最后一个了.', 'info')
        return redirect(url_for('.show_photo', blog_id=blog_id))
    return redirect(url_for('.show_photo', blog_id=photo_n.id))


@blog_bp.route('/photo/p/<int:blog_id>')
def blog_previous(blog_id):
    photo = Blog.query.get_or_404(blog_id)
    photo_p = Blog.query.with_parent(photo.user).filter(Blog.id > blog_id, Blog.type == photo.type).order_by(Blog.id.asc()).first()

    if photo_p is None:
        flash('这已经是第一个了.', 'info')
        return redirect(url_for('.show_photo', blog_id=blog_id))
    return redirect(url_for('.show_photo', blog_id=photo_p.id))


@blog_bp.route('/blog/<int:blog_id>/description', methods=['POST'])
@login_required
def edit_description(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if current_user != blog.user and not current_user.can('MODERATE'):
        abort(403)

    form = DescriptionForm()
    if form.validate_on_submit():
        blog.description = form.description.data
        db.session.commit()
        flash('Description updated.', 'success')

    flash_errors(form)
    if blog.type == 2:
        return redirect(url_for('.show_photo', blog_id=blog_id))
    elif blog.type == 1:
        return redirect(url_for('.show_post', blog_id=blog_id))


@blog_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('该评论已被举报.', 'success')
    if comment.blog.type == 2:
        return redirect(url_for('.show_photo', blog_id=comment.blog_id))
    elif comment.blog.type == 1:
        return redirect(url_for('.show_post', blog_id=comment.blog_id))


@blog_bp.route('/report/blog/<int:blog_id>', methods=['POST'])
@login_required
@confirm_required
def report_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    blog.flag += 1
    db.session.commit()
    flash('该博文已举报.', 'success')
    if blog.type == 2:
        return redirect(url_for('.show_photo', blog_id=blog_id))
    elif blog.type == 1:
        return redirect(url_for('.show_post', blog_id=blog_id))


@blog_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(url_for('.show_post',
                            blog_id=comment.blog_id, reply=comment_id, author=comment.user.name) + '#comment-form')


@blog_bp.route('/delete/comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.user and current_user != comment.blog.user \
            and not current_user.can('MODERATE'):
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除', 'info')
    return redirect_back()


@blog_bp.route('/change-theme/<theme_name>')
def change_theme(theme_name):
    if theme_name not in current_app.config['BLUELOG_THEMES'].keys():
        abort(404)
    response = make_response(redirect_back())
    response.set_cookie('theme', theme_name, max_age=30*24*60*60)
    return response


@blog_bp.route('/blog/<int:blog_id>/comment/new', methods=['POST'])
@login_required
@permission_required('COMMENT')
def new_comment(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    page = request.args.get('page', default=1, type=int)
    if page == 0:
        page = 1
    form = CommentForm()
    if form.validate_on_submit():
        body = form.body.data
        user = current_user._get_current_object()
        comment = Comment(body=body, user=user, blog=blog)

        replied_id = request.args.get('reply')
        if replied_id:
            comment.replied = Comment.query.get_or_404(replied_id)
            if comment.replied.user.receive_comment_notification:
                push_comment_notification(blog_id=blog.id, receiver=comment.replied.user, type=blog.type)
        db.session.add(comment)
        db.session.commit()
        flash('评论已推送.', 'success')

        if current_user != blog.user and blog.user.receive_comment_notification:
            push_comment_notification(blog_id, receiver=blog.user, page=page, type=blog.type)

    flash_errors(form)
    if blog.type == 2:
        return redirect(url_for('.show_photo', blog_id=blog_id, page=page))
    elif blog.type == 1:
        return redirect(url_for('.show_post', blog_id=blog_id, page=page))


@blog_bp.route('/blog/<int:blog_id>/tag/new', methods=['POST'])
@login_required
def new_tag(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if current_user != blog.user and not current_user.can('MODERATE'):
        abort(403)

    form = TagForm()
    if form.validate_on_submit():
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in blog.tags:
                blog.tags.append(tag)
                db.session.commit()
        flash('标签已添加.', 'success')

    flash_errors(form)
    return redirect(url_for('.show_photo', blog_id=blog_id))


@blog_bp.route('/delete/tag/<int:blog_id>/<int:tag_id>', methods=['POST'])
@login_required
def delete_tag(blog_id, tag_id):
    tag = Tag.query.get_or_404(tag_id)
    photo = Blog.query.get_or_404(blog_id)
    if current_user != photo.user and not current_user.can('MODERATE'):
        abort(403)
    photo.tags.remove(tag)
    db.session.commit()

    if not tag.photos:
        db.session.delete(tag)
        db.session.commit()

    flash('Tag deleted.', 'info')
    return redirect(url_for('.show_photo', blog_id=blog_id))


