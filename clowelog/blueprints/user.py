from flask import Blueprint, render_template, request, current_app, url_for, flash, redirect, abort, make_response
from flask_login import current_user
from clowelog.forms import AdminCommentForm, CommentForm
from clowelog.emails import send_new_comment_email, send_new_reply_email
from clowelog.models import Post, Category, Comment, User
from clowelog.extensions import db
from clowelog.utils import redirect_back


user_bp = Blueprint('user', __name__)


@user_bp.route('/<int:user_id>')
def index(user_id):
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['BLUELOG_POST_PER_PAGE']
    admin = User.query.get(user_id).admin
    if admin:
        pagination = Post.query.with_parent(admin).order_by(Post.timestamp.desc()).paginate(
            page, per_page=per_page, error_out=False)
    else:
        flash('还没有开通博文哟~')
        return redirect_back()
    # pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page=per_page, error_out=False)
    posts = pagination.items
    return render_template('blog/index.html', posts=posts, pagination=pagination)


# @user_bp.route('/about')
# def about():
#     return render_template('blog/about.html')


# @user_bp.route('/category/<int:category_id>')
# def show_category(category_id):
#     category = Category.query.get_or_404(category_id)
#     page = request.args.get('page', 1, type=int)
#     per_page = current_app.config['BLUELOG_POST_PER_PAGE']
#     pagination = Post.query.with_parent(category).order_by(Post.timestamp.desc()).paginate(page, per_page=per_page)
#     posts = pagination.items
#     return render_template('blog/category.html', category=category, pagination=pagination, posts=posts)


# @user_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
# def show_post(post_id):
#     post = Post.query.get_or_404(post_id)
#     page = request.args.get('page', 1, type=int)
#     per_page = current_app.config['BLUELOG_POST_PER_PAGE']
#     pagination = Comment.query.with_parent(post).order_by(Comment.timestamp.desc()).paginate(page, per_page=per_page)
#     comments = pagination.items
#     if current_user.is_authenticated:
#         form = AdminCommentForm()
#         form.author.data = current_user.name
#         form.email.data = current_app.config['BLUELOG_EMAIL']
#         form.site.data = url_for('.index')
#         from_admin = True
#         reviewed = True
#     else:
#         form = CommentForm()
#         from_admin = False
#         reviewed = False
#
#     if form.validate_on_submit():
#         author = form.author.data
#         email = form.email.data
#         site = form.site.data
#         body = form.body.data
#         comment = Comment(
#             author=author, email=email, site=site, body=body,
#             from_admin=from_admin, post=post, reviewed=reviewed)
#         replied_id = request.args.get('reply')
#         if replied_id:
#             replied_comment = Comment.query.get_or_404(replied_id)
#             comment.replied = replied_comment
#             send_new_reply_email(replied_comment)
#         db.session.add(comment)
#         db.session.commit()
#         if current_user.is_authenticated:  # send message based on authentication status
#             flash('Comment published.', 'success')
#         else:
#             flash('Thanks, your comment will be published after reviewed.', 'info')
#             send_new_comment_email(post)  # send notification email to admin
#         return redirect(url_for('.show_post', post_id=post_id) + '#comments')
#     return render_template('blog/post.html', post=post, pagination=pagination, form=form, comments=comments)
#
#
# @user_bp.route('/reply/comment/<int:comment_id>')
# def reply_comment(comment_id):
#     comment = Comment.query.get_or_404(comment_id)
#     return redirect(url_for('.show_post',
#                             post_id=comment.post_id, reply=comment_id, author=comment.author) + '#comment-form')
#
#
# @user_bp.route('/change-theme/<theme_name>')
# def change_theme(theme_name):
#     if theme_name not in current_app.config['BLUELOG_THEMES'].keys():
#         abort(404)
#     response = make_response(redirect_back())
#     response.set_cookie('theme', theme_name, max_age=30*24*60*60)
#     return response