"""
用户状态管理定时任务模块

本模块提供用户状态自动管理的核心功能,包括用户活跃度检查、状态更新和清理。
通常由调度器定时调用,也可手动触发执行。

主要功能:
    - 自动将长时间未登录的用户状态设置为inactive
    - 统计和分析用户活跃度数据
    - 清理长期不活跃的用户(支持软删除和硬删除)

用户状态说明:
    - active: 活跃用户,最近有登录记录
    - inactive: 不活跃用户,超过一定时间未登录
    - suspended: 暂停用户,被管理员暂停
    - deleted: 已删除用户,软删除状态

使用场景:
    1. 定期任务: 每天凌晨自动更新不活跃用户
    2. 数据统计: 每周统计用户活跃度
    3. 数据清理: 每月清理长期不活跃用户
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func

from blues_aka.extensions import db
from blues_aka.user.models import User


# 配置日志记录器
logger = logging.getLogger(__name__)


def update_inactive_users(days_threshold=30):
    """
    将超过指定天数未登录的用户状态设置为 inactive

    本函数会查询所有状态为active但超过指定天数未登录的用户,
    并将其状态更新为inactive。这是定时任务系统的核心功能之一。

    Args:
        days_threshold (int): 天数阈值,默认30天。
                              超过此天数未登录的active用户会被更新为inactive。

    Returns:
        dict: 更新统计信息,包含以下字段:
            - updated_count (int): 实际更新的用户数量
            - threshold_days (int): 使用的天数阈值
            - threshold_date (str): 阈值日期的ISO格式字符串

    Raises:
        Exception: 当数据库操作失败时抛出异常

    Note:
        - 查询条件: status='active' AND (last_login_at < threshold_date OR last_login_at IS NULL)
        - 包含从未登录过的用户(last_login_at IS NULL)
        - 每个更新操作都会记录详细日志

    Example:
        >>> result = update_inactive_users(days_threshold=30)
        >>> print(f"更新了 {result['updated_count']} 个用户")
        更新了 15 个用户
        >>> # 日志示例:
        # INFO - 用户状态更新: ID=123, 用户名=john_doe, 旧状态=active, 新状态=inactive, 最后登录=2024-12-10T15:30:00
        # INFO - 用户状态更新完成: 更新了 15 个用户为 inactive 状态 (阈值: 30天)

    See Also:
        - cleanup_old_inactive_users: 清理长期不活跃用户
        - get_user_activity_stats: 获取用户活跃度统计
    """
    try:
        # ============================================================
        # 步骤1: 计算阈值日期
        # ============================================================
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        # ============================================================
        # 步骤2: 查询需要更新的用户
        # 查询条件:
        #   1. 用户状态为 'active'
        #   2. 最后登录时间早于阈值日期, 或者 从未登录过
        # ============================================================
        users_to_update = User.query.filter(
            User.status == 'active',
            db.or_(
                User.last_login_at < threshold_date,
                User.last_login_at.is_(None)
            )
        ).all()

        # ============================================================
        # 步骤3: 如果没有需要更新的用户,返回空结果
        # ============================================================
        if not users_to_update:
            logger.info(f"没有需要更新状态的用户 (阈值: {days_threshold}天)")
            return {
                'updated_count': 0,
                'threshold_days': days_threshold,
                'threshold_date': threshold_date.isoformat()
            }

        # ============================================================
        # 步骤4: 批量更新用户状态
        # ============================================================
        updated_count = 0
        for user in users_to_update:
            old_status = user.status
            user.status = 'inactive'
            updated_count += 1

            # 记录每个用户的更新详情
            logger.info(
                f"用户状态更新: ID={user.id}, "
                f"用户名={user.username}, "
                f"旧状态={old_status}, "
                f"新状态={user.status}, "
                f"最后登录={user.last_login_at.isoformat() if user.last_login_at else '从未登录'}"
            )

        # ============================================================
        # 步骤5: 提交更改到数据库
        # ============================================================
        db.session.commit()

        # 记录汇总日志
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
        # 发生错误时回滚数据库事务
        db.session.rollback()
        logger.error(f"更新用户状态时发生错误: {str(e)}", exc_info=True)
        raise


def get_user_activity_stats():
    """
    获取用户活跃度统计信息

    本函数统计和分析用户活跃度数据,提供多维度的用户统计报告。
    可以用于监控用户活跃情况、生成报表或进行数据分析。

    Returns:
        dict: 用户活跃度统计数据,包含以下字段:
            - total_users (int): 总用户数
            - active_users (int): 活跃用户数(status='active')
            - inactive_users (int): 不活跃用户数(status='inactive')
            - suspended_users (int): 暂停用户数(status='suspended')
            - deleted_users (int): 已删除用户数(status='deleted')
            - recently_active_30days (int): 最近30天登录的用户数
            - never_logged_in (int): 从未登录的用户数
            - active_rate (str): 活跃用户百分比(格式: "65.00%")

    Raises:
        Exception: 当数据库查询失败时抛出异常

    Note:
        - 活跃率计算: (active_users / total_users) * 100
        - 当总用户数为0时,活跃率返回"0%"
        - 所有统计都是实时查询,不使用缓存

    Example:
        >>> stats = get_user_activity_stats()
        >>> print(f"总用户: {stats['total_users']}")
        >>> print(f"活跃用户: {stats['active_users']}")
        >>> print(f"活跃率: {stats['active_rate']}")
        总用户: 1000
        活跃用户: 650
        活跃率: 65.00%

    See Also:
        - update_inactive_users: 更新不活跃用户状态
    """
    try:
        # ============================================================
        # 步骤1: 统计各状态用户数量
        # ============================================================
        total_users = User.query.count()                          # 总用户数
        active_users = User.query.filter_by(status='active').count()       # 活跃用户
        inactive_users = User.query.filter_by(status='inactive').count()   # 不活跃用户
        suspended_users = User.query.filter_by(status='suspended').count() # 暂停用户
        deleted_users = User.query.filter_by(status='deleted').count()     # 已删除用户

        # ============================================================
        # 步骤2: 统计登录时间相关数据
        # ============================================================
        # 最近30天登录的用户
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recently_active = User.query.filter(
            User.last_login_at >= thirty_days_ago
        ).count()

        # 从未登录的用户
        never_logged_in = User.query.filter(
            User.last_login_at.is_(None)
        ).count()

        # ============================================================
        # 步骤3: 计算活跃率并组装结果
        # ============================================================
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

    本函数用于清理长时间未登录的不活跃用户,支持软删除和硬删除两种方式。
    软删除只是将用户状态标记为deleted,硬删除则从数据库中彻底删除记录。

    Args:
        days_threshold (int): 天数阈值,默认180天。
                              超过此天数未登录的inactive用户会被清理。
        delete_softly (bool): 是否使用软删除,默认True。
                             - True: 软删除,仅将status改为'deleted'
                             - False: 硬删除,从数据库中删除记录

    Returns:
        dict: 清理统计信息,包含以下字段:
            - cleaned_count (int): 实际清理的用户数量
            - threshold_days (int): 使用的天数阈值
            - delete_softly (bool): 使用的删除方式

    Raises:
        Exception: 当数据库操作失败时抛出异常

    Warning:
        - 硬删除操作不可逆,会永久删除用户数据
        - 硬删除可能导致外键约束错误(如果有关联数据)
        - 生产环境建议使用软删除

    Note:
        - 只清理状态为'inactive'的用户
        - 查询条件: status='inactive' AND last_login_at < threshold_date
        - 软删除是推荐方式,便于数据恢复和审计

    Example:
        >>> # 软删除示例(推荐)
        >>> result = cleanup_old_inactive_users(days_threshold=180, delete_softly=True)
        >>> print(f"软删除了 {result['cleaned_count']} 个用户")
        软删除了 5 个用户

        >>> # 硬删除示例(谨慎使用)
        >>> result = cleanup_old_inactive_users(days_threshold=180, delete_softly=False)
        >>> print(f"硬删除了 {result['cleaned_count']} 个用户")
        硬删除了 5 个用户

    See Also:
        - update_inactive_users: 更新不活跃用户状态
        - get_user_activity_stats: 获取用户活跃度统计
    """
    try:
        # ============================================================
        # 步骤1: 计算阈值日期
        # ============================================================
        threshold_date = datetime.now() - timedelta(days=days_threshold)

        # ============================================================
        # 步骤2: 查询需要清理的用户
        # 查询条件:
        #   1. 用户状态为 'inactive'
        #   2. 最后登录时间早于阈值日期
        # ============================================================
        users_to_cleanup = User.query.filter(
            User.status == 'inactive',
            User.last_login_at < threshold_date
        ).all()

        # ============================================================
        # 步骤3: 如果没有需要清理的用户,返回空结果
        # ============================================================
        if not users_to_cleanup:
            logger.info(f"没有需要清理的用户 (阈值: {days_threshold}天)")
            return {
                'cleaned_count': 0,
                'threshold_days': days_threshold,
                'delete_softly': delete_softly
            }

        # ============================================================
        # 步骤4: 执行清理操作
        # ============================================================
        cleaned_count = 0
        for user in users_to_cleanup:
            if delete_softly:
                # 软删除: 仅标记用户状态为deleted,不删除数据
                user.status = 'deleted'
                cleaned_count += 1
                logger.info(
                    f"用户软删除: ID={user.id}, "
                    f"用户名={user.username}, "
                    f"最后登录={user.last_login_at.isoformat() if user.last_login_at else '从未登录'}"
                )
            else:
                # 硬删除: 从数据库中彻底删除记录(不可逆)
                db.session.delete(user)
                cleaned_count += 1
                logger.warning(
                    f"用户硬删除: ID={user.id}, "
                    f"用户名={user.username}"
                )

        # ============================================================
        # 步骤5: 提交更改到数据库
        # ============================================================
        db.session.commit()

        # 记录汇总日志
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
        # 发生错误时回滚数据库事务
        db.session.rollback()
        logger.error(f"清理用户时发生错误: {str(e)}", exc_info=True)
        raise
