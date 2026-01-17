"""
定时任务管理接口

提供手动触发和管理定时任务的REST API
"""

import logging

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from blues_aka.common.exception import BusinessException
from blues_aka.common.response import success
from blues_aka.common.responseapi import handle_api_response
from blues_aka.tasks.scheduler import (
    get_scheduled_jobs,
    run_cleanup_now,
    run_user_status_update_now,
)
from blues_aka.tasks.user_status_task import get_user_activity_stats
from blues_aka.user.models import User


logger = logging.getLogger(__name__)
tasks_bp = Blueprint('tasks', __name__, url_prefix='/admin/tasks')


@tasks_bp.route('/jobs', methods=['GET'])
@handle_api_response
@jwt_required()
def get_jobs():
    """
    获取所有定时任务信息

    需要管理员权限
    """
    try:
        # TODO: 添加管理员权限检查
        # current_user_id = get_jwt_identity()
        # user = User.query.get(current_user_id)
        # if not user or not user.is_admin:
        #     raise BusinessException(403, "权限不足", "FORBIDDEN")

        jobs = get_scheduled_jobs()
        return success(data=jobs, message='获取定时任务列表成功')

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {str(e)}", exc_info=True)
        raise BusinessException(500, "获取定时任务列表失败", "GET_JOBS_FAILED")


@tasks_bp.route('/update-user-status', methods=['POST'])
@handle_api_response
@jwt_required()
def update_user_status():
    """
    手动触发用户状态更新任务

    将30天未登录的用户状态设置为inactive

    需要管理员权限
    """
    try:
        # TODO: 添加管理员权限检查
        # current_user_id = get_jwt_identity()
        # user = User.query.get(current_user_id)
        # if not user or not user.is_admin:
        #     raise BusinessException(403, "权限不足", "FORBIDDEN")

        result = run_user_status_update_now()
        return success(data=result, message='用户状态更新任务执行成功')

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"执行用户状态更新任务失败: {str(e)}", exc_info=True)
        raise BusinessException(500, "执行用户状态更新任务失败", "TASK_EXECUTION_FAILED")


@tasks_bp.route('/cleanup-users', methods=['POST'])
@handle_api_response
@jwt_required()
def cleanup_users():
    """
    手动触发用户清理任务

    清理180天未登录的用户(软删除)

    需要管理员权限
    """
    try:
        # TODO: 添加管理员权限检查
        # current_user_id = get_jwt_identity()
        # user = User.query.get(current_user_id)
        # if not user or not user.is_admin:
        #     raise BusinessException(403, "权限不足", "FORBIDDEN")

        result = run_cleanup_now()
        return success(data=result, message='用户清理任务执行成功')

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"执行用户清理任务失败: {str(e)}", exc_info=True)
        raise BusinessException(500, "执行用户清理任务失败", "TASK_EXECUTION_FAILED")


@tasks_bp.route('/user-stats', methods=['GET'])
@handle_api_response
@jwt_required()
def get_stats():
    """
    获取用户活跃度统计信息

    需要管理员权限
    """
    try:
        # TODO: 添加管理员权限检查
        # current_user_id = get_jwt_identity()
        # user = User.query.get(current_user_id)
        # if not user or not user.is_admin:
        #     raise BusinessException(403, "权限不足", "FORBIDDEN")

        stats = get_user_activity_stats()
        return success(data=stats, message='获取用户统计信息成功')

    except BusinessException as e:
        raise e
    except Exception as e:
        logger.error(f"获取用户统计信息失败: {str(e)}", exc_info=True)
        raise BusinessException(500, "获取用户统计信息失败", "GET_STATS_FAILED")
