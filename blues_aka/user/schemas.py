from flask_marshmallow import Marshmallow
from marshmallow import fields, validate
from .models import User

ma = Marshmallow()
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        exclude = ("password_hash",)

    username = fields.String(required=True, validate=validate.Length(min=3))
    password = fields.String(required=True, validate=validate.Length(min=6))
    email = fields.String(required=True, validate=validate.Email())

user_schema = UserSchema()
users_schema = UserSchema(many=True)