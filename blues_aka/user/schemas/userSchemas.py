from marshmallow import Schema, fields, validate, validates_schema, ValidationError

class userQuerySchema(Schema):
    # 查询参数 - 添加长度限制以防止ReDoS攻击和数据库资源消耗
    id = fields.Integer()
    username = fields.String(validate=validate.Length(max=50))
    email = fields.String(validate=validate.Length(max=100))
    nickname = fields.String(validate=validate.Length(max=100))
    phone = fields.String(validate=validate.Length(max=20))

    # 分页参数
    page = fields.Integer(validate=validate.Range(min=1))
    per_page = fields.Integer(validate=validate.Range(min=1, max=100))
    # 允许排序的字段（与路由中的 ALLOWED_SORT_FIELDS 保持一致）
    sort_by = fields.String(validate=validate.OneOf([
        'id', 'username', 'email', 'nickname',
        'phone', 'role', 'status', 'created_at', 'updated_at'
    ]))
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
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': '用户名不能为空'}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6),
        error_messages={'required': '密码不能为空'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': '邮箱不能为空'}
    )
    nickname = fields.String(
        validate=validate.Length(max=100),
        missing=None  # 默认值为 None
    )
    phone = fields.String(
        allow_none=True,
        validate=validate.Length(max=20),
        missing=None
    )

class userCreateRespSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    nickname = fields.String()
    phone = fields.String(allow_none=True)

class userUpdateSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    nickname = fields.String()
    phone = fields.String(allow_none=True)

class userUpdateRespSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    nickname = fields.String()
    phone = fields.String(allow_none=True)