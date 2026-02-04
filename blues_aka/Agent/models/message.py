from sqlalchemy import Column, Integer, String, Text, DECIMAL, JSON, DateTime, ForeignKey, func, Boolean
from blues_aka.extensions import db
from langchain_core.messages import HumanMessage, AIMessage

class Message(db.Model):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(Integer, db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)

    # 消息内容
    role = Column(String(20), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)

    # 元数据
    model = Column(String(50))
    tokens = Column(Integer)
    cost = Column(DECIMAL(10, 6))

    # 工具调用记录
    tool_calls = Column(JSON)

    # 反馈
    feedback = Column(Integer)  # 1-5
    feedback_text = Column(Text)

    # 状态
    status = Column(String(20), default='sent')  # sent, pending, failed

    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True, index=True)  # 软删除时间戳

    is_deleted = Column(Boolean, default=False, index=True)

    # 关系
    user = db.relationship('User', backref=db.backref('messages', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Message {self.id} - {self.role}>'

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'model': self.model,
            'tokens': self.tokens,
            'cost': float(self.cost) if self.cost else None,
            'tool_calls': self.tool_calls,
            'feedback': self.feedback,
            'feedback_text': self.feedback_text,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def add_feedback(self, rating, feedback_text=None):
        """添加反馈"""
        self.feedback = rating
        self.feedback_text = feedback_text
        # 注意: 不在这里 commit,由调用者负责事务管理

    def soft_delete(self):
        """
        软删除消息
        将消息标记为已删除,并记录删除时间
        """
        self.is_deleted = True
        self.deleted_at = func.now()
        # 注意: 不在这里 commit,由调用者负责事务管理

    def restore(self):
        """
        恢复已软删除的消息
        """
        self.is_deleted = False
        self.deleted_at = None
        # 注意: 不在这里 commit,由调用者负责事务管理

    @property
    def is_deleted_property(self):
        """
        检查消息是否已被软删除
        """
        return self.is_deleted or self.deleted_at is not None

    @classmethod
    def get_message_history(cls, conversation_id, limit=50):
        """获取聊天历史，用于传递给AI"""
        message_history = Message.query.filter_by(
            conversation_id=conversation_id,
            is_deleted=False
        ).order_by(Message.created_at.asc()).limit(limit).all()
        history = []
        for msg in message_history:
            if msg.role == 'user':
                history.append(HumanMessage(content=msg.content))
            elif msg.role == 'assistant':
                history.append(AIMessage(content=msg.content))
        return history