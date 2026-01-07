from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func

from blues_aka.Agent.models.message import Message
from blues_aka.extensions import db

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    agent_id = Column(Integer, db.ForeignKey('agents.id', ondelete='SET NULL'))

    # 对话信息
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # 配置信息
    model = Column(String(50))
    system_prompt = Column(Text)

    # 状态信息
    status = Column(String(20), default='active', index=True)  # active, archived, deleted
    is_pinned = Column(Boolean, default=False)

    # 统计信息
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)

    # 时间戳
    last_message_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 关系
    user = db.relationship('User', backref=db.backref('conversations', lazy='dynamic', cascade='all, delete-orphan'))
    agent = db.relationship('Agent', back_populates='conversations')
    messages = db.relationship('Message', backref=db.backref('conversation', lazy='joined'), cascade='all, delete-orphan', order_by='Message.created_at')

    def __repr__(self):
        return f'<Conversation {self.title}>'

    def to_dict(self, include_agent=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'model': self.model,
            'status': self.status,
            'is_pinned': self.is_pinned,
            'message_count': self.message_count,
            'token_count': self.token_count,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_agent and self.agent:
            data['agent'] = {
                'id': self.agent.id,
                'name': self.agent.name,
                'avatar': self.agent.avatar
            }

        return data

    def update_message_stats(self, token=0):
        """更新消息信息"""
        self.message_count = Message.query.filter_by(conversation_id=self.id).count()
        self.token_count = (self.token_count or 0) + token
        self.last_message_at = func.now()
        db.session.commit()

    def archive(self):
        """归档对话"""
        self.status = 'archived'
        db.session.commit()

    def delete_soft(self):
        """软删除对话"""
        self.status = 'deleted'
        db.session.commit()