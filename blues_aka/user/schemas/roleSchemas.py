from marshmallow import Schema, fields

class userRoleQuerySchema(Schema):
    username = fields.String()
    role = fields.String()

