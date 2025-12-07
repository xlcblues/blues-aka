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

