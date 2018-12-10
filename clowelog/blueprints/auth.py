from flask import Blueprint, url_for, redirect, flash, render_template
from flask_login import login_user, current_user, login_required, logout_user
from clowelog.extensions import db
from clowelog.models import User
from clowelog.forms import LoginForm, JoinForm
from clowelog.utils import redirect_back

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        # admin = Admin.query.first()
        user = User.query.filter_by(username=username).first()
        if user:
            if username == user.username and user.validate_password(password):
                login_user(user, remember)
                flash('欢迎回来~，' + user.name, 'info')
                return redirect_back()
            flash('用户名与密码不匹配！', 'warning')
        else:
            flash('没有该账号！', 'warning')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/join', methods=['GET', 'POST'])
def join():
    form = JoinForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        name = form.name.data
        # admin = Admin.query.first()
        user_name = User.query.filter_by(username=username).first()
        ahtour = User.query.filter_by(name=name).first()
        email_true = User.query.filter_by(email=email).first()

        if user_name is None:
            if ahtour is None:
                if email_true is None:
                    user = User(username=username, email=email, name=name)
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                    flash('注册成功，快登录试试！', 'info')
                    formlogin = LoginForm()
                    return redirect(url_for('.login'))
                else:
                    flash('邮箱已被注册', 'warning')
                    return redirect_back()
            else:
                flash('该用户名已存在！', 'warning')
                return redirect_back()
        else:
            flash('该账号已存在！', 'warning')
            return redirect_back()
    return render_template('auth/join.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout success.', 'info')
    return redirect_back()