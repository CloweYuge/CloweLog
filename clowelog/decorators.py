from functools import wraps

from flask import Markup, flash, url_for, redirect, abort
from flask_login import current_user
from clowelog.models import Useronline


def confirm_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.confirmed:
            message = Markup(
                '请先验证你的邮箱！'
                '没有搜到邮件吗？'
                '<a class="alert-link" href="%s">重新发送验证邮件</a>' %
                url_for('auth.resend_confirm_email'))
            flash(message, 'warning')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)
    return decorated_function


def permission_required(permission_name):       # 检查权限，传入权限名称，不具有权限返回403错误
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission_name):
                abort(403)
            return func(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(func):                       # 只检查是不是最高管理员
    return permission_required('ADMINISTER')(func)


def online_required(func):
    @wraps(func)
    def clike_function(*args, **kwargs):
        if not current_user.online.ifonline(current_user.id):
            abort(403)                          # 这里只是限制点击次数，应该设置频繁点击的提醒页面
        return func(*args, **kwargs)
    return clike_function
