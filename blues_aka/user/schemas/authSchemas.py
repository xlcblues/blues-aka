from marshmallow import Schema, fields

class userLoginSchema(Schema):
    username = fields.String()
    password = fields.String()