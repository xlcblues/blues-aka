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
# 所有可用工具的注册表
ALL_AVAILABLE_TOOLS = {
    'get_current_time': get_current_time,
    'get_current_date': get_current_date,
    'web_search': web_search,
}

__all__ = [
    'get_current_time',
    'get_current_date',
    'web_search',
    'BASIC_TOOLS',
    'OPTIONAL_TOOLS',
    'ALL_AVAILABLE_TOOLS',
    'get_tools_by_names',
]


def get_tools_by_names(tool_names):
    """
    根据工具名称列表动态加载工具

    Args:
        tool_names (list): 工具名称列表，如 ['get_current_time', 'web_search']

    Returns:
        list: 工具函数列表

    Raises:
        ValueError: 当工具名称不存在时

    Example:
        >>> tools = get_tools_by_names(['get_current_time', 'web_search'])
        >>> # 返回 [get_current_time, web_search]
    """
    if not tool_names:
        return []

    tools = []
    invalid_tools = []

    for tool_name in tool_names:
        if tool_name in ALL_AVAILABLE_TOOLS:
            tools.append(ALL_AVAILABLE_TOOLS[tool_name])
        else:
            invalid_tools.append(tool_name)

    if invalid_tools:
        raise ValueError(
            f"以下工具不存在: {', '.join(invalid_tools)}. "
            f"可用工具: {', '.join(ALL_AVAILABLE_TOOLS.keys())}"
        )

    return tools