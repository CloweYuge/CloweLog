from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp

from clowelog.models import User


class EditProfileForm(FlaskForm):
    name = StringField('昵称', validators=[DataRequired(), Length(1, 30)])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 20),
                                              Regexp('^[a-zA-Z0-9]*$', message='用户名需要包含大小写字母和数字')])
    website = StringField('主页', validators=[Optional(), Length(0, 255)])
    location = StringField('所在地', validators=[Optional(), Length(0, 50)])
    bio = TextAreaField('说明', validators=[Optional(), Length(0, 120)])
    submit = SubmitField('提交')

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('已经被别人用过的用户名，你还想要用吗？')

    def validate_name(self, field):
        if field.data != current_user.name and User.query.filter_by(name=field.data).first():
            raise ValidationError('该昵称已被别人用过了，你还要用吗？')


class UploadAvatarForm(FlaskForm):
    image = FileField('Upload', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], '请上传.jpg或.png格式文件')
    ])
    submit = SubmitField('上传')


class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField('剪裁后提交新头像~')


class ChangeEmailForm(FlaskForm):
    email = StringField('新Email地址', validators=[DataRequired(), Length(1, 254), Email(message='输入正确的邮箱地址！')])
    submit = SubmitField()


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('更改')


class NotificationSettingForm(FlaskForm):
    receive_comment_notification = BooleanField('新的评论')
    receive_follow_notification = BooleanField('新的关注')
    receive_collect_notification = BooleanField('新的收藏')
    submit = SubmitField('设置')


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('公开我的收藏列表')
    submit = SubmitField('设置')


class DeleteAccountForm(FlaskForm):
    username = StringField('确认删除的用户名！！', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField('确认')

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError('你确定你输对了？开什么玩笑，要删删你自己的=，=')