import logging
from datetime import datetime

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool(description="获取当前时间")
def get_current_time() -> str:
    currentTime = datetime.now()
    currentTimeStr = currentTime.strftime("%Y-%m-%d %H:%M:%S")
    logger.info(currentTimeStr)
    return f"当前时间为：{currentTimeStr}"

@tool(description="获取当前日期")
def get_current_date() -> str:
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