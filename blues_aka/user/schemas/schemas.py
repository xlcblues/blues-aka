from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class userQuerySchema(Schema):
    # 查询参数
    id = fields.Integer()
    username = fields.String()
    email = fields.String()

    # 分页参数
    page = fields.Integer(validate=validate.Range(min=1))
    per_page = fields.Integer(validate=validate.Range(min=1, max=100))
    sort_by = fields.String(validate=validate.OneOf(['id', 'username', 'email']))
    order_by = fields.String(validate=validate.OneOf(['asc', 'desc']))

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

class userCreateSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    phone = fields.String(allow_none=True)

class userCreateRespSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    phone = fields.String(allow_none=True)

class userUpdateSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    phone = fields.String(allow_none=True)

class userUpdateRespSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    phone = fields.String(allow_none=True)