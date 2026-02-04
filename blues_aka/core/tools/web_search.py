"""
联网搜索工具模块

本模块提供了基于 Tavily 搜索 API 的联网搜索功能，允许 AI 智能体在对话中
获取最新的网络信息，增强回答的时效性和准确性。

主要功能：
    - 实时网络搜索：通过 Tavily API 搜索互联网内容
    - 灵活配置：支持自定义搜索参数（结果数量、搜索深度、域名过滤等）
    - LangChain 集成：作为 LangChain 工具，可被 AI 智能体自动调用
    - 友好错误处理：当 API 未配置或搜索失败时返回清晰的提示信息

使用场景：
    - 询问实时信息（如"今天的天气"、"最新新闻"）
    - 获取最新数据（如"当前股价"、"最近发布的产品"）
    - 验证过时信息（如"这个说法还准确吗"）
    - 补充知识盲区（如"详细解释一下这个概念"）

配置要求：
    1. 安装依赖：pip install langchain-tavily
    2. 设置 API Key：在环境变量或 .env 文件中配置 TAVILY_API_KEY
    3. 可选配置：TAVILY_MAX_RESULTS（默认搜索结果数量）

工具注册：
    本工具被注册到 OPTIONAL_TOOLS 中，需要在 Agent 配置中明确启用才能使用。

性能考虑：
    - 搜索操作会产生额外的 API 调用和延迟
    - 建议在需要实时信息时才启用此工具
    - 可以通过缓存和配额管理控制成本

Example:
    基本使用（作为 LangChain 工具）::

        from blues_aka.core.tools import OPTIONAL_TOOLS

        # 创建带联网搜索的 Agent
        agent = BaseAgent(
            model="glm-4.5",
            tools=[OPTIONAL_TOOLS['web_search']]
        )

        # AI 会根据需要自动调用搜索
        response = agent.invoke("今天的新闻是什么？")

    自定义搜索参数::

        tool = create_tavily_search_tool(
            max_results=5,
            search_depth="basic",
            include_domain=["wikipedia.org"]
        )

Author: Blues AKA Team
Version: 1.0.0
"""

import logging
from typing import Optional, List

from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from blues_aka.config.config import ConfigFactory

logger = logging.getLogger(__name__)
_config = ConfigFactory.get_config()

def create_tavily_search_tool(
    max_results: Optional[int] = None,
    search_depth: str = "advanced",
    include_domain: Optional[List[str]] = None,
    exclude_domain: Optional[List[str]] = None,
):
    """
    创建 Tavily 搜索工具实例

    创建一个配置完整的 Tavily 搜索工具，支持自定义搜索参数。
    这个工具可以直接用于 LangChain Agent 或作为独立组件使用。

    Args:
        max_results (Optional[int]): 最大返回结果数量
            - 如果为 None，使用配置文件中的 tavily_max_results 值
            - 建议范围：5-20，默认值通常为 10
            - 注意：更多的结果会消耗更多的 API 配额

        search_depth (str): 搜索深度，影响搜索质量和响应时间
            - "basic": 快速搜索，返回基本结果，适合一般查询
            - "advanced": 深度搜索，返回更详细的结果，适合复杂查询
            - 默认值："advanced"

        include_domain (Optional[List[str]]): 限定搜索的域名白名单
            - 只搜索指定的域名
            - 例如：["wikipedia.org", "github.com", "stackoverflow.com"]
            - 如果为 None，搜索所有域名
            - 用途：提高搜索结果的相关性和可信度

        exclude_domain (Optional[List[str]]): 排除搜索的域名黑名单
            - 排除指定的域名
            - 例如：["ads.example.com", "spam.site"]
            - 如果为 None，不排除任何域名
            - 用途：过滤广告、垃圾内容等

    Returns:
        TavilySearch: 配置好的 Tavily 搜索工具实例
            可以直接用于 LangChain Agent 或通过 invoke() 方法调用

    Raises:
        ValueError: 当出现以下情况时抛出
            - Tavily 搜索工具未安装（缺少 langchain-tavily 包）
            - Tavily API Key 未配置（环境变量 TAVILY_API_KEY 未设置）

        Exception: 创建工具实例时的其他错误
            - 通常与网络连接或 API 服务相关

    Example:
        基本使用::

            tool = create_tavily_search_tool()
            results = tool.invoke({"query": "Python 编程"})

        自定义结果数量::

            tool = create_tavily_search_tool(max_results=5)
            results = tool.invoke({"query": "最新科技新闻"})

        限定搜索范围::

            tool = create_tavily_search_tool(
                max_results=10,
                search_depth="advanced",
                include_domain=["wikipedia.org", "github.com"]
            )
            results = tool.invoke({"query": "机器学习"})

        排除特定域名::

            tool = create_tavily_search_tool(
                exclude_domain=["ads.com", "spam.site"]
            )
            results = tool.invoke({"query": "健康饮食"})

    Note:
        - Tavily API Key 需要在环境变量或配置文件中设置
        - 搜索深度为 "advanced" 时响应时间会稍长，但结果质量更高
        - 建议根据具体需求平衡搜索质量和响应速度

    See Also:
        web_search: 封装了此函数的 LangChain 工具函数
        TavilySearch: LangChain 的 Tavily 搜索工具类
    """
    # 验证依赖和配置
    if TavilySearch is None:
        raise ValueError("Tavily 搜索工具未安装！请安装: pip install langchain-tavily")

    if not _config.tavily_api_key:
        raise ValueError("Tavily API Key 未设置！请在环境变量或 .env 文件中设置 TAVILY_API_KEY")

    # 确定最大结果数量（优先使用配置文件的值）
    max_results = _config.tavily_max_results or max_results

    # 构建基础配置参数
    tool_kwargs = {
        "max_results": max_results,
        "api_key": _config.tavily_api_key,
        "search_depth": search_depth
    }

    # 添加域名过滤配置
    if include_domain:
        tool_kwargs["include_domain"] = include_domain

    if exclude_domain:
        tool_kwargs["exclude_domain"] = exclude_domain

    # 创建并返回工具实例
    try:
        tool = TavilySearch(**tool_kwargs)
        return tool

    except Exception as e:
        logger.error(f"创建 Tavily 工具失败: {e}")
        raise

@tool
def web_search(query: str) -> str:
    """
    在互联网上搜索信息并返回结果

    这是一个 LangChain 工具函数，可以被 AI 智能体自动调用。
    使用 Tavily 搜索 API 在互联网上查找最新的信息，帮助 AI
    提供基于最新数据的准确回答。

    工具名称: web_search
    工具描述: 搜索互联网以获取最新信息。当你需要实时数据、当前事件、
             或验证过时信息时使用此工具。输入应该是一个搜索查询字符串。

    Args:
        query (str): 搜索查询字符串
            - 必填参数
            - 应该简洁明了地描述要搜索的内容
            - 支持自然语言查询（如"今天的天气"、"最新科技新闻"）
            - 也支持关键词搜索（如"Python教程"、"机器学习算法"）
            - 建议长度：10-100 个字符

    Returns:
        str: 格式化的搜索结果
            包含以下信息：
            - 搜索结果数量
            - 每个结果的标题
            - 每个结果的内容摘要
            - 每个结果的来源 URL

            返回格式示例::

                找到 5 条搜索结果：

                1. Python 官方网站
                   内容: Python 是一种高级编程语言...
                   来源: https://www.python.org

                2. Python 教程 - 菜鸟教程
                   内容: Python 基础语法、数据类型、函数...
                   来源: https://www.runoob.com/python

            错误情况返回：
            - 如果 API Key 未配置：返回友好的配置提示
            - 如果未找到结果：返回"未找到相关信息"
            - 如果搜索失败：返回错误描述

    Raises:
        无显式抛出异常，所有错误都在函数内部处理并返回友好的错误消息

    Example:
        AI 调用示例::

            # 用户问："今天的天气怎么样？"
            # AI 判断需要最新信息，自动调用工具

            result = web_search("北京今天天气")
            # 返回："找到 3 条搜索结果：\n\n1. 北京天气预报..."

        手动调用示例::

            from blues_aka.core.tools import OPTIONAL_TOOLS

            tool = OPTIONAL_TOOLS['web_search']
            result = tool.invoke("ChatGPT 最新发布")
            print(result)

    Usage Tips:
        何时使用：
        - 需要实时信息（天气、新闻、股价等）
        - 验证已知信息的准确性
        - 获取最新的技术文档或公告
        - 补充知识库中缺失的信息

        何时不使用：
        - 询问常识性问题（AI 已知道答案）
        - 需要创意或想象力（搜索帮助不大）
        - 涉及隐私或敏感信息
        - 可以从对话历史中推断答案

        查询优化：
        - 使用具体的关键词而非模糊描述
        - 包含时间限定（如"2024年"、"最新"）
        - 如果知道相关领域，添加领域限定词
        - 避免过于复杂的查询语句

    Performance:
        - 响应时间：通常 1-3 秒
        - API 配额：每次搜索消耗 1 次调用
        - 结果数量：默认 10 条，可通过配置调整
        - 建议频率：单次对话中不超过 3 次搜索

    Configuration:
        需要设置环境变量：
        - TAVILY_API_KEY: Tavily API 密钥（必填）
        - TAVILY_MAX_RESULTS: 最大结果数（可选，默认 10）

        获取 API Key：
        访问 https://tavily.com 注册账号并获取 API Key

    Note:
        - 此工具使用 Tavily 搜索 API，需要有效的 API Key
        - 搜索结果来自互联网，质量和准确性可能因来源而异
        - AI 会根据搜索结果综合分析，而不是直接返回原始结果
        - 搜索操作会增加响应延迟，请合理使用

    See Also:
        create_tavily_search_tool: 创建自定义配置的搜索工具
        TavilySearch: 底层搜索实现类
    """
    logger.info(f"开始查找网络内容：{query}")

    try:
        # 检查 API Key 是否配置
        if not _config.tavily_api_key:
            logger.warning("Tavily API Key 未设置，无法执行搜索")
            return (
                "抱歉，网络搜索功能暂时不可用（未配置 Tavily API Key）。"
                "请在 .env 文件中设置 TAVILY_API_KEY。"
            )
        # 创建搜索工具并执行搜索
        search_tool = create_tavily_search_tool()
        response = search_tool.invoke({"query": query})
        # 检查响应格式并提取结果
        if isinstance(response, dict):
            # Tavily API 返回的格式
            if "results" in response:
                results = response["results"]
            else:
                logger.warning("Tavily 响应格式异常：缺少 'results' 字段")
                return f"搜索服务响应异常，请稍后重试。"
        elif isinstance(response, list):
            # 如果直接返回的是列表
            results = response
        else:
            logger.error(f"未知的响应格式: {type(response)}")
            return f"搜索服务响应格式错误。"
        # 处理无结果的情况
        if not results:
            logger.info("未找到搜索结果")
            return f"未找到关于 '{query}' 的相关信息。"
        # 格式化搜索结果
        formatted_results = [f"找到 {len(results)} 条搜索结果：\n"]
        for i, result in enumerate(results, 1):
            # 确保每个结果都是字典类型
            if not isinstance(result, dict):
                logger.warning(f"结果 {i} 不是字典类型: {type(result)}")
                continue

            title = result.get("title", "无标题")
            content = result.get("content", "")
            url = result.get("url", "")
            # 构建结果条目
            formatted_results.append(f"\n{i}. {title}")
            if content:
                formatted_results.append(f"   内容: {content}")
            if url:
                formatted_results.append(f"   来源: {url}")
        # 合并结果并返回
        result_text = "\n".join(formatted_results)
        logger.info(f"搜索完成，找到 {len(results)} 条结果")
        return result_text
    except Exception as e:
        # 错误处理：记录日志并返回友好的错误消息
        error_msg = f"搜索时发生错误: {str(e)}"
        logger.error(f"{error_msg}")
        return f"抱歉，{error_msg}"

