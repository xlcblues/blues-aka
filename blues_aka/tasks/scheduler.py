"""
定时任务调度器

配置和管理系统定时任务
"""

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from blues_aka.tasks.user_status_task import (
    cleanup_old_inactive_users,
    get_user_activity_stats,
    update_inactive_users,
)


logger = logging.getLogger(__name__)

# 创建全局调度器实例
scheduler = BackgroundScheduler()


def init_scheduler(app=None):
    """
    初始化定时任务调度器

    Args:
        app: Flask应用实例,如果提供则在应用上下文中运行任务

    Returns:
        BackgroundScheduler: 调度器实例
    """
    if scheduler.running:
        logger.warning("调度器已经在运行中,跳过初始化")
        return scheduler

    # 配置定时任务

    # 任务1: 每天凌晨2点检查用户状态,将30天未登录的用户设置为inactive
    scheduler.add_job(
        func=update_inactive_users,
        trigger=CronTrigger(hour=2, minute=0),  # 每天凌晨2点执行
        id='update_inactive_users',
        name='更新不活跃用户状态',
        args=[30],  # 30天阈值
        replace_existing=True,
        misfire_grace_time=3600,  # 错过执行时间后的宽限期(秒)
    )

    # 任务2: 每周一凌晨3点获取用户活跃度统计
    scheduler.add_job(
        func=get_user_activity_stats,
        trigger=CronTrigger(day_of_week='mon', hour=3, minute=0),  # 每周一凌晨3点
        id='user_activity_stats',
        name='用户活跃度统计',
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # 任务3: 每月1号凌晨4点清理180天未登录的用户(软删除)
    scheduler.add_job(
        func=cleanup_old_inactive_users,
        trigger=CronTrigger(day=1, hour=4, minute=0),  # 每月1号凌晨4点
        id='cleanup_inactive_users',
        name='清理不活跃用户',
        args=[180, True],  # 180天阈值,软删除
        replace_existing=True,
        misfire_grace_time=7200,  # 2小时宽限期
    )

    # 配置错误处理器 - 监听所有事件
    from apscheduler.events import EVENT_ALL
    scheduler.add_listener(
        job_listener,
        EVENT_ALL
    )

    # 启动调度器
    if not scheduler.running:
        # 只在非调试环境下启动
        debug_mode = app.config.get('DEBUG', False) if app else False
        enable_scheduler = os.environ.get('ENABLE_SCHEDULER', 'true').lower() == 'true'

        if not debug_mode or enable_scheduler:
            scheduler.start()
            logger.info("定时任务调度器启动成功")
            logger.info(f"已注册的任务: {len(scheduler.get_jobs())}")
            for job in scheduler.get_jobs():
                logger.info(f"  - {job.id}: {job.name} ({job.next_run_time})")
        else:
            logger.info("调试模式下跳过调度器启动")

    return scheduler


def job_listener(event):
    """
    任务事件监听器

    Args:
        event: APScheduler事件对象
    """
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

    # 只处理作业相关事件
    if not hasattr(event, 'job_id'):
        return

    if event.code == EVENT_JOB_EXECUTED:
        logger.info(f"定时任务执行成功: 任务ID={event.job_id}")
    elif event.code == EVENT_JOB_ERROR:
        logger.error(f"定时任务执行出错: 任务ID={event.job_id}")
    elif event.code == EVENT_JOB_MISSED:
        logger.warning(f"定时任务错过执行: 任务ID={event.job_id}")


def get_scheduled_jobs():
    """
    获取所有已注册的定时任务信息

    Returns:
        list: 任务信息列表
    """
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger': str(job.trigger),
        })
    return jobs


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")


def run_user_status_update_now():
    """
    立即执行用户状态更新任务(用于手动触发)

    Returns:
        dict: 任务执行结果
    """
    logger.info("手动触发用户状态更新任务")
    return update_inactive_users(days_threshold=30)


def run_cleanup_now():
    """
    立即执行用户清理任务(用于手动触发)

    Returns:
        dict: 任务执行结果
    """
    logger.info("手动触发用户清理任务")
    return cleanup_old_inactive_users(days_threshold=180, delete_softly=True)
