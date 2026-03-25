"""
对话统计更新异步任务模块

本模块提供对话统计信息的异步更新功能，用于在流式响应完成后更新对话的统计数据。
主要解决在流式响应生成器中进行数据库操作可能导致的连接问题和性能问题。

主要功能:
    - 异步更新对话消息数量
    - 更新对话最后消息时间
    - 支持批量更新以提高性能

使用场景:
    1. 流式响应完成后异步更新统计信息
    2. 批量更新多个对话的统计数据
    3. 定期同步和修复统计数据

设计原则:
    - 不在生成器中进行数据库操作
    - 使用后台线程处理统计更新
    - 失败时记录日志但不影响主流程
"""

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from blues_aka.extensions import db
from blues_aka.Agent.models.conversation import Conversation
from blues_aka.Agent.models.message import Message


# 配置日志记录器
logger = logging.getLogger(__name__)


def update_conversation_stats_async(conversation_id: int) -> bool:
    """
    异步更新对话统计信息

    本函数用于在流式响应完成后更新对话的统计数据（消息数量、Token数量和最后消息时间）。
    设计为异步执行，不会阻塞主流程或流式响应。

    Args:
        conversation_id (int): 对话ID，指定要更新的对话

    Returns:
        bool: 更新是否成功
            - True: 更新成功
            - False: 更新失败（对话不存在或数据库错误）

    Note:
        - 查询并更新指定对话的消息数量、Token数量和最后消息时间
        - Token数量通过估算消息内容长度计算（1 token ≈ 2 characters）
        - 如果对话不存在，记录警告日志并返回False
        - 如果数据库操作失败，记录错误日志并返回False
        - 失败不影响主流程，只记录日志

    Example:
        >>> success = update_conversation_stats_async(conversation_id=123)
        >>> if success:
        ...     print("统计信息更新成功")
        ... else:
        ...     print("统计信息更新失败")
        统计信息更新成功

    See Also:
        - update_conversation_stats_batch: 批量更新多个对话
    """
    try:
        # ============================================================
        # 步骤1: 查询对话是否存在
        # ============================================================
        conversation = Conversation.query.get(conversation_id)

        if not conversation:
            logger.warning(f"对话不存在，无法更新统计信息: conversation_id={conversation_id}")
            return False

        # ============================================================
        # 步骤2: 计算消息数量
        # ============================================================
        message_count = Message.query.filter_by(conversation_id=conversation_id).count()

        # ============================================================
        # 步骤2.5: 计算Token总数
        # ============================================================
        # 获取所有消息并估算token数量（1 token ≈ 2 characters，保守估计）
        messages = Message.query.filter_by(conversation_id=conversation_id).all()
        total_tokens = sum(len(msg.content) // 2 for msg in messages if msg.content)

        # ============================================================
        # 步骤3: 更新对话统计信息
        # ============================================================
        conversation.message_count = message_count
        conversation.token_count = total_tokens
        conversation.last_message_at = func.now()

        # ============================================================
        # 步骤4: 提交更改到数据库
        # ============================================================
        db.session.add(conversation)
        db.session.commit()

        logger.info(
            f"对话统计信息更新成功: conversation_id={conversation_id}, "
            f"message_count={message_count}, token_count={total_tokens}"
        )

        return True

    except SQLAlchemyError as e:
        # 数据库错误时回滚事务
        db.session.rollback()
        logger.error(
            f"更新对话统计信息时发生数据库错误: "
            f"conversation_id={conversation_id}, error={str(e)}",
            exc_info=True
        )
        return False

    except Exception as e:
        # 其他未知错误
        db.session.rollback()
        logger.error(
            f"更新对话统计信息时发生未知错误: "
            f"conversation_id={conversation_id}, error={str(e)}",
            exc_info=True
        )
        return False


def update_conversation_stats_batch(conversation_ids: list) -> dict:
    """
    批量更新多个对话的统计信息

    本函数用于批量更新多个对话的统计数据，提供比单个更新更好的性能。
    适用于需要同时更新多个对话统计信息的场景。

    Args:
        conversation_ids (list): 对话ID列表，指定要更新的所有对话

    Returns:
        dict: 批量更新统计信息，包含以下字段:
            - total (int): 总共需要更新的对话数量
            - success (int): 成功更新的对话数量
            - failed (int): 更新失败的对话数量
            - failed_ids (list): 更新失败的对话ID列表

    Note:
        - 遍历对话ID列表，逐个更新统计信息
        - 记录每个对话的更新结果
        - 即使部分更新失败，也会继续处理其他对话
        - 最终返回详细的统计结果

    Example:
        >>> result = update_conversation_stats_batch([123, 456, 789])
        >>> print(f"成功: {result['success']}, 失败: {result['failed']}")
        成功: 2, 失败: 1
        >>> if result['failed_ids']:
        ...     print(f"失败的对话ID: {result['failed_ids']}")
        失败的对话ID: [789]

    See Also:
        - update_conversation_stats_async: 更新单个对话统计
    """
    total = len(conversation_ids)
    success_count = 0
    failed_count = 0
    failed_ids = []

    logger.info(f"开始批量更新对话统计信息，共 {total} 个对话")

    for conversation_id in conversation_ids:
        try:
            # 尝试更新单个对话统计
            if update_conversation_stats_async(conversation_id):
                success_count += 1
            else:
                failed_count += 1
                failed_ids.append(conversation_id)

        except Exception as e:
            # 记录单个对话更新失败，但继续处理其他对话
            failed_count += 1
            failed_ids.append(conversation_id)
            logger.error(
                f"批量更新中单个对话失败: conversation_id={conversation_id}, error={str(e)}",
                exc_info=True
            )

    # 记录批量更新汇总日志
    logger.info(
        f"批量更新对话统计信息完成: "
        f"总数={total}, 成功={success_count}, 失败={failed_count}"
    )

    return {
        'total': total,
        'success': success_count,
        'failed': failed_count,
        'failed_ids': failed_ids
    }


def sync_all_conversation_stats() -> dict:
    """
    同步所有对话的统计信息

    本函数会遍历所有对话，重新计算并更新每个对话的消息数量和最后消息时间。
    用于修复统计数据不一致的情况，或定期同步以确保数据准确性。

    Returns:
        dict: 同步统计信息，包含以下字段:
            - total (int): 对话总数
            - success (int): 成功同步的对话数量
            - failed (int): 同步失败的对话数量

    Note:
        - 查询所有对话记录
        - 对每个对话重新计算消息数量
        - 更新最后消息时间为数据库中实际值
        - 适用于数据修复或定期维护

    Warning:
        - 如果对话数量很多，此操作可能需要较长时间
        - 建议在低峰期执行，避免影响正常业务
        - 可能消耗较多数据库资源

    Example:
        >>> result = sync_all_conversation_stats()
        >>> print(f"同步完成: 成功 {result['success']}/{result['total']}")
        同步完成: 成功 145/150

    See Also:
        - update_conversation_stats_async: 更新单个对话
        - update_conversation_stats_batch: 批量更新
    """
    try:
        # ============================================================
        # 步骤1: 查询所有对话
        # ============================================================
        all_conversations = Conversation.query.all()
        total = len(all_conversations)

        logger.info(f"开始同步所有对话统计信息，共 {total} 个对话")

        # ============================================================
        # 步骤2: 遍历并更新每个对话
        # ============================================================
        success_count = 0
        failed_count = 0

        for conversation in all_conversations:
            try:
                # 计算消息数量
                message_count = Message.query.filter_by(
                    conversation_id=conversation.id
                ).count()

                # 更新统计信息
                conversation.message_count = message_count
                db.session.add(conversation)

                success_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"同步对话统计失败: conversation_id={conversation.id}, error={str(e)}",
                    exc_info=True
                )

        # ============================================================
        # 步骤3: 批量提交所有更改
        # ============================================================
        db.session.commit()

        logger.info(
            f"同步所有对话统计信息完成: "
            f"总数={total}, 成功={success_count}, 失败={failed_count}"
        )

        return {
            'total': total,
            'success': success_count,
            'failed': failed_count
        }

    except SQLAlchemyError as e:
        # 数据库错误时回滚事务
        db.session.rollback()
        logger.error(f"同步对话统计时发生数据库错误: {str(e)}", exc_info=True)
        raise

    except Exception as e:
        # 其他未知错误
        db.session.rollback()
        logger.error(f"同步对话统计时发生未知错误: {str(e)}", exc_info=True)
        raise
