"""
定时任务调度器模块

本模块负责配置和管理系统中的所有定时任务,使用APScheduler库实现。

主要功能:
    - 初始化和启动调度器
    - 注册和管理定时任务
    - 监听任务执行事件
    - 提供手动触发任务的接口

任务列表:
    1. update_inactive_users: 每天凌晨2点执行,将30天未登录的用户状态设为inactive
    2. user_activity_stats: 每周一凌晨3点执行,统计用户活跃度数据
    3. cleanup_inactive_users: 每月1号凌晨4点执行,清理180天未登录的用户

环境变量:
    ENABLE_SCHEDULER: 是否启用调度器,默认为true
                      在调试模式下默认不启动,除非显式设置为true

Example:
    >>> from blues_aka import create_app
    >>> app = create_app('development')
    >>> # 调度器会在应用初始化时自动启动
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


# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建全局调度器实例
# 使用BackgroundScheduler在后台线程中运行任务,不会阻塞主线程
scheduler = BackgroundScheduler()


def init_scheduler(app=None):
    """
    初始化定时任务调度器

    本函数会注册所有定时任务并启动调度器。调度器会在后台线程中运行,
    定时执行用户状态管理、数据统计等任务。

    Args:
        app: Flask应用实例。如果提供,会根据应用的配置决定是否启动调度器。
             当app.config['DEBUG']为True时,除非环境变量ENABLE_SCHEDULER
             设置为true,否则不会启动调度器。

    Returns:
        BackgroundScheduler: 已配置的调度器实例。如果调度器已在运行,
                            则直接返回现有实例。

    Note:
        - 调度器使用Cron触发器,支持类似Linux cron的表达式
        - 所有任务都配置了misfire_grace_time,允许在错过计划时间后的一段时间内执行
        - replace_existing=True确保重复调用此函数时不会重复添加任务

    Example:
        >>> from flask import Flask
        >>> from blues_aka.tasks.scheduler import init_scheduler
        >>> app = Flask(__name__)
        >>> scheduler = init_scheduler(app)
        >>> print(f"调度器状态: {'运行中' if scheduler.running else '未启动'}")
    """
    # 检查调度器是否已经运行,避免重复初始化
    if scheduler.running:
        logger.warning("调度器已经在运行中,跳过初始化")
        return scheduler

    # ============================================================
    # 任务1: 用户状态自动更新
    # 用途: 将超过指定天数未登录的用户状态设置为inactive
    # 执行时间: 每天凌晨2:00
    # ============================================================
    scheduler.add_job(
        func=update_inactive_users,                    # 要执行的函数
        trigger=CronTrigger(hour=2, minute=0),         # Cron表达式: 每天凌晨2点
        id='update_inactive_users',                    # 任务唯一标识符
        name='更新不活跃用户状态',                      # 任务描述名称
        args=[30],                                     # 传递给函数的参数: 30天阈值
        replace_existing=True,                         # 如果任务已存在则替换
        misfire_grace_time=3600,                       # 错过执行后1小时内仍执行
    )

    # ============================================================
    # 任务2: 用户活跃度统计
    # 用途: 统计和记录用户活跃度相关数据
    # 执行时间: 每周一凌晨3:00
    # ============================================================
    scheduler.add_job(
        func=get_user_activity_stats,                  # 要执行的函数
        trigger=CronTrigger(day_of_week='mon', hour=3, minute=0),  # 每周一凌晨3点
        id='user_activity_stats',                      # 任务唯一标识符
        name='用户活跃度统计',                          # 任务描述名称
        replace_existing=True,                         # 如果任务已存在则替换
        misfire_grace_time=3600,                       # 错过执行后1小时内仍执行
    )

    # ============================================================
    # 任务3: 长期不活跃用户清理
    # 用途: 清理长时间未登录的用户(软删除)
    # 执行时间: 每月1号凌晨4:00
    # ============================================================
    scheduler.add_job(
        func=cleanup_old_inactive_users,               # 要执行的函数
        trigger=CronTrigger(day=1, hour=4, minute=0),  # 每月1号凌晨4点
        id='cleanup_inactive_users',                   # 任务唯一标识符
        name='清理不活跃用户',                          # 任务描述名称
        args=[180, True],                              # 参数: 180天阈值, 软删除
        replace_existing=True,                         # 如果任务已存在则替换
        misfire_grace_time=7200,                       # 错过执行后2小时内仍执行
    )

    # ============================================================
    # 事件监听器配置
    # 用途: 监听所有任务事件,记录执行日志
    # ============================================================
    from apscheduler.events import EVENT_ALL
    scheduler.add_listener(
        job_listener,                                  # 监听器函数
        EVENT_ALL                                      # 监听所有类型的事件
    )

    # ============================================================
    # 启动调度器
    # ============================================================
    if not scheduler.running:
        # 获取调试模式配置
        debug_mode = app.config.get('DEBUG', False) if app else False

        # 从环境变量获取调度器开关,默认为true
        enable_scheduler = os.environ.get('ENABLE_SCHEDULER', 'true').lower() == 'true'

        # 决定是否启动调度器:
        # 1. 如果不是调试模式,则启动
        # 2. 如果是调试模式但ENABLE_SCHEDULER=true,则也启动
        if not debug_mode or enable_scheduler:
            scheduler.start()
            logger.info("定时任务调度器启动成功")
            logger.info(f"已注册的任务: {len(scheduler.get_jobs())}")

            # 输出每个任务的下次执行时间
            for job in scheduler.get_jobs():
                logger.info(f"  - {job.id}: {job.name} ({job.next_run_time})")
        else:
            logger.debug("调试模式下跳过调度器启动")

    return scheduler


def job_listener(event):
    """
    任务事件监听器函数

    当调度器中的任务发生任何事件时,此函数会被调用。
    主要用于记录任务执行的日志,便于监控和调试。

    Args:
        event: APScheduler事件对象,包含事件的详细信息
               常用属性:
               - code: 事件代码(EVENT_JOB_EXECUTED, EVENT_JOB_ERROR等)
               - job_id: 任务ID
               - scheduled_run_time: 计划执行时间

    Note:
        此函数会过滤掉非作业相关的事件(如调度器启动/关闭事件),
        只处理与具体任务执行相关的事件。

    Example:
        当任务执行成功时,日志会记录:
        INFO - 定时任务执行成功: 任务ID=update_inactive_users
    """
    from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED

    # 过滤非作业事件: 只处理有job_id属性的事件
    # 这样可以忽略调度器级别的启动、关闭等事件
    if not hasattr(event, 'job_id'):
        return

    # 根据事件类型记录不同级别的日志
    if event.code == EVENT_JOB_EXECUTED:
        # 任务成功执行完成
        logger.info(f"定时任务执行成功: 任务ID={event.job_id}")
    elif event.code == EVENT_JOB_ERROR:
        # 任务执行过程中出现错误
        logger.error(f"定时任务执行出错: 任务ID={event.job_id}")
    elif event.code == EVENT_JOB_MISSED:
        # 任务错过了计划执行时间(如调度器停止期间)
        logger.warning(f"定时任务错过执行: 任务ID={event.job_id}")


def get_scheduled_jobs():
    """
    获取所有已注册的定时任务信息

    本函数用于查询当前调度器中所有注册的任务,返回每个任务的基本信息,
    包括任务ID、名称、下次执行时间等。

    Returns:
        list: 任务信息列表,每个元素是一个字典,包含以下字段:
            - id (str): 任务唯一标识符
            - name (str): 任务描述名称
            - next_run_time (str|None): 下次执行时间的ISO格式字符串,如果无下次执行则为None
            - trigger (str): 触发器的字符串表示

    Example:
        >>> jobs = get_scheduled_jobs()
        >>> for job in jobs:
        ...     print(f"{job['name']}: {job['next_run_time']}")
        更新不活跃用户状态: 2026-01-18T02:00:00+08:00
        用户活跃度统计: 2026-01-20T03:00:00+08:00
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
    """
    关闭调度器

    优雅地关闭调度器,停止所有定时任务的执行。
    应在应用关闭时调用此函数,确保资源被正确释放。

    Note:
        - wait=False表示不等待正在执行的任务完成
        - 如果需要等待当前任务完成,使用wait=True
        - 关闭后的调度器需要重新初始化才能再次使用

    Example:
        >>> from blues_aka.tasks.scheduler import shutdown_scheduler
        >>> shutdown_scheduler()
        INFO - 定时任务调度器已关闭
    """
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")


def run_user_status_update_now():
    """
    立即执行用户状态更新任务(用于手动触发)

    本函数允许管理员手动触发用户状态更新任务,而不需要等待定时执行。
    主要用于测试或紧急情况下需要立即更新用户状态。

    Returns:
        dict: 任务执行结果,包含以下字段:
            - updated_count (int): 更新的用户数量
            - threshold_days (int): 使用的天数阈值
            - threshold_date (str): 阈值日期的ISO格式字符串

    Example:
        >>> result = run_user_status_update_now()
        >>> print(f"更新了 {result['updated_count']} 个用户")
        更新了 15 个用户

    Note:
        此函数会更新所有超过30天未登录的active用户状态为inactive
    """
    logger.info("手动触发用户状态更新任务")
    return update_inactive_users(days_threshold=30)


def run_cleanup_now():
    """
    立即执行用户清理任务(用于手动触发)

    本函数允许管理员手动触发用户清理任务,用于清理长时间未登录的用户。
    默认使用软删除方式,将用户状态标记为deleted。

    Returns:
        dict: 任务执行结果,包含以下字段:
            - cleaned_count (int): 清理的用户数量
            - threshold_days (int): 使用的天数阈值
            - delete_softly (bool): 是否使用软删除

    Example:
        >>> result = run_cleanup_now()
        >>> print(f"清理了 {result['cleaned_count']} 个用户")
        清理了 5 个用户

    Note:
        - 此函数默认执行软删除(status='deleted'),不会从数据库中物理删除用户
        - 清理阈值为180天未登录
        - 如需修改阈值,请直接调用cleanup_old_inactive_users函数
    """
    logger.info("手动触发用户清理任务")
    return cleanup_old_inactive_users(days_threshold=180, delete_softly=True)
