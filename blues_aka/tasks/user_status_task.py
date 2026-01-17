"""
用户状态管理定时任务

功能:
- 检查用户最后一次登录时间
- 将超过指定天数未登录的用户状态设置为 inactive
- 可配置的检查间隔和天数阈值
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from blues_aka.extensions import db
from blues_aka.user.models import User


logger = logging.getLogger(__name__)


def update_inactive_users(days_threshold=30):
    """
    将超过指定天数未登录的用户状态设置为 inactive

    Args:
        days_threshold (int): 天数阈值,默认30天

    Returns:
        dict: 更新统计信息
    """
    try:
        # 计算阈值日期
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        # 查找需要更新的用户:
        # - 状态为 active
        # - 最后登录时间早于阈值日期
        # - 或者从未登录过的用户
        users_to_update = User.query.filter(
            User.status == 'active',
            db.or_(
                User.last_login_at < threshold_date,
                User.last_login_at.is_(None)
            )
        ).all()

        if not users_to_update:
            logger.info(f"没有需要更新状态的用户 (阈值: {days_threshold}天)")
            return {
                'updated_count': 0,
                'threshold_days': days_threshold,
                'threshold_date': threshold_date.isoformat()
            }

        # 批量更新用户状态
        updated_count = 0
        for user in users_to_update:
            old_status = user.status
            user.status = 'inactive'
            updated_count += 1
            logger.info(
                f"用户状态更新: ID={user.id}, "
                f"用户名={user.username}, "
                f"旧状态={old_status}, "
                f"新状态={user.status}, "
                f"最后登录={user.last_login_at.isoformat() if user.last_login_at else '从未登录'}"
            )

        # 提交更改
        db.session.commit()

        logger.info(
            f"用户状态更新完成: "
            f"更新了 {updated_count} 个用户为 inactive 状态 "
            f"(阈值: {days_threshold}天, "
            f"最后登录时间早于 {threshold_date.strftime('%Y-%m-%d %H:%M:%S')})"
        )

        return {
            'updated_count': updated_count,
            'threshold_days': days_threshold,
            'threshold_date': threshold_date.isoformat()
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新用户状态时发生错误: {str(e)}", exc_info=True)
        raise


def get_user_activity_stats():
    """
    获取用户活跃度统计信息

    Returns:
        dict: 用户活跃度统计数据
    """
    try:
        # 总用户数
        total_users = User.query.count()

        # 活跃用户数
        active_users = User.query.filter_by(status='active').count()

        # 不活跃用户数
        inactive_users = User.query.filter_by(status='inactive').count()

        # 暂停用户数
        suspended_users = User.query.filter_by(status='suspended').count()

        # 已删除用户数
        deleted_users = User.query.filter_by(status='deleted').count()

        # 最近30天登录的用户
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recently_active = User.query.filter(
            User.last_login_at >= thirty_days_ago
        ).count()

        # 从未登录的用户
        never_logged_in = User.query.filter(
            User.last_login_at.is_(None)
        ).count()

        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'suspended_users': suspended_users,
            'deleted_users': deleted_users,
            'recently_active_30days': recently_active,
            'never_logged_in': never_logged_in,
            'active_rate': f"{(active_users / total_users * 100):.2f}%" if total_users > 0 else "0%"
        }

        logger.info(f"用户活跃度统计: {stats}")
        return stats

    except Exception as e:
        logger.error(f"获取用户活跃度统计时发生错误: {str(e)}", exc_info=True)
        raise


def cleanup_old_inactive_users(days_threshold=180, delete_softly=True):
    """
    清理长时间不活跃的用户

    Args:
        days_threshold (int): 天数阈值,默认180天
        delete_softly (bool): 是否软删除,默认True

    Returns:
        dict: 清理统计信息
    """
    try:
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        # 查找需要清理的用户
        users_to_cleanup = User.query.filter(
            User.status == 'inactive',
            User.last_login_at < threshold_date
        ).all()

        if not users_to_cleanup:
            logger.info(f"没有需要清理的用户 (阈值: {days_threshold}天)")
            return {
                'cleaned_count': 0,
                'threshold_days': days_threshold,
                'delete_softly': delete_softly
            }

        cleaned_count = 0
        for user in users_to_cleanup:
            if delete_softly:
                # 软删除: 标记为 deleted 状态
                user.status = 'deleted'
                cleaned_count += 1
                logger.info(
                    f"用户软删除: ID={user.id}, "
                    f"用户名={user.username}, "
                    f"最后登录={user.last_login_at.isoformat() if user.last_login_at else '从未登录'}"
                )
            else:
                # 硬删除: 从数据库中删除
                db.session.delete(user)
                cleaned_count += 1
                logger.warning(
                    f"用户硬删除: ID={user.id}, "
                    f"用户名={user.username}"
                )

        db.session.commit()

        logger.info(
            f"用户清理完成: "
            f"清理了 {cleaned_count} 个用户 "
            f"(阈值: {days_threshold}天, "
            f"删除方式: {'软删除' if delete_softly else '硬删除'})"
        )

        return {
            'cleaned_count': cleaned_count,
            'threshold_days': days_threshold,
            'delete_softly': delete_softly
        }

    except Exception as e:
        db.session.rollback()
        logger.error(f"清理用户时发生错误: {str(e)}", exc_info=True)
        raise
