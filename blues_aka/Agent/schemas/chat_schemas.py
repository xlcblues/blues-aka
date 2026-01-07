from marshmallow import Schema, fields, validate, ValidationError, validates


class CreateConversationSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    agent_id = fields.Int()
    description = fields.Str(validate=validate.Length(max=1000))
    model = fields.Str()

    @validates('agent_id')
    def validate_agent_id(self, value):
        if value is not None:
            from blues_aka.Agent.models.agent import Agent
            if not Agent.query.get(value):
                raise ValidationError("智能体不存在")

class ChatSchema(Schema):
    content = fields.Str(required=True, validate=validate.Length(min=1, max=10000))
    stream = fields.Bool(missing=False)