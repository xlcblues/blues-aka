from sqlalchemy import Column, Integer, String, Text, DECIMAL, JSON, DateTime, ForeignKey, func, Boolean
from blues_aka.extensions import db
from langchain_core.messages import HumanMessage, AIMessage
import logging
import redis
import json
from typing import Optional, List

logger = logging.getLogger(__name__)

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

    reasoning_data = db.Column(db.JSON, comment="推理过程数据（包含 content 和 length）")
    has_reasoning = db.Column(db.Boolean, default=False, comment="是否包含推理信息")

    # 关系
    user = db.relationship('User', backref=db.backref('messages', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Message {self.id} - {self.role}>'

    def to_dict(self):
        data = {
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

        if self.has_reasoning and self.reasoning_data:
            data['reasoning'] = self.reasoning_data

        return data

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
    def get_message_history(
        cls,
        conversation_id: int,
        limit: Optional[int] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True
    ):
        """
        智能获取聊天历史

        优化功能:
        1. 基于 token 数量的智能截断
        2. Redis 缓存支持
        3. 灵活的限制策略

        Args:
            conversation_id: 对话ID
            limit: 最大消息数量限制(默认50,设为None表示不限制)
            max_tokens: 最大token数量限制(默认4000,设为None表示不限制)
            use_cache: 是否使用Redis缓存(默认True)

        Returns:
            list: LangChain消息对象列表 [HumanMessage, AIMessage, ...]

        性能优化:
            - Redis缓存: 避免重复查询数据库
            - 智能截断: 根据token数量控制上下文大小
            - 反向遍历: 优先保留最近的消息

        使用示例:
            # 基础使用 - 使用默认限制(50条消息或4000 tokens)
            history = Message.get_message_history(conversation_id)

            # 自定义消息数量限制
            history = Message.get_message_history(conversation_id, limit=100)

            # 使用token限制
            history = Message.get_message_history(conversation_id, max_tokens=8000)

            # 组合限制(同时满足消息数和token数限制)
            history = Message.get_message_history(conversation_id, limit=100, max_tokens=8000)

            # 禁用缓存
            history = Message.get_message_history(conversation_id, use_cache=False)
        """
        # 设置默认值
        if limit is None:
            limit = 50
        if max_tokens is None:
            max_tokens = 4000

        # 尝试从Redis缓存获取
        if use_cache:
            try:
                from blues_aka.config.config import ConfigFactory
                config = ConfigFactory.get_config()

                if hasattr(config, 'redis_url'):
                    cache_key = f"message_history:{conversation_id}:{limit}:{max_tokens}"

                    try:
                        redis_client = redis.from_url(config.redis_url, decode_responses=True)
                        cached = redis_client.get(cache_key)

                        if cached:
                            logger.debug(f"从缓存获取对话历史: {conversation_id}")
                            cached_data = json.loads(cached)
                            # 重建消息对象
                            history = []
                            for msg_data in cached_data:
                                if msg_data['role'] == 'user':
                                    history.append(HumanMessage(content=msg_data['content']))
                                elif msg_data['role'] == 'assistant':
                                    history.append(AIMessage(content=msg_data['content']))
                            return history
                    except Exception as cache_error:
                        logger.warning(f"Redis缓存读取失败: {cache_error}")
            except Exception as config_error:
                logger.debug(f"未配置Redis或配置读取失败: {config_error}")

        # 从数据库查询
        logger.debug(f"从数据库查询对话历史: conversation_id={conversation_id}")

        # 查询所有消息(不限制数量,后续在Python中智能截断)
        messages = Message.query.filter_by(
            conversation_id=conversation_id,
            is_deleted=False
        ).order_by(Message.created_at.asc()).all()

        # 智能截断: 从最新消息开始,反向添加
        history = []
        total_tokens = 0
        total_messages = 0

        # 从最新的消息开始反向遍历
        for msg in reversed(messages):
            # 检查消息数量限制
            if limit and total_messages >= limit:
                break

            # 估算token数量(中文约1.5 chars per token,英文约4 chars per token)
            # 使用保守估计: 1 token ≈ 2 characters
            msg_tokens = len(msg.content) // 2 + 10  # +10 为消息开销

            # 检查token数量限制
            if max_tokens and total_tokens + msg_tokens > max_tokens:
                logger.info(
                    f"达到token限制: conversation_id={conversation_id}, "
                    f"total_tokens={total_tokens}, max_tokens={max_tokens}"
                )
                break

            # 添加消息到历史(在开头插入,保持时间顺序)
            if msg.role == 'user':
                history.insert(0, HumanMessage(content=msg.content))
            elif msg.role == 'assistant':
                history.insert(0, AIMessage(content=msg.content))

            total_tokens += msg_tokens
            total_messages += 1

        logger.info(
            f"加载对话历史: conversation_id={conversation_id}, "
            f"messages={total_messages}, tokens={total_tokens}"
        )

        # 保存到Redis缓存
        if use_cache and history:
            try:
                from blues_aka.config.config import ConfigFactory
                config = ConfigFactory.get_config()

                if hasattr(config, 'redis_url'):
                    cache_key = f"message_history:{conversation_id}:{limit}:{max_tokens}"
                    cache_ttl = 300  # 5分钟缓存

                    # 序列化历史
                    cache_data = []
                    for msg in history:
                        if isinstance(msg, HumanMessage):
                            cache_data.append({'role': 'user', 'content': msg.content})
                        elif isinstance(msg, AIMessage):
                            cache_data.append({'role': 'assistant', 'content': msg.content})

                    try:
                        redis_client = redis.from_url(config.redis_url, decode_responses=True)
                        redis_client.setex(
                            cache_key,
                            cache_ttl,
                            json.dumps(cache_data, ensure_ascii=False)
                        )
                        logger.debug(f"对话历史已缓存: {conversation_id}")
                    except Exception as cache_error:
                        logger.warning(f"Redis缓存写入失败: {cache_error}")
            except Exception as config_error:
                logger.debug(f"未配置Redis或配置读取失败: {config_error}")

        return history

    @classmethod
    def invalidate_history_cache(cls, conversation_id: int):
        """
        清除指定对话的历史缓存

        当有新消息添加时,应该调用此方法清除缓存

        Args:
            conversation_id: 对话ID
        """
        try:
            from blues_aka.config.config import ConfigFactory
            config = ConfigFactory.get_config()

            if hasattr(config, 'redis_url'):
                redis_client = redis.from_url(config.redis_url, decode_responses=True)

                # 删除所有相关的缓存键
                # 使用模式匹配删除
                for key in redis_client.scan_iter(f"message_history:{conversation_id}:*"):
                    redis_client.delete(key)
                    logger.debug(f"清除缓存: {key}")
        except Exception as e:
            logger.warning(f"清除缓存失败: {e}")