"""
时间相关工具模块

本模块提供了获取当前时间和日期的工具函数,用于AI助手在对话中提供时间信息。

主要功能:
    - get_current_time: 获取当前系统时间
    - get_current_date: 获取当前系统日期及星期

模块依赖:
    - datetime: Python标准库,用于日期时间处理
    - langchain_core.tools: 用于将函数转换为LangChain工具

使用示例:
    >>> from blues_aka.core.tools.time_tools import get_current_time, get_current_date
    >>> get_current_time.invoke({})
    '当前时间为：2025-01-30 14:30:45'
    >>> get_current_date.invoke({})
    '2025-01-30:星期四'
"""

import logging
from datetime import datetime

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool(description="获取当前时间")
def get_current_time() -> str:
    """
    获取当前系统时间

    该函数获取当前系统时间,并格式化为 '年-月-日 时:分:秒' 的形式返回。
    返回的字符串包含中文描述,便于用户阅读。

    Returns:
        str: 格式化后的当前时间字符串,格式为 '当前时间为：YYYY-MM-DD HH:MM:SS'

    Example:
        >>> get_current_time.invoke({})
        '当前时间为：2025-01-30 14:30:45'

    Note:
        - 使用系统本地时区
        - 时间格式固定为 '%Y-%m-%d %H:%M:%S'
        - 每次调用都会记录日志
    """
    currentTime = datetime.now()
    currentTimeStr = currentTime.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(currentTimeStr)
    return f"当前时间为：{currentTimeStr}"

@tool(description="获取当前日期")
def get_current_date() -> str:
    """
    获取当前系统日期和星期

    该函数获取当前系统日期,并计算对应的星期几。日期格式化为 '年-月-日',
    星期返回中文形式(如'星期一')。两部分用冒号连接返回。

    Returns:
        str: 格式化后的当前日期和星期字符串,格式为 'YYYY-MM-DD:星期X'

    Example:
        >>> get_current_date.invoke({})
        '2025-01-30:星期四'

    Note:
        - 使用系统本地时区
        - 星期返回中文形式(星期一到星期日)
        - 日期格式固定为 '%Y-%m-%d'
        - 每次调用都会记录日志

    Weekday Mapping:
        0: 星期一 (Monday)
        1: 星期二 (Tuesday)
        2: 星期三 (Wednesday)
        3: 星期四 (Thursday)
        4: 星期五 (Friday)
        5: 星期六 (Saturday)
        6: 星期日 (Sunday)
    """
    now = datetime.now()
    currentDate = now.strftime("%Y-%m-%d")
    logger.info(currentDate)

    # 中文星期映射
    weekday_map = {
        0: "星期一",
        1: "星期二",
        2: "星期三",
        3: "星期四",
        4: "星期五",
        5: "星期六",
        6: "星期日",
    }
    weekday = weekday_map[now.weekday()]
    logger.info(weekday)
    result = f"{currentDate}:{weekday}"
    return result