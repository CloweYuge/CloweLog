from flask import Blueprint, render_template, request, current_app, url_for, flash, redirect, abort, make_response
from flask_login import current_user
from clowelog.forms import AdminCommentForm, CommentForm
from clowelog.emails import send_new_comment_email, send_new_reply_email
from clowelog.models import Post, Category, Comment, User, Admin
from clowelog.extensions import db
from clowelog.utils import redirect_back

blog_bp = Blueprint('blog', __name__)


@blog_bp.route('/')
def index():
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=per_page, error_out=False)
    posts = pagination.items
    return render_template('blog/index.html', posts=posts, pagination=pagination)


@blog_bp.route('/about')
def about():
    return render_template('blog/about.html')


@blog_bp.route('/category/<int:category_id>')
def show_category(category_id):
    # admin = Admin.query.get(current_user.id).admin
    # if admin is None:
    #     flash('对不起，您还未能开通博客权限！', 'success')
    #     return redirect_back()
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Post.query.with_parent(category).order_by(Post.timestamp.desc()).paginate(page, per_page=per_page)
    posts = pagination.items
    return render_template('blog/category.html', category=category, pagination=pagination, posts=posts)


@blog_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    post = Post.query.get_or_404(post_id)
    admin = post.admin
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    pagination = Comment.query.with_parent(post).order_by(Comment.timestamp.desc()).paginate(page, per_page=per_page)
    comments = pagination.items

    if current_user.is_authenticated:
        admin_user = Admin.query.get(current_user.id)
        form = CommentForm()
        # form.author.data = current_user.name
        # form.email.data = current_app.config['BLUELOG_EMAIL']
        # form.site.data = url_for('.index')
        if admin_user is None:
            from_admin = False
            reviewed = False
        elif admin_user.id == admin.id:
            from_admin = True
            reviewed = True
        else:
            from_admin = False
            reviewed = True
    else:
        form = CommentForm()
        # form.author.data = current_user.name
        from_admin = False
        reviewed = False

    if form.validate_on_submit():
        # author = form.author.data
        # email = form.email.data
        # site = form.site.data
        body = form.body.data
        user = User.query.get_or_404(current_user.id)
        comment = Comment(user=user, admin=admin, body=body, from_admin=from_admin, post=post, reviewed=reviewed)
        replied_id = request.args.get('reply')
        if replied_id:
            replied_comment = Comment.query.get_or_404(replied_id)
            comment.replied = replied_comment
            # send_new_reply_email(replied_comment)
        if current_user.is_authenticated:  # send message based on authentication status
            db.session.add(comment)
            db.session.commit()
            flash('已推送评论', 'success')
        elif Admin.query.get(current_user.id):
            db.session.add(comment)
            db.session.commit()
            flash('谢谢，你的评论需要等待管理者批准显示', 'info')
            # send_new_comment_email(post)  # send notification email to admin
        else:
            flash('注册账号后才能评论！', 'success')
        return redirect(url_for('.show_post', post_id=post_id) + '#comments')
    return render_template('blog/post.html', post=post, pagination=pagination, form=form, comments=comments)


@blog_bp.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    return redirect(url_for('.show_post',
                            post_id=comment.post_id, reply=comment_id, author=comment.user.name) + '#comment-form')


@blog_bp.route('/change-theme/<theme_name>')
def change_theme(theme_name):
    if theme_name not in current_app.config['BLUELOG_THEMES'].keys():
        abort(404)
    response = make_response(redirect_back())
    response.set_cookie('theme', theme_name, max_age=30*24*60*60)
    return response
