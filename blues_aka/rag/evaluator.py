"""RAG 质量评估模块

该模块提供了评估 RAG（检索增强生成）系统质量的工具和指标。
主要包括：
    - 检索质量评估（准确率、召回率、F1 分数）
    - 用户反馈收集和分析
    - RAG 回答质量评估
    - 检索效果追踪

主要功能:
    - RAGEvaluator: 评估检索质量
    - RAGFeedbackCollector: 收集用户反馈
    - RAGMetricsTracker: 追踪 RAG 性能指标

使用示例:
    >>> from blues_aka.rag.evaluator import RAGEvaluator
    >>> evaluator = RAGEvaluator()
    >>> metrics = evaluator.evaluate_retrieval(query, retrieved_docs, relevant_docs)
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class RAGEvaluator:
    """RAG 质量评估器

    提供检索质量评估和 RAG 系统性能分析功能。
    """

    def __init__(self):
        """初始化评估器"""
        self.evaluations: List[Dict[str, Any]] = []
        self.feedback_history: List[Dict[str, Any]] = []

    def evaluate_retrieval(
        self,
        query: str,
        retrieved_docs: List[Any],
        relevant_docs: List[Any],
        doc_id_field: str = 'id'
    ) -> Dict[str, float]:
        """
        评估检索质量

        计算检索结果的准确率、召回率和 F1 分数。

        Args:
            query: 用户查询
            retrieved_docs: 检索到的文档列表
            relevant_docs: 真实相关的文档列表（标注数据）
            doc_id_field: 文档 ID 字段名称

        Returns:
            包含以下指标的字典:
                - precision: 准确率（检索到的相关文档 / 总检索文档数）
                - recall: 召回率（检索到的相关文档 / 总相关文档数）
                - f1: F1 分数（准确率和召回率的调和平均）
                - true_positives: 真阳性数量
                - false_positives: 假阳性数量
                - false_negatives: 假阴性数量
                - retrieved_count: 检索到的文档数
                - relevant_count: 相关文档总数

        Example:
            >>> evaluator = RAGEvaluator()
            >>> metrics = evaluator.evaluate_retrieval(
            ...     query="如何使用 Python",
            ...     retrieved_docs=[doc1, doc2, doc3],
            ...     relevant_docs=[doc1, doc4]
            ... )
            >>> print(f"准确率: {metrics['precision']:.2%}")
        """
        # 提取文档 ID
        try:
            retrieved_ids = self._extract_doc_ids(retrieved_docs, doc_id_field)
            relevant_ids = self._extract_doc_ids(relevant_docs, doc_id_field)
        except Exception as e:
            logger.error(f"提取文档 ID 失败: {e}")
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'true_positives': 0,
                'false_positives': 0,
                'false_negatives': 0,
                'retrieved_count': len(retrieved_docs),
                'relevant_count': len(relevant_docs),
                'error': str(e)
            }

        # 计算混淆矩阵
        true_positives = len(retrieved_ids & relevant_ids)
        false_positives = len(retrieved_ids - relevant_ids)
        false_negatives = len(relevant_ids - retrieved_ids)

        # 计算指标
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        metrics = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'retrieved_count': len(retrieved_ids),
            'relevant_count': len(relevant_ids),
            'query': query,
            'timestamp': datetime.now().isoformat()
        }

        # 记录评估结果
        self.evaluations.append(metrics)

        # 记录日志
        logger.info(
            f"检索质量评估 - 查询: {query[:50]}... | "
            f"准确率: {precision:.2%} | 召回率: {recall:.2%} | F1: {f1:.2%}"
        )

        return metrics

    def _extract_doc_ids(self, docs: List[Any], id_field: str) -> set:
        """
        从文档列表中提取 ID

        Args:
            docs: 文档列表
            id_field: ID 字段名称

        Returns:
            文档 ID 集合
        """
        doc_ids = set()
        for doc in docs:
            if hasattr(doc, 'metadata'):
                doc_id = doc.metadata.get(id_field)
                if doc_id:
                    doc_ids.add(str(doc_id))
            elif isinstance(doc, dict):
                doc_id = doc.get(id_field)
                if doc_id:
                    doc_ids.add(str(doc_id))
            else:
                # 尝试直接使用文档对象作为 ID
                doc_id = str(doc)
                doc_ids.add(doc_id)
        return doc_ids

    def log_rag_feedback(
        self,
        query: str,
        answer: str,
        feedback: int,
        retrieved_docs: Optional[List[Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        记录 RAG 回答的用户反馈

        Args:
            query: 用户查询
            answer: RAG 生成的回答
            feedback: 用户评分 (1-5)
                - 1: 非常不满意
                - 2: 不满意
                - 3: 一般
                - 4: 满意
                - 5: 非常满意
            retrieved_docs: 检索到的文档（可选）
            context: 额外的上下文信息（可选）

        Example:
            >>> evaluator = RAGEvaluator()
            >>> evaluator.log_rag_feedback(
            ...     query="如何使用 Python",
            ...     answer="Python 是一种高级编程语言...",
            ...     feedback=5
            ... )
        """
        if not 1 <= feedback <= 5:
            logger.warning(f"无效的反馈评分: {feedback}，应为 1-5")
            return

        feedback_record = {
            'query': query,
            'answer': answer,
            'feedback': feedback,
            'retrieved_docs_count': len(retrieved_docs) if retrieved_docs else 0,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }

        self.feedback_history.append(feedback_record)

        logger.info(
            f"RAG 用户反馈 - 查询: {query[:50]}... | "
            f"评分: {feedback}/5 | "
            f"检索文档数: {feedback_record['retrieved_docs_count']}"
        )

    def get_average_feedback(self, last_n: Optional[int] = None) -> float:
        """
        计算平均反馈分数

        Args:
            last_n: 只考虑最近 N 条反馈，None 表示全部

        Returns:
            平均反馈分数 (1-5)
        """
        if not self.feedback_history:
            return 0.0

        feedback_subset = self.feedback_history[-last_n:] if last_n else self.feedback_history
        scores = [f['feedback'] for f in feedback_subset]
        return sum(scores) / len(scores) if scores else 0.0

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取 RAG 性能摘要

        Returns:
            包含以下内容的字典:
                - total_evaluations: 总评估次数
                - avg_precision: 平均准确率
                - avg_recall: 平均召回率
                - avg_f1: 平均 F1 分数
                - total_feedback: 总反馈次数
                - avg_feedback: 平均反馈分数
                - recent_performance: 最近 10 次的性能
        """
        if not self.evaluations and not self.feedback_history:
            return {
                'message': '暂无评估数据',
                'total_evaluations': 0,
                'total_feedback': 0
            }

        summary = {
            'total_evaluations': len(self.evaluations),
            'total_feedback': len(self.feedback_history),
            'timestamp': datetime.now().isoformat()
        }

        # 计算平均检索指标
        if self.evaluations:
            summary['avg_precision'] = sum(e['precision'] for e in self.evaluations) / len(self.evaluations)
            summary['avg_recall'] = sum(e['recall'] for e in self.evaluations) / len(self.evaluations)
            summary['avg_f1'] = sum(e['f1'] for e in self.evaluations) / len(self.evaluations)

            # 最近 10 次性能
            recent_evals = self.evaluations[-10:]
            summary['recent_performance'] = {
                'avg_precision': sum(e['precision'] for e in recent_evals) / len(recent_evals),
                'avg_recall': sum(e['recall'] for e in recent_evals) / len(recent_evals),
                'avg_f1': sum(e['f1'] for e in recent_evals) / len(recent_evals)
            }

        # 计算平均反馈
        if self.feedback_history:
            summary['avg_feedback'] = self.get_average_feedback()
            summary['recent_feedback'] = self.get_average_feedback(last_n=10)

        return summary

    def export_evaluations(self, file_path: Optional[str] = None) -> str:
        """
        导出评估数据到 JSON 文件

        Args:
            file_path: 文件路径，None 表示使用默认路径

        Returns:
            导出的文件路径
        """
        import json

        if file_path is None:
            file_path = f"rag_evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'evaluations': self.evaluations,
            'feedback_history': self.feedback_history,
            'summary': self.get_performance_summary(),
            'exported_at': datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"评估数据已导出到: {file_path}")
        return file_path


class RAGMetricsTracker:
    """RAG 性能指标追踪器

    持久化存储和追踪 RAG 系统的性能指标。
    """

    def __init__(self, storage_path: str = "data/rag_metrics.json"):
        """
        初始化追踪器

        Args:
            storage_path: 指标存储文件路径
        """
        self.storage_path = Path(storage_path)
        self.metrics: Dict[str, Any] = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        """加载已保存的指标"""
        if self.storage_path.exists():
            import json
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载指标失败: {e}，返回空指标")
                return self._get_empty_metrics()
        else:
            # 创建父目录
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            return self._get_empty_metrics()

    def _get_empty_metrics(self) -> Dict[str, Any]:
        """返回空的指标结构"""
        return {
            'total_queries': 0,
            'total_retrievals': 0,
            'total_tokens_used': 0,
            'avg_precision': 0.0,
            'avg_recall': 0.0,
            'avg_feedback': 0.0,
            'daily_stats': {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

    def record_query(
        self,
        query: str,
        retrieved_count: int,
        tokens_used: int,
        conversation_id: Optional[str] = None
    ):
        """
        记录查询指标

        Args:
            query: 查询内容
            retrieved_count: 检索到的文档数量
            tokens_used: 使用的 token 数量
            conversation_id: 对话 ID（可选）
        """
        self.metrics['total_queries'] += 1
        self.metrics['total_retrievals'] += retrieved_count
        self.metrics['total_tokens_used'] += tokens_used

        # 记录每日统计
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.metrics['daily_stats']:
            self.metrics['daily_stats'][today] = {
                'queries': 0,
                'retrievals': 0,
                'tokens': 0
            }

        self.metrics['daily_stats'][today]['queries'] += 1
        self.metrics['daily_stats'][today]['retrievals'] += retrieved_count
        self.metrics['daily_stats'][today]['tokens'] += tokens_used

        self.metrics['updated_at'] = datetime.now().isoformat()
        self._save_metrics()

    def record_evaluation(self, precision: float, recall: float, f1: float):
        """
        记录评估指标

        Args:
            precision: 准确率
            recall: 召回率
            f1: F1 分数
        """
        # 更新平均值
        total = self.metrics['total_queries']
        current_avg_precision = self.metrics['avg_precision']
        current_avg_recall = self.metrics['avg_recall']
        current_avg_f1 = self.metrics['avg_f1']

        self.metrics['avg_precision'] = (
            (current_avg_precision * (total - 1) + precision) / total
        )
        self.metrics['avg_recall'] = (
            (current_avg_recall * (total - 1) + recall) / total
        )
        self.metrics['avg_f1'] = (
            (current_avg_f1 * (total - 1) + f1) / total
        )

        self.metrics['updated_at'] = datetime.now().isoformat()
        self._save_metrics()

    def record_feedback(self, feedback: int):
        """
        记录用户反馈

        Args:
            feedback: 反馈评分 (1-5)
        """
        total = self.metrics['total_queries']
        current_avg_feedback = self.metrics['avg_feedback']

        self.metrics['avg_feedback'] = (
            (current_avg_feedback * (total - 1) + feedback) / total
        )

        self.metrics['updated_at'] = datetime.now().isoformat()
        self._save_metrics()

    def _save_metrics(self):
        """保存指标到文件"""
        import json
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存指标失败: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        return self.metrics.copy()

    def reset_metrics(self):
        """重置所有指标"""
        self.metrics = self._get_empty_metrics()
        self._save_metrics()
        logger.info("RAG 指标已重置")


# 全局评估器实例（单例）
_global_evaluator: Optional[RAGEvaluator] = None
_global_metrics_tracker: Optional[RAGMetricsTracker] = None


def get_rag_evaluator() -> RAGEvaluator:
    """获取全局 RAG 评估器实例"""
    global _global_evaluator
    if _global_evaluator is None:
        _global_evaluator = RAGEvaluator()
    return _global_evaluator


def get_rag_metrics_tracker() -> RAGMetricsTracker:
    """获取全局 RAG 指标追踪器实例"""
    global _global_metrics_tracker
    if _global_metrics_tracker is None:
        _global_metrics_tracker = RAGMetricsTracker()
    return _global_metrics_tracker
