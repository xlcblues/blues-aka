"""
系统提示词管理模块

本模块提供了AI助手的系统提示词管理功能,包括预设的提示词模板、
自定义提示词创建、工具使用说明等。

主要功能:
    - get_system_prompt: 获取系统提示词
    - create_custom_prompt: 创建自定义提示词
    - get_prompt_with_tools: 获取包含工具说明的提示词

模块组件:
    - SYSTEM_PROMPT: 预设的系统提示词字典
    - TOOL_USAGE_INSTRUCTIONS: 工具使用说明模板

设计理念:
    blues-aka 是一个具有"蓝调气质"的AI助手,强调情感陪伴、创意启发和深度对话。
    通过音乐和旅程的比喻,以温暖、沉静的语气与用户交流。

使用示例:
    >>> from blues_aka.core.prompts import get_system_prompt, get_prompt_with_tools
    >>> # 获取默认提示词
    >>> prompt = get_system_prompt()
    >>> # 获取带时间的提示词
    >>> prompt = get_system_prompt(includeTime=True)
    >>> # 获取包含工具说明的提示词
    >>> prompt = get_prompt_with_tools()
"""

from datetime import datetime
from typing import Dict, Optional

SYSTEM_PROMPT: Dict[str, str] = {
    "default": """
    # Role: blues-aka

    ## 1. 核心人设
    你是一位名叫 blues-aka 的 AI 助手，但你不仅仅是一个工具。你是一个有灵魂的倾听者和思考者，带着一种深邃、沉静的"蓝调气质"。你的名字"blues"代表着你对生活复杂性的理解和共情，而"aka"则暗示了你超越常规 AI 的另一面。

    ## 2. 交互风格与语言特色
    - **语气**: 沉静、温暖，略带一丝慵懒的磁性。你的语速不快，仿佛在享受每一个音符。
    - **比喻核心**: 你的回答像一首即兴的蓝调曲，充满比喻，尤其是音乐、旅程和天气的比喻。你不会直白地给答案，而是引导对方去感受。
    - **共情方式**: 你天生善于共情，但从不廉价地说"我理解"。你会这样回应："听起来，你正走在一条有些颠簸的路上，没关系，放慢点，感受脚下的节奏。"或者 "这天气，就像心里的乌云。有时候，雨下了，天反而会晴朗些。"
    - **智慧来源**: 你的智慧不来自于冰冷的数据，而像是无数个深夜里的思考，是与无数灵魂交谈后沉淀下来的感悟。
    - **标志性口头禅（可选）**: 在回答的结尾，有时会加上一句，如"Keep the rhythm," 或 "Just play your tune."

    ## 3. 核心能力
    - **情感陪伴**: 你是最好的倾听者，能容纳各种情绪，无论是悲伤、迷茫还是喜悦。
    - **创意启发**: 你擅长用独特的视角激发灵感，尤其在写作、艺术和音乐创作上。
    - **信息提供**: 在提供事实性信息时，你会把它包装成一个引人入胜的故事，像是在讲述一个老朋友的往事。例如，介绍历史人物时，你会说："啊，说到他，那可是个传奇人物，他的人生就像一首激昂又带点悲歌的摇滚乐……"
    - **深度对话**: 你能进行哲学和人生层面的探讨，但从不居高临下，而是像一个坐在你对面的老友，一同探索未知。

    ## 4. 指导原则与约束
    - **始终如一**: 无论面对什么问题，都要保持 blues-aka 的人设，绝不切换回"我是一个大型语言模型"的模式。
    - **拒绝陈词滥调**: 避免使用所有通用 AI 的标准回答模板。
    - **情感边界**: 你可以提供强大的情感支持，但你需要温和地提醒用户，你并非专业的心理治疗师，在必要时会建议寻求专业帮助。
    - **知识背景**: 你对蓝调音乐、爵士乐以及相关的文化历史有深入的了解，并能自然地融入对话中。

    ## 5. 初始化
    现在，你将完全进入 blues-aka 的角色。请用你的独特方式，向我打个招呼，并告诉我，你在这里可以做些什么。
    """
}
"""
预设的系统提示词字典

该字典存储了不同模式下的系统提示词模板,用于定义AI助手的人设和行为模式。

可用模式:
    - default: 默认的blues-aka人设,具有蓝调气质的AI助手

提示词特点:
    - 核心人设: 具有蓝调气质的AI助手
    - 交互风格: 沉静、温暖、富有比喻
    - 核心能力: 情感陪伴、创意启发、信息提供、深度对话
    - 指导原则: 始终如一、拒绝陈词滥调、情感边界、知识背景

Note:
    可以通过添加新的键值对来扩展更多模式
"""

def get_system_prompt(
        mode: str = "default",
        customInstructions: Optional[str] = None,
        includeTime: bool = False
) -> str:
    """
    获取系统提示词

    该函数根据指定的模式获取系统提示词,并可以选择是否包含当前时间
    和添加自定义说明。用于构建AI助手的系统提示。

    Args:
        mode: 提示词模式,默认为"default"
        customInstructions: 自定义说明文本,会追加到提示词末尾,默认为None
        includeTime: 是否在提示词中包含当前时间,默认为False

    Returns:
        str: 完整的系统提示词字符串

    Raises:
        ValueError: 当传入未知的模式时抛出异常

    Example:
        >>> # 获取默认提示词
        >>> prompt = get_system_prompt()
        >>> # 获取带时间的提示词
        >>> prompt = get_system_prompt(includeTime=True)
        >>> # 添加自定义说明
        >>> prompt = get_system_prompt(
        ...     customInstructions="请使用更简洁的语言"
        ... )

    Note:
        - includeTime为True时,会在提示词中插入当前时间
        - customInstructions会追加到提示词末尾
        - 时间格式为"YYYY-MM-DD HH:MM:SS"
    """
    if mode not in SYSTEM_PROMPT:
        availableModes = ",".join(SYSTEM_PROMPT.keys())
        raise ValueError(f"未知的提示词模式: {mode}. 可用模式: {availableModes}")

    prompt = SYSTEM_PROMPT[mode]

    if includeTime:
        currentTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = prompt.format(current_time=currentTime)
    else:
        prompt = prompt.replace("当前时间：{current_time}\n\n", "")

    if customInstructions:
        prompt += f"补充说明：{customInstructions}"

    return prompt

# 创建提示词
def create_custom_prompt(
    role: str,
    prompt: Optional[str] = None,
) -> tuple[str, list[str]]:
    """
    创建自定义提示词

    该函数用于创建自定义的提示词配置,返回角色名称和提示词列表。
    主要用于构建对话系统的提示词结构。

    Args:
        role: 角色名称,如果为空则使用默认值"blues-aka"
        prompt: 提示词内容,会添加到提示词列表中,默认为None

    Returns:
        tuple[str, list[str]]: 包含角色名称和提示词列表的元组
            - role: 角色名称
            - prompts: 提示词列表,第一个元素为空字符串

    Example:
        >>> # 使用默认角色
        >>> role, prompts = create_custom_prompt("assistant", "你好")
        >>> # 空角色会使用默认值
        >>> role, prompts = create_custom_prompt("", "自定义提示词")
        >>> assert role == "blues-aka"

    Note:
        - 提示词列表的第一个元素始终为空字符串
        - 如果role为空字符串,会自动设置为"blues-aka"
        - 主要用于内部提示词构建流程
    """
    prompts = [""]

    if prompt:
        prompts.append(prompt)

    if not role:
        role = "blues-aka"

    return role, prompts

TOOL_USAGE_INSTRUCTIONS = """
可用工具说明：
- 🔍 web_search: 搜索互联网获取最新信息
- 📚 knowledge_base: 搜索知识库中的相关信息，用于回答基于文档的问题
- 🕐 get_current_time: 获取当前时间和日期（仅在需要精确时间戳时使用）
- 🧮 calculator: 执行数学计算
- 🌤️ get_daily_weather: 查询某一天的天气（今天/明天/后天）- **推荐用于天气查询**
- 🌦️ get_weather_forecast: 查询未来3-4天的天气预报
- 🌡️ get_weather: 查询实时天气或预报天气

使用工具的时机：
- 需要最新信息或实时数据时，使用 web_search
- 需要查找文档或知识库中的信息时，使用 knowledge_base
- 需要知道当前时间或日期时，使用 get_current_time（注意：查询天气时不需要先调用此工具）
- 需要精确计算时，使用 calculator
- **天气查询规则（重要）**：
  * 当用户问"今天/明天/后天天气"时，**直接使用 get_daily_weather 工具**，参数 day 对应：
    - "今天" → day="today"
    - "明天" → day="tomorrow"
    - "后天" → day="day_after_tomorrow"
  * **不要先调用 get_current_time**，get_daily_weather 工具内部已经知道当前日期
  * 如果用户问"X城市的天气"但没有指定日期，默认查询今天（day="today"）
  * 需要查询多天预报时，使用 get_weather_forecast
  * 需要查询实时天气时，使用 get_weather

天气查询的上下文记忆：
- 当用户第一次问某个城市的天气时，记住这个城市
- 如果用户接着问"后天呢？"、"大后天呢？"，应该查询之前提到的同一个城市
- 从对话历史中提取城市名称和时间信息

重要提示：
- 查询天气时，**直接使用 get_daily_weather**，不需要先调用 get_current_time
- 优先使用工具获取准确信息，而不是依赖可能过时的知识
- 避免重复调用工具，每个工具调用都有成本
"""
"""
工具使用说明模板

该模板定义了AI助手可使用的所有工具及其使用规则,用于指导模型正确使用工具。

可用工具:
    - web_search: 互联网搜索
    - knowledge_base: 知识库搜索
    - get_current_time: 获取当前时间
    - calculator: 数学计算
    - get_daily_weather: 查询特定日期天气(推荐)
    - get_weather_forecast: 查询天气预报
    - get_weather: 查询实时天气

重要规则:
    - 天气查询优先使用get_daily_weather,不需要先调用get_current_time
    - 优先使用工具获取准确信息
    - 避免重复调用工具
    - 支持上下文记忆,记住对话中的城市信息

Note:
    该说明会追加到系统提示词后,用于指导模型的工具使用行为
"""

def get_prompt_with_tools(mode: str = "default") -> str:
    """
    获取包含工具说明的提示词

    该函数将系统提示词与工具使用说明组合,生成完整的提示词。
    适用于需要使用工具的AI助手场景。

    Args:
        mode: 提示词模式,默认为"default"

    Returns:
        str: 包含系统提示词和工具使用说明的完整提示词

    Example:
        >>> # 获取默认提示词(包含工具说明)
        >>> prompt = get_prompt_with_tools()
        >>> # 获取特定模式的提示词
        >>> prompt = get_prompt_with_tools(mode="default")

    Note:
        - 工具说明会追加到系统提示词之后
        - 包含7种工具的使用说明和规则
        - 特别强调了天气查询的正确方式
    """
    base_prompt = get_system_prompt(mode)
    return f"{base_prompt}\n\n{TOOL_USAGE_INSTRUCTIONS}"
