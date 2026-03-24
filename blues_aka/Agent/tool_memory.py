"""工具记忆模块

该模块提供了工具调用结果的记忆和管理功能，
解决 Agent 工具调用结果没有被有效记忆的问题。

主要功能:
    - ToolCallMemory: 工具调用结果记忆
    - ToolCallCache: 工具调用结果缓存
    - 总结工具调用结果
    - 在对话历史中保存工具调用信息

Author: Blues AKA Team
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage

logger = logging.getLogger(__name__)


class ToolCallMemory:
    """
    工具调用结果记忆

    记录和管理 Agent 的工具调用历史，使 Agent 能够引用之前的工具调用结果。

    主要特性:
        1. 记录所有工具调用
        2. 保存工具调用结果
        3. 生成工具调用摘要
        4. 支持在对话历史中引用

    使用示例:
        >>> from blues_aka.Agent.tool_memory import ToolCallMemory
        >>>
        >>> tool_memory = ToolCallMemory()
        >>> tool_memory.add_tool_call(
        ...     tool_name="search",
        ...     tool_input={"query": "机器学习"},
        ...     tool_output="找到 10 个相关文档..."
        ... )
        >>>
        >>> # 获取工具调用历史
        >>> history = tool_memory.get_history()
        >>>
        >>> # 生成摘要
        >>> summary = tool_memory.summarize()
    """

    def __init__(self, max_history: int = 50):
        """
        初始化工具调用记忆

        Args:
            max_history: 最大保存的工具调用数量
                - 超过此数量时会删除最早的记录
                - 默认 50
        """
        self.tool_calls: List[Dict[str, Any]] = []
        self.max_history = max_history

    def add_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: str,
        timestamp: Optional[datetime] = None
    ):
        """
        添加工具调用记录

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            tool_output: 工具输出结果
            timestamp: 工具调用时间
                - 如果为 None，使用当前时间
                - 默认 None
        """
        if timestamp is None:
            timestamp = datetime.now()

        tool_call = {
            "tool": tool_name,
            "input": tool_input,
            "output": tool_output,
            "timestamp": timestamp.isoformat()
        }

        self.tool_calls.append(tool_call)

        # 限制历史记录数量
        if len(self.tool_calls) > self.max_history:
            self.tool_calls = self.tool_calls[-self.max_history:]

        logger.debug(f"添加工具调用: {tool_name}, 总计: {len(self.tool_calls)}")

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取工具调用历史

        Args:
            limit: 返回的最大记录数
                - None: 返回所有记录
                - 默认 None

        Returns:
            List[Dict[str, Any]]: 工具调用记录列表
        """
        if limit and limit < len(self.tool_calls):
            return self.tool_calls[-limit:]
        return list(self.tool_calls)

    def summarize(
        self,
        max_output_length: int = 200,
        include_tools: Optional[List[str]] = None
    ) -> str:
        """
        生成工具调用摘要

        将工具调用历史转换为可读的摘要文本，方便添加到对话历史中。

        Args:
            max_output_length: 每个工具输出的最大长度
                - 超过此长度会被截断
                - 默认 200
            include_tools: 只包含指定的工具
                - None: 包含所有工具
                - 默认 None

        Returns:
            str: 工具调用摘要文本

        示例输出:
            之前使用的工具:
            1. [search] 查询"机器学习" -> 找到10个相关文档...
            2. [calculator] 计算 2+2 -> 结果: 4
        """
        if not self.tool_calls:
            return ""

        # 过滤工具
        calls_to_summarize = self.tool_calls
        if include_tools:
            calls_to_summarize = [
                call for call in self.tool_calls
                if call["tool"] in include_tools
            ]

        # 生成摘要
        summary_parts = []

        if len(calls_to_summarize) > 0:
            summary_parts.append("之前使用的工具:")

            for i, call in enumerate(calls_to_summarize, 1):
                tool_name = call["tool"]
                tool_input = call["input"]
                tool_output = call["output"]

                # 格式化输入
                input_str = str(tool_input)
                if len(input_str) > 100:
                    input_str = input_str[:100] + "..."

                # 格式化输出
                output_str = tool_output
                if len(output_str) > max_output_length:
                    output_str = output_str[:max_output_length] + "..."

                summary_parts.append(f"{i}. [{tool_name}] {input_str} -> {output_str}")

        return "\n".join(summary_parts)

    def get_recent_tool_output(
        self,
        tool_name: str,
        max_calls: int = 5
    ) -> List[str]:
        """
        获取最近某工具的输出

        Args:
            tool_name: 工具名称
            max_calls: 返回的最近调用次数
                - 默认 5

        Returns:
            List[str]: 工具输出列表（按时间倒序）
        """
        calls = [
            call for call in self.tool_calls
            if call["tool"] == tool_name
        ]

        # 返回最近的调用
        recent_calls = calls[-max_calls:][::-1]
        return [call["output"] for call in recent_calls]

    def clear(self):
        """清除所有工具调用记录"""
        self.tool_calls = []
        logger.info("工具调用记忆已清除")

    def to_context_messages(self) -> List[BaseMessage]:
        """
        将工具调用历史转换为消息列表

        可以添加到对话历史中，使 Agent 能够引用之前的工具调用。

        Returns:
            List[BaseMessage]: 消息列表
        """
        messages = []

        if not self.tool_calls:
            return messages

        # 创建工具调用摘要消息
        summary = self.summarize()
        if summary:
            messages.append(
                AIMessage(
                    content=summary,
                    additional_kwargs={"type": "tool_summary"}
                )
            )

        return messages


class ToolCallCache:
    """
    工具调用缓存

    缓存工具调用的结果，避免重复调用相同的工具。

    主要特性:
        1. 基于 tool_name 和 input 生成缓存键
        2. 支持过期时间（TTL）
        3. 自动清理过期缓存
        4. 缓存命中统计

    使用示例:
        >>> from blues_aka.Agent.tool_memory import ToolCallCache
        >>>
        >>> cache = ToolCallCache(ttl_minutes=60)
        >>>
        >>> # 尝试从缓存获取
        >>> result = cache.get("search", {"query": "机器学习"})
        >>> if result is not None:
        >>>     print("缓存命中")
        >>> else:
        >>>     # 调用工具
        >>>     result = search_tool({"query": "机器学习"})
        >>>     # 保存到缓存
        >>>     cache.set("search", {"query": "机器学习"}, result)
        >>>
        >>> # 查看缓存统计
        >>> stats = cache.get_stats()
        >>> print(f"命中率: {stats['hit_rate']:.2%}")
    """

    def __init__(self, ttl_minutes: int = 60):
        """
        初始化工具调用缓存

        Args:
            ttl_minutes: 缓存过期时间（分钟）
                - 默认 60 分钟
                - 过期的缓存会自动清理
        """
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

        # 统计信息
        self.hits = 0
        self.misses = 0

        logger.info(f"工具调用缓存初始化: TTL={ttl_minutes}分钟")

    def _make_key(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        生成缓存键

        基于 tool_name 和 tool_input 生成唯一的缓存键。

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            str: MD5 哈希值
        """
        # 序列化输入参数（排序键以确保一致性）
        key_data = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存结果

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数

        Returns:
            Optional[Any]: 缓存的结果，如果未命中或过期返回 None
        """
        key = self._make_key(tool_name, tool_input)

        if key in self.cache:
            cached_data, timestamp = self.cache[key]

            # 检查是否过期
            if datetime.now() - timestamp < self.ttl:
                self.hits += 1
                logger.debug(f"缓存命中: {tool_name}")
                return cached_data
            else:
                # 过期，删除
                del self.cache[key]
                logger.debug(f"缓存过期: {tool_name}")

        self.misses += 1
        return None

    def set(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        result: Any
    ):
        """
        设置缓存

        Args:
            tool_name: 工具名称
            tool_input: 工具输入参数
            result: 工具调用结果
        """
        key = self._make_key(tool_name, tool_input)
        self.cache[key] = (result, datetime.now())
        logger.debug(f"缓存保存: {tool_name}, 总计: {len(self.cache)}")

    def clear(self):
        """清除所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("工具调用缓存已清除")

    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"清理过期缓存: {len(expired_keys)} 个")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 统计信息字典
                - total_calls: 总调用次数
                - hits: 缓存命中次数
                - misses: 缓存未命中次数
                - hit_rate: 命中率（0-1）
                - cache_size: 当前缓存大小
        """
        total_calls = self.hits + self.misses

        return {
            "total_calls": total_calls,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total_calls if total_calls > 0 else 0.0,
            "cache_size": len(self.cache)
        }


def extract_tool_calls_from_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """
    从消息列表中提取工具调用信息

    Args:
        messages: 消息列表（包含 AIMessage 和 ToolMessage）

    Returns:
        List[Dict[str, Any]]: 工具调用记录列表

    示例:
        >>> messages = [
        ...     HumanMessage("搜索机器学习"),
        ...     AIMessage("", tool_calls=[{"name": "search", "args": {"query": "机器学习"}}]),
        ...     ToolMessage("找到10个文档...", tool_call_id="...")
        ... ]
        >>> tool_calls = extract_tool_calls_from_messages(messages)
        >>> print(tool_calls)
        [
            {
                "tool": "search",
                "input": {"query": "机器学习"},
                "output": "找到10个文档..."
            }
        ]
    """
    tool_calls = []

    for msg in messages:
        if isinstance(msg, AIMessage):
            # 检查是否有工具调用
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_calls.append({
                        "tool": tool_call.get("name"),
                        "input": tool_call.get("args", {}),
                        "output": None,  # 输出在后面的 ToolMessage 中
                        "tool_call_id": tool_call.get("id", "")
                    })

        elif isinstance(msg, ToolMessage):
            # 找到对应的工具调用，添加输出
            tool_call_id = getattr(msg, 'tool_call_id', '')

            for tc in reversed(tool_calls):
                if tc["tool_call_id"] == tool_call_id and tc["output"] is None:
                    tc["output"] = msg.content
                    break

    return tool_calls
