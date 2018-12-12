from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    SelectField, ValidationError, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email, URL, Optional

from clowelog.models import Category


class LoginForm(FlaskForm):         # 登录表单
    username = StringField('用户名(Username)', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码(Password)', validators=[DataRequired(), Length(8, 128)])
    remember = BooleanField('记住我(Remember me)')
    submit = SubmitField('登入(Log in)')


class JoinForm(FlaskForm):
    username = StringField('用户名(将用于登录)', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码(设置至少8位以上)', validators=[DataRequired(), Length(8, 128)])
    name = StringField('昵称', validators=[DataRequired(), Length(1, 20)])
    email = StringField('邮箱(用于密码找回)', validators=[DataRequired(), Email(), Length(1, 254)])
    submit = SubmitField('提交')

class SettingForm(FlaskForm):       # 设置表单
    name = StringField('昵称', validators=[DataRequired(), Length(1, 60)])
    blog_title = StringField('博客标题', validators=[DataRequired(), Length(1, 60)])
    blog_sub_title = StringField('博客简介', validators=[DataRequired(), Length(1, 100)])
    about = CKEditorField('说明', validators=[DataRequired()])
    submit = SubmitField('提交')


class PostForm(FlaskForm):          # 文章表单
    title = StringField('标题(Title)', validators=[DataRequired(), Length(1, 60)])
    category = SelectField('选择分类(Cateory)', coerce=int, default=1)
    body = CKEditorField('正文(Body)', validators=[DataRequired()])
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.name).all()]


class CategoryForm(FlaskForm):          # 分类表单
    name = StringField('分类名称(Name)', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField('提交')

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('类别已存在(Name already in use.)')


class CommentForm(FlaskForm):           # 评论表单
    # author = StringField('昵称', validators=[DataRequired(), Length(1, 30)])
    # email = StringField('邮箱', validators=[DataRequired(), Email(), Length(1, 254)])
    # site = StringField('主页', validators=[Optional(), URL, Length(0, 255)])
    body = TextAreaField('你想说的', validators=[DataRequired()])
    submit = SubmitField('提交')


class AdminCommentForm(CommentForm):        # 登录评论表单
    author = HiddenField()
    email = HiddenField()
    site = HiddenField()


class LinkForm(FlaskForm):              # 添加链接表单
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    url = StringField('URL', validators=[DataRequired(), URL(), Length(1, 255)])
    submit = SubmitField('提交')
