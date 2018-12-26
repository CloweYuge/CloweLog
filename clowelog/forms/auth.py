from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp

from clowelog.models import User


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember = BooleanField('记住我')
    submit = SubmitField('Log in')


class JoinForm(FlaskForm):
    name = StringField('昵称', validators=[DataRequired(), Length(5, 30, message='长度为5-30位字符')])
    email = StringField('Email', validators=[DataRequired(), Length(1, 254),
                                             Email(message='请输入正确的邮箱地址！')])
    username = StringField(
        '用户名', validators=[DataRequired(), Length(5, 20, message='长度为5-20位字符'),
                           Regexp('^[a-zA-Z0-9]*$', message='用户名由英文字母和数字组成！')])
    password = PasswordField('密码', validators=[
        DataRequired(), Length(8, 128,message='密码长度需要在8-128位之间'), 
        EqualTo('password2', message='密码不一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).first():
            raise ValidationError('该昵称已被使用')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被使用')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')


class ForgetPasswordForm(FlaskForm):        # 忘记密码
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()


class ResetPasswordForm(FlaskForm):         # 重置密码
    email = StringField('Email', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField('新密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField()
