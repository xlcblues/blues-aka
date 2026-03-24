"""Agent性能监控模块

该模块提供了Agent性能监控和指标收集功能，
帮助了解Agent的运行状况和性能瓶颈。

主要功能:
    - AgentMetrics: 性能指标收集器
    - track_agent_performance: 性能监控装饰器
    - MetricsStore: 指标存储和查询
    - 性能统计和分析

Author: Blues AKA Team
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class MetricsStore:
    """
    指标存储和查询

    存储和管理Agent的性能指标数据。
    """

    def __init__(self, max_records: int = 10000):
        """
        初始化指标存储

        Args:
            max_records: 最大存储记录数（默认10000）
        """
        self._metrics: List[Dict[str, Any]] = []
        self._max_records = max_records
        self._lock = threading.RLock()

        # 统计缓存
        self._stats_cache: Dict[str, Any] = {}
        self._stats_cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=60)

    def add_metric(self, metric: Dict[str, Any]):
        """
        添加指标记录

        Args:
            metric: 指标数据字典
        """
        with self._lock:
            self._metrics.append(metric)

            # 限制记录数量
            if len(self._metrics) > self._max_records:
                self._metrics = self._metrics[-self._max_records:]

            # 清除统计缓存
            self._stats_cache = {}
            self._stats_cache_time = None

    def get_metrics(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询指标记录

        Args:
            filters: 过滤条件（如 {'model': 'glm-4.5'}）
            limit: 返回记录数
            offset: 偏移量

        Returns:
            List[Dict[str, Any]]: 指标记录列表
        """
        with self._lock:
            metrics = self._metrics

            # 应用过滤
            if filters:
                metrics = [
                    m for m in metrics
                    if all(m.get(k) == v for k, v in filters.items())
                ]

            # 分页
            return metrics[offset:offset + limit]

    def get_statistics(
        self,
        group_by: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取统计信息（优化版，避免长时间持锁）

        Args:
            group_by: 分组字段（如 'model', 'agent_type'）
            force_refresh: 是否强制刷新缓存

        Returns:
            Dict[str, Any]: 统计信息字典
        """
        # 步骤1：快速检查缓存（持锁时间很短）
        with self._lock:
            cache_key = f"stats_{group_by or 'all'}"
            if not force_refresh and self._stats_cache_time:
                if datetime.now() - self._stats_cache_time < self._cache_ttl:
                    return self._stats_cache.get(cache_key, {})

            # 快速复制数据（复制列表很快，毫秒级）
            metrics_data = list(self._metrics)

        # 步骤2：在锁外计算统计（关键优化！避免阻塞其他操作）
        stats = self._calculate_statistics_with_data(metrics_data, group_by)

        # 步骤3：更新缓存（持锁时间很短）
        with self._lock:
            self._stats_cache[cache_key] = stats
            self._stats_cache_time = datetime.now()

        return stats

    def _calculate_statistics_with_data(
        self,
        metrics_data: List[Dict[str, Any]],
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用提供的数据计算统计（不持有锁）

        这是关键优化：在锁外计算，避免阻塞其他操作
        """
        if not metrics_data:
            return {}

        if group_by:
            # 分组统计
            groups = defaultdict(list)
            for m in metrics_data:
                key = m.get(group_by, 'unknown')
                groups[key].append(m)

            return {
                key: self._calc_group_stats(group_metrics)
                for key, group_metrics in groups.items()
            }
        else:
            # 整体统计
            return self._calc_group_stats(metrics_data)

    def _calc_group_stats(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算一组指标的统计信息"""
        if not metrics:
            return {}

        durations = [m.get('duration', 0) for m in metrics if m.get('duration')]
        input_tokens = [m.get('input_tokens', 0) for m in metrics if m.get('input_tokens')]
        output_tokens = [m.get('output_tokens', 0) for m in metrics if m.get('output_tokens')]

        total_requests = len(metrics)
        successful_requests = len([m for m in metrics if m.get('success', True)])
        failed_requests = total_requests - successful_requests

        stats = {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0.0,
        }

        if durations:
            stats.update({
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p50_duration': self._percentile(durations, 50),
                'p95_duration': self._percentile(durations, 95),
                'p99_duration': self._percentile(durations, 99),
            })

        if input_tokens:
            stats.update({
                'total_input_tokens': sum(input_tokens),
                'avg_input_tokens': sum(input_tokens) / len(input_tokens),
            })

        if output_tokens:
            stats.update({
                'total_output_tokens': sum(output_tokens),
                'avg_output_tokens': sum(output_tokens) / len(output_tokens),
            })

        return stats

    def _percentile(self, data: List[float], p: int) -> float:
        """
        计算百分位数（优化版）

        当数据量大时使用采样，避免长时间排序
        """
        if not data:
            return 0.0

        # 优化：如果数据量大，使用采样计算百分位数
        if len(data) > 1000:
            import random
            sample_size = min(1000, len(data))
            data = random.sample(data, sample_size)

        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def clear_old_metrics(self, older_than: timedelta = timedelta(hours=24)):
        """
        清理旧指标

        Args:
            older_than: 保留最近多长时间的指标
        """
        with self._lock:
            cutoff_time = datetime.now() - older_than
            self._metrics = [
                m for m in self._metrics
                if datetime.fromisoformat(m.get('timestamp', '')) > cutoff_time
            ]
            logger.info(f"清理了旧指标，保留 {len(self._metrics)} 条记录")

    def clear_all(self):
        """清除所有指标"""
        with self._lock:
            self._metrics.clear()
            self._stats_cache.clear()
            self._stats_cache_time = None
            logger.info("已清除所有指标")


class AgentMetrics:
    """
    Agent性能监控器

    负责收集和记录Agent的性能指标。

    主要功能:
        1. 记录请求时间
        2. 记录token使用量
        3. 记录错误和异常
        4. 统计和分析

    使用示例:
        >>> from blues_aka.Agent.agent_metrics import AgentMetrics
        >>>
        >>> metrics = AgentMetrics()
        >>>
        >>> # 记录请求
        >>> metrics.record_request(
        ...     model='glm-4.5',
        ...     duration=1.5,
        ...     input_tokens=100,
        ...     output_tokens=200,
        ...     success=True
        ... )
        >>>
        >>> # 获取统计
        >>> stats = metrics.get_statistics()
        >>> print(f"平均响应时间: {stats['avg_duration']:.2f}秒")
    """

    def __init__(self, store: Optional[MetricsStore] = None):
        """
        初始化监控器

        Args:
            store: 指标存储实例（None 使用全局实例）
        """
        self.store = store or get_global_metrics_store()

    def record_request(
        self,
        model: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        agent_type: str = 'base',
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """
        记录一次Agent请求

        Args:
            model: 模型名称
            duration: 响应时间（秒）
            success: 是否成功
            error: 错误信息（如果失败）
            input_tokens: 输入token数
            output_tokens: 输出token数
            agent_type: Agent类型
            extra_data: 额外数据
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'duration': duration,
            'success': success,
            'agent_type': agent_type,
        }

        if error:
            metric['error'] = error

        if input_tokens is not None:
            metric['input_tokens'] = input_tokens

        if output_tokens is not None:
            metric['output_tokens'] = output_tokens

        if extra_data:
            metric.update(extra_data)

        self.store.add_metric(metric)

        # 日志记录
        if success:
            logger.debug(
                f"Agent请求成功 - 模型: {model}, "
                f"耗时: {duration:.2f}秒, "
                f"tokens: {input_tokens or 0} -> {output_tokens or 0}"
            )
        else:
            logger.warning(f"Agent请求失败 - 模型: {model}, 错误: {error}")

    def record_error(
        self,
        model: str,
        error: str,
        duration: Optional[float] = None,
        agent_type: str = 'base'
    ):
        """
        记录错误

        Args:
            model: 模型名称
            error: 错误信息
            duration: 尝试的时长
            agent_type: Agent类型
        """
        self.record_request(
            model=model,
            duration=duration or 0.0,
            success=False,
            error=error,
            agent_type=agent_type
        )

    def get_statistics(
        self,
        group_by: Optional[str] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取统计信息

        Args:
            group_by: 分组字段（如 'model'）
            force_refresh: 是否强制刷新

        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.store.get_statistics(group_by=group_by, force_refresh=force_refresh)

    def get_recent_metrics(
        self,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取最近的指标记录

        Args:
            limit: 返回记录数
            filters: 过滤条件

        Returns:
            List[Dict[str, Any]]: 指标记录
        """
        return self.store.get_metrics(filters=filters, limit=limit)

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            Dict[str, Any]: 性能摘要
        """
        stats = self.get_statistics()
        recent = self.get_recent_metrics(limit=100)

        summary = {
            'total_requests': stats.get('total_requests', 0),
            'success_rate': stats.get('success_rate', 0.0),
            'avg_duration': stats.get('avg_duration', 0.0),
            'p95_duration': stats.get('p95_duration', 0.0),
        }

        # 最近的趋势
        if len(recent) >= 10:
            recent_durations = [m.get('duration', 0) for m in recent[-10:]]
            summary['recent_avg_duration'] = sum(recent_durations) / len(recent_durations)

        return summary


# 全局指标存储实例
_global_metrics_store: Optional[MetricsStore] = None
_store_lock = threading.Lock()


def get_global_metrics_store() -> MetricsStore:
    """
    获取全局指标存储实例

    Returns:
        MetricsStore: 全局指标存储
    """
    global _global_metrics_store

    if _global_metrics_store is None:
        with _store_lock:
            if _global_metrics_store is None:
                _global_metrics_store = MetricsStore()
                logger.info("全局指标存储已初始化")

    return _global_metrics_store


def get_global_metrics() -> AgentMetrics:
    """
    获取全局监控器实例

    Returns:
        AgentMetrics: 全局监控器
    """
    return AgentMetrics(get_global_metrics_store())


def track_agent_performance(
    metrics: Optional[AgentMetrics] = None,
    agent_type: str = 'base'
):
    """
    Agent性能监控装饰器

    自动记录被装饰函数的性能指标。

    Args:
        metrics: 监控器实例（None 使用全局实例）
        agent_type: Agent类型

    Returns:
        装饰器函数

    使用示例:
        >>> from blues_aka.Agent.agent_metrics import track_agent_performance
        >>>
        >>> @track_agent_performance()
        ... def my_agent_function(query: str) -> str:
        ...     # 你的代码
        ...     return result
        >>>
        >>> # 调用时会自动记录性能
        >>> result = my_agent_function("test")
    """
    if metrics is None:
        metrics = get_global_metrics()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            model_name = 'unknown'
            success = True
            error_msg = None
            result = None
            input_tokens = None
            output_tokens = None

            try:
                # 尝试从 args[0]（self）获取模型名称
                if args and hasattr(args[0], 'model'):
                    model = args[0].model
                    if hasattr(model, 'model_name'):
                        model_name = model.model_name
                    elif isinstance(model, str):
                        model_name = model

                # 调用原始函数
                result = func(*args, **kwargs)

                # 尝试提取token信息（如果返回的是LLM结果）
                if hasattr(result, 'usage_metadata'):
                    usage = result.usage_metadata
                    input_tokens = usage.get('input_tokens')
                    output_tokens = usage.get('output_tokens')

                return result

            except Exception as e:
                success = False
                error_msg = str(e)
                logger.error(f"Agent调用失败: {e}", exc_info=True)
                raise

            finally:
                # 记录指标
                duration = time.time() - start_time
                metrics.record_request(
                    model=model_name,
                    duration=duration,
                    success=success,
                    error=error_msg,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    agent_type=agent_type
                )

        return wrapper

    return decorator


def track_method_performance(
    method_name: Optional[str] = None,
    metrics: Optional[AgentMetrics] = None
):
    """
    方法级性能监控装饰器

    用于监控特定方法的性能。

    Args:
        method_name: 方法名称（None 使用函数名）
        metrics: 监控器实例

    使用示例:
        >>> class MyAgent:
        ...     @track_method_performance()
        ...     def invoke(self, text: str):
        ...         return self.model.invoke(text)
    """
    if metrics is None:
        metrics = get_global_metrics()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                success = True
                return result

            except Exception as e:
                success = False
                logger.error(f"{func.__name__} 调用失败: {e}")
                raise

            finally:
                duration = time.time() - start_time
                name = method_name or func.__name__

                # 记录到额外数据中
                metrics.record_request(
                    model='method',
                    duration=duration,
                    success=success,
                    extra_data={
                        'method_name': name,
                        'class_name': args[0].__class__.__name__ if args else 'unknown'
                    }
                )

        return wrapper

    return decorator
