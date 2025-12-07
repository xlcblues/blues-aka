from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class userQueryRespSchema(Schema):
    id = fields.Integer()
    username = fields.String()
    email = fields.String()
    nickname = fields.String()
    phone = fields.String()

    status = fields.String()
    is_verified = fields.Boolean()
    is_admin = fields.Boolean()

    failed_login_attempts = fields.Integer()
    locked_until = fields.DateTime()
    last_login_at = fields.DateTime()
    last_login_ip = fields.String()
    login_count = fields.Integer()

    password_changed_at = fields.DateTime()
    email_verified_at = fields.DateTime()
    reset_password_expires = fields.DateTime()

    created_at = fields.DateTime()
    updated_at = fields.DateTime()