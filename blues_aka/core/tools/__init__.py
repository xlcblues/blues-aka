from blues_aka.core.tools.time_tools import get_current_time, get_current_date
from blues_aka.core.tools.web_search import web_search

# 基础工具集（默认可用）
BASIC_TOOLS = [
    get_current_time,
    get_current_date,
]

# 可选工具集（需要用户明确启用）
OPTIONAL_TOOLS = {
    'web_search': web_search,
}

__all__ = [
    'get_current_time',
    'get_current_date',
    'web_search',
    'BASIC_TOOLS',
    'OPTIONAL_TOOLS',
]