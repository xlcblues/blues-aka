from marshmallow import Schema, fields


class userCreateSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    phone = fields.String(allow_none=True)

class userUpdateRespSchema(Schema):
    username = fields.String()
    password = fields.String()
    email = fields.String()
    phone = fields.String(allow_none=True)