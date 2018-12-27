import os

from flask import render_template, flash, redirect, url_for, current_app, \
    send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user
from flask_dropzone import random_filename
from sqlalchemy.sql.expression import func

from clowelog.decorators import confirm_required, permission_required
from clowelog.extensions import db
from clowelog.forms.blog import DescriptionForm, TagForm, CommentForm, PhotosForm, PostForm
from clowelog.models import User, Photo, Tag, Follow, Collect, Comment, Notification, Blog, Category, Text
from clowelog.notifications import push_comment_notification, push_collect_notification
from clowelog.utils import rename_image, resize_image, redirect_back, flash_errors

main_bp = Blueprint('main', __name__)


@main_bp.route('/search')
def search():
    q = request.args.get('q', '')
    if q == '':
        flash('可搜索到的关键词包含文章，图文，分类，标签，以及用户', 'warning')
        return redirect_back()

    category = request.args.get('category', 'photo')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['CLOWELOG_SEARCH_RESULT_PER_PAGE']
    if category == 'user':
        pagination = User.query.whooshee_search(q).paginate(page, per_page)
    elif category == 'tag':
        pagination = Tag.query.whooshee_search(q).paginate(page, per_page)
    else:
        pagination = Blog.query.whooshee_search(q).paginate(page, per_page)
    results = pagination.items
    return render_template('blog/search.html', q=q, results=results, pagination=pagination, category=category)


@main_bp.route('/post/new', methods=['GET', 'POST'])
@permission_required('UPPOST')
def new_post():
    form = PostForm()
    user = User.query.get(current_user.id)
    if form.validate_on_submit():
        description = form.title.data
        body = form.body.data
        category = Category.query.get(form.category.data)
        text = Text(body=body)
        db.session.add(text)
        blog = Blog(description=description, type=1, category=category, user=user, text=text)
        db.session.add(blog)
        db.session.commit()
        flash('文章已发布', 'success')
        return redirect(url_for('blog.show_post', blog_id=blog.id))
    return render_template('blog/new_post.html', form=form)


@main_bp.route('/post/<int:blog_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(blog_id):
    form = PostForm()
    post = Blog.query.get_or_404(blog_id)
    if form.validate_on_submit():
        post.description = form.title.data
        post.text.body = form.body.data
        post.category = Category.query.get(form.category.data)
        db.session.commit()
        flash('文章已修改', 'success')
        return redirect(url_for('blog.show_post', blog_id=post.id))
    form.title.data = post.description
    form.body.data = post.text.body
    form.category.data = post.category_id
    return render_template('main/edit_post.html', form=form, blog_id=post.id)


@main_bp.route('/upload/<stacie>', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPPHOTO')
def upload(stacie):
    if request.method == 'POST' and stacie == 'upload':
        user = User.query.get_or_404(current_user.id)
        blog = Blog(user=user, type=2)
        db.session.add(blog)
        db.session.commit()
        for file, f in request.files.items():
            filename = rename_image(f.filename)
            f.save(os.path.join(current_app.config['CLOWELOG_UPLOAD_PATH'], filename))
            filename_s, type = resize_image(f, filename, current_app.config['CLOWELOG_PHOTO_SIZE']['small'])
            filename_m, type = resize_image(f, filename, current_app.config['CLOWELOG_PHOTO_SIZE']['medium'])
            photo = Photo(
                filename=filename,
                filename_s=filename_s,
                filename_m=filename_m,
                blog=blog,
                type_photo=type
            )
            db.session.add(photo)
            db.session.commit()
    form = PhotosForm()
    blog = None
    return render_template('blog/upload.html', blog=blog, form=form, stacie=stacie)


@main_bp.route('/upload', methods=['GET'])
@login_required
@confirm_required
@permission_required('UPPHOTO')
def upload_edit():
    form = PhotosForm()
    user = User.query.get_or_404(current_user.id)
    blog = Blog.query.with_parent(user).order_by(Blog.timestamp.desc()).first()
    photos = Photo.query.with_parent(blog).all()
    return render_template('blog/upload.html', photos=photos, blog=blog,
                           form=form, stacie='text')


@main_bp.route('/blog/<int:blog_id>/edit', methods=['POST'])
@login_required
def edit_photos(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if current_user != blog.user and not current_user.can('MODERATE'):
        abort(403)

    form = PhotosForm()
    if form.validate_on_submit():
        blog.description = form.description.data
        db.session.commit()
        for name in form.tag.data.split():
            tag = Tag.query.filter_by(name=name).first()
            if tag is None:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.commit()
            if tag not in blog.tags:
                blog.tags.append(tag)
                db.session.commit()
        flash('已发布成功.', 'success')

    flash_errors(form)
    return redirect(url_for('blog.show_photo', blog_id=blog_id))


@main_bp.route('/collect/<int:blog_id>', methods=['POST'])
@login_required
@confirm_required
@permission_required('COLLECT')
def collect(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if current_user.is_collecting(blog):
        flash('已经收藏了.', 'info')
        return redirect(url_for('.show_photo', blog_id=blog_id))

    current_user.collect(blog)
    flash('已收藏该贴.', 'success')
    if current_user != blog.user and blog.user.receive_collect_notification:
        push_collect_notification(collector=current_user, blog_id=blog_id, receiver=blog.user, type=blog.type)
    return redirect(url_for('blog.show_photo', blog_id=blog_id))


@main_bp.route('/uncollect/<int:blog_id>', methods=['POST'])
@login_required
def uncollect(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    if not current_user.is_collecting(blog):
        flash('Not collect yet.', 'info')
        return redirect(url_for('blog.show_photo', blog_id=blog_id))

    current_user.uncollect(blog)
    flash('Photo uncollected.', 'info')
    return redirect(url_for('blog.show_photo', blog_id=blog_id))


@main_bp.route('/avatars/<path:filename>')
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)


@main_bp.route('/uploads/<path:filename>')
def get_image(filename):
    return send_from_directory(current_app.config['CLOWELOG_UPLOAD_PATH'], filename)


@main_bp.route('/report/comment/<int:comment_id>', methods=['POST'])
@login_required
@confirm_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.flag += 1
    db.session.commit()
    flash('已成功举报该评论.', 'success')
    return redirect(url_for('.show_photo', photo_id=comment.photo_id))


@main_bp.route('/report/photo/<int:photo_id>', methods=['POST'])
@login_required
@confirm_required
def report_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    photo.flag += 1
    db.session.commit()
    flash('已成功举报.', 'success')
    return redirect(url_for('.show_photo', photo_id=photo.id))

