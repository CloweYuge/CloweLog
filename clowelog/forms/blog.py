from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from wtforms import StringField, SubmitField, TextAreaField, SelectField, ValidationError
from wtforms.validators import DataRequired, Optional, Length, URL
from clowelog.models import Category


class DescriptionForm(FlaskForm):
    description = TextAreaField('描述', validators=[Optional(), Length(0, 500)])
    submit = SubmitField('提交')


class TagForm(FlaskForm):
    tag = StringField('添加标签（使用空格分隔）', validators=[Optional(), Length(0, 20)])
    submit = SubmitField('添加')


class CommentForm(FlaskForm):
    body = TextAreaField('你想说点啥？', validators=[DataRequired()])
    submit = SubmitField('喷他！')


class CategoryForm(FlaskForm):
    category = StringField('添加分类', validators=[Optional(), Length(0, 20)])
    submit = SubmitField('提交')


class PhotosForm(FlaskForm):
    description = TextAreaField('描述：', validators=[Optional(), Length(0, 250)])
    tag = StringField('标签（使用空格分隔）', validators=[Optional(), Length(0, 20)])
    submit = SubmitField('发布！')


class PostForm(FlaskForm):          # 文章表单
    title = StringField('标题', validators=[DataRequired(), Length(1, 50)])
    category = SelectField('选择分类', coerce=int, default=1)
    body = CKEditorField('正文', validators=[DataRequired()])
    submit = SubmitField('发布')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.with_parent(kwargs['user']).order_by(Category.name).all()]


class LinkForm(FlaskForm):              # 添加链接表单
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    url = StringField('URL', validators=[DataRequired(), URL(), Length(1, 255)])
    submit = SubmitField('提交')
