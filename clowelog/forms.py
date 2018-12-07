from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, \
    SelectField, ValidationError, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email, URL, Optional

from clowelog.models import Category


class LoginForm(FlaskForm):
    username = StringField('用户名(Username)', validators=[DataRequired(), Length(1, 20)])
    password = PasswordField('密码(Password)', validators=[DataRequired(), Length(8, 128)])
    remember = BooleanField('记住我(Remember me)')
    submit = SubmitField('登入(Log in)')


class SettingForm(FlaskForm):
    name = StringField('标题（Name）', validators=[DataRequired(), Length(1, 70)])
    blog_title = StringField('博客标题（Blog Title）', validators=[DataRequired(), Length(1, 60)])
    blog_sub_title = StringField('博客简介（Blog Sub Title）', validators=[DataRequired(), Length(1, 100)])
    about = CKEditorField('主页（About Page）', validators=[DataRequired()])
    submit = SubmitField()


class PostForm(FlaskForm):
    title = StringField('标题(Title)', validators=[DataRequired(), Length(1, 60)])
    category = SelectField('选择分类(Cateory)', coerce=int, default=1)
    body = CKEditorField('正文(Body)', validators=[DataRequired()])
    submit = SubmitField('提交(Submit)')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.name).all()]


class CategoryForm(FlaskForm):
    name = StringField('类别(Name)', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField()

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('类别已存在(Name already in use.)')


class CommentForm(FlaskForm):
    author = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    email = StringField('邮箱(Email)', validators=[DataRequired(), Email(), Length(1, 254)])
    site = StringField('主页(site)', validators=[Optional(), URL, Length(0, 255)])
    body = TextAreaField('评论(Comment)', validators=[DataRequired()])
    submit = SubmitField()


class AdminCommentForm(CommentForm):
    author = HiddenField()
    email = HiddenField()
    site = HiddenField()


class LinkForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    url = StringField('URL', validators=[DataRequired(), URL(), Length(1, 255)])
    submit = SubmitField()
