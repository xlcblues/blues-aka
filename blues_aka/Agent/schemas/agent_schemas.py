from marshmallow import Schema, fields, validate, validates, ValidationError, EXCLUDE

class CreateAgentSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # 忽略未知字段

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    avatar = fields.Str(allow_none=True, allow_blank=True)
    model = fields.Str(missing='glm-4.5')
    system_prompt = fields.Str(validate=validate.Length(max=10000))
    prompt_mode = fields.Str(missing='default', validate=validate.OneOf(['default', 'coding', 'creative']))
    tools = fields.List(fields.Str(), allow_none=True)  # 允许为None
    temperature = fields.Float(missing=0.7, validate=validate.Range(min=0, max=2))
    max_tokens = fields.Int(missing=2000, validate=validate.Range(min=1, max=32000))
    top_p = fields.Float(missing=1.0, validate=validate.Range(min=0, max=1))
    is_public = fields.Bool(missing=False)
    config = fields.Dict(allow_none=True)  # 允许为None
    # RAG相关字段
    enable_rag = fields.Bool(missing=False)
    rag_index_name = fields.Str(allow_none=True)
    rag_config = fields.Str(allow_none=True)  # JSON字符串
    enable_web_search = fields.Bool(missing=False)
    web_search_config = fields.Str(allow_none=True)  # JSON字符串

class UpdateAgentSchema(Schema):
    class Meta:
        unknown = EXCLUDE  # 忽略未知字段

    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    avatar = fields.Str(allow_none=True, allow_blank=True)
    model = fields.Str()
    system_prompt = fields.Str(validate=validate.Length(max=10000))
    prompt_mode = fields.Str(validate=validate.OneOf(['default', 'coding', 'creative']))
    tools = fields.List(fields.Str(), allow_none=True)  # 允许为None
    temperature = fields.Float(validate=validate.Range(min=0, max=2))
    max_tokens = fields.Int(validate=validate.Range(min=1, max=32000))
    top_p = fields.Float(validate=validate.Range(min=0, max=1))
    is_public = fields.Bool()
    is_active = fields.Bool()
    config = fields.Dict(allow_none=True)  # 允许为None
    # RAG相关字段
    enable_rag = fields.Bool()
    rag_index_name = fields.Str(allow_none=True)
    rag_config = fields.Str(allow_none=True)  # JSON字符串
    enable_web_search = fields.Bool(missing=False)
    web_search_config = fields.Str(allow_none=True)  # JSON字符串