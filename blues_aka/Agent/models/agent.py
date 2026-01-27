from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, JSON, DateTime, func
from blues_aka.extensions import db

class Agent(db.Model):
    __tablename__ = 'agents'

    # 基础字段
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    description = Column(Text)
    avatar = Column(String(255))

    # 配置信息
    model = Column(String(50), default='glm-4.5')
    system_prompt = Column(Text)
    prompt_mode = Column(String(20), default='default')

    # 工具配置
    tools = Column(JSON)  # 存储工具列表

    # 智能体配置
    temperature = Column(DECIMAL(3,2), default=0.7)
    max_tokens = Column(Integer, default=2000)
    top_p = Column(DECIMAL(3,2), default=1.0)

    # 状态信息
    is_public = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)

    # 使用统计
    usage_count = Column(Integer, default=0)
    rating = Column(DECIMAL(3,2))

    # 扩展配置
    config = Column(JSON)

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # rag配置
    enable_rag = Column(Boolean, default=False)
    rag_index_name = Column(String(100))
    rag_config = Column(Text)  # JSON: {"search_type": "similarity", "k": 4}

    # 关系
    user = db.relationship('User', backref=db.backref('agents', lazy='dynamic', cascade='all, delete-orphan'))
    conversations = db.relationship('Conversation', back_populates='agent', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Agent {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'avatar': self.avatar,
            'model': self.model,
            'system_prompt': self.system_prompt,
            'prompt_mode': self.prompt_mode,
            'tools': self.tools,
            'temperature': float(self.temperature) if self.temperature else 0.7,
            'max_tokens': self.max_tokens,
            'top_p': float(self.top_p) if self.top_p else 1.0,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'rating': float(self.rating) if self.rating else None,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'enable_rag': self.enable_rag,
            'rag_index_name': self.rag_index_name,
            'rag_config': self.rag_config
        }

    def increment_usage(self):
        """增加使用次数"""
        self.usage_count = (self.usage_count or 0) + 1
        db.session.commit()