from flask import Blueprint, url_for, redirect, flash, render_template
from flask_login import login_user, current_user, login_required, logout_user, login_fresh, confirm_login
from clowelog.extensions import db
from clowelog.settings import Operations
from clowelog.emails import send_confirm_email
from clowelog.models import User
from clowelog.forms.auth import LoginForm, JoinForm
from clowelog.utils import redirect_back, generate_token, validate_token

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user is not None and user.validate_password(form.password.data):
                if login_user(user, form.remember.data):
                    flash('欢迎回来~，' + user.name, 'info')
                    return redirect_back()
                else:
                    flash('你的账户已经被锁定', 'warning')
                    return redirect(url_for('blog.index'))
            flash('用户名与密码不匹配！', 'warning')
        else:
            flash('没有该账号！', 'warning')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/re-authenticate', methods=['GET', 'POST'])
@login_required
def re_authenticate():
    if login_fresh():
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit() and current_user.validate_password(form.password.data):
        confirm_login()
        return redirect_back()
    return render_template('auth/login.html', form=form)


@auth_bp.route('/join', methods=['GET', 'POST'])
def join():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = JoinForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data.lower()
        username = form.username.data
        password = form.password.data
        user = User(name=name, email=email, confirmed=True, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        # token = generate_token(user=user, operation='confirm')
        # send_confirm_email(user=user, token=token)
        flash('确认已发送的电子邮件，请检查收件箱。 ', 'info')
        return redirect(url_for('.login'))
    return render_template('auth/join.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-confirm-email')
@login_required
def resend_confirm_email():
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    token = generate_token(user=current_user, operation=Operations.CONFIRM)
    send_confirm_email(user=current_user, token=token)
    flash('New email sent, check your inbox.', 'info')
    return redirect(url_for('main.index'))
