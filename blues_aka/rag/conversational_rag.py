"""上下文感知的 RAG Agent 模块

该模块提供了支持对话历史的检索增强生成（RAG）实现，
解决了传统 RAG 与对话历史分离的问题。

主要功能:
    - ConversationalRAGAgent: 支持对话历史的 RAG Agent
    - ContextAwareRAGAgent: 上下文感知检索的 RAG Agent
    - 查询重写和上下文增强
    - 检索结果与对话历史的协同

Author: Blues AKA Team
"""

import logging
from typing import Optional, List, Any, Dict
from langchain_core.retrievers import BaseRetriever
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)


class ConversationalRAGAgent:
    """
    支持对话历史的 RAG Agent

    将 RAG 检索与对话历史有机结合，实现上下文感知的问答。

    主要特性:
        1. 对话历史感知: 检索时考虑对话上下文
        2. 查询重写: 基于对话历史自动重写查询
        3. 历史压缩: 智能压缩对话历史以控制 token 使用
        4. 来源追踪: 记录检索到的文档来源

    使用示例:
        >>> from blues_aka.rag.conversational_rag import ConversationalRAGAgent
        >>>
        >>> agent = ConversationalRAGAgent(
        ...     retriever=retriever,
        ...     model=model,
        ...     max_history_tokens=2000
        ... )
        >>>
        >>> # 第一轮对话
        >>> result1 = agent.query("什么是机器学习？")
        >>> print(result1["answer"])
        >>>
        >>> # 第二轮对话（自动理解上下文）
        >>> result2 = agent.query("它有哪些应用？")
        >>> print(result2["answer"])  # 会理解为"机器学习的应用"
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        model: BaseChatModel,
        max_history_tokens: int = 2000,
        max_retrieved_docs: int = 5,
        enable_query_rewriting: bool = True,
        system_prompt: Optional[str] = None
    ):
        """
        初始化 ConversationalRAGAgent

        Args:
            retriever: 向量检索器实例
            model: 语言模型实例
            max_history_tokens: 对话历史的最大 token 数量
                - 用于控制传递给模型的上下文大小
                - 超过此限制时会自动压缩历史
                - 默认 2000
            max_retrieved_docs: 最大检索文档数量
                - 控制每次检索返回的文档数量
                - 默认 5
            enable_query_rewriting: 是否启用查询重写
                - 启用后会基于对话历史重写查询
                - 提高检索准确性
                - 默认 True
            system_prompt: 系统提示词
                - 如果为 None，使用默认提示词
                - 默认 None
        """
        self.retriever = retriever
        self.model = model
        self.max_history_tokens = max_history_tokens
        self.max_retrieved_docs = max_retrieved_docs
        self.enable_query_rewriting = enable_query_rewriting

        # 对话历史存储
        self.chat_history: List[BaseMessage] = []

        # 设置系统提示词
        if system_prompt is None:
            self.system_prompt = """你是一个智能问答助手，基于知识库回答用户问题。

回答要求:
1. 准确: 严格基于检索到的文档内容回答
2. 完整: 提供详细的解释和说明
3. 上下文感知: 理解对话历史，保持回答的连贯性
4. 引用来源: 在回答末尾列出参考的文档来源

如果文档中没有相关信息，诚实地告诉用户知识库中没有找到相关内容。"""
        else:
            self.system_prompt = system_prompt

        logger.info("ConversationalRAGAgent 初始化完成")
        logger.info(f"最大历史 token: {max_history_tokens}")
        logger.info(f"最大检索文档数: {max_retrieved_docs}")
        logger.info(f"查询重写: {enable_query_rewriting}")

    def query(
        self,
        question: str,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        执行带对话历史的查询

        Args:
            question: 用户问题
            return_sources: 是否返回来源信息
                - True: 返回 sources 和 retrieved_documents
                - False: 只返回 answer
                - 默认 True

        Returns:
            Dict[str, Any]: 查询结果，包含:
                - answer (str): 生成的回答
                - sources (List[str]): 来源文档列表（如果 return_sources=True）
                - retrieved_documents (List[Document]): 检索到的文档（如果 return_sources=True）
                - rewritten_query (str): 重写后的查询（如果启用了查询重写）

        Example:
            >>> result = agent.query("什么是深度学习？")
            >>> print(result["answer"])
            >>> print(result["sources"])
        """
        try:
            logger.info(f"查询问题: {question[:50]}...")

            # 1. 查询重写（如果启用）
            if self.enable_query_rewriting and self.chat_history:
                rewritten_query = self._rewrite_query(question, self.chat_history)
                logger.debug(f"原始查询: {question}")
                logger.debug(f"重写查询: {rewritten_query}")
                search_query = rewritten_query
            else:
                search_query = question

            # 2. 检索相关文档
            retrieved_docs = self.retriever.get_relevant_documents(
                search_query,
                **{"k": self.max_retrieved_docs}
            )

            logger.info(f"检索到 {len(retrieved_docs)} 个文档")

            # 3. 构建上下文
            context = self._build_context(retrieved_docs)

            # 4. 构建完整的提示
            messages = self._build_messages(question, context)

            # 5. 生成回答
            response = self.model.invoke(messages)
            answer = response.content if hasattr(response, 'content') else str(response)

            # 6. 保存到对话历史
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=answer))

            # 7. 压缩对话历史（如果需要）
            self._compress_history()

            # 8. 构建返回结果
            result = {"answer": answer}

            if return_sources:
                result["sources"] = self._extract_sources(retrieved_docs)
                result["retrieved_documents"] = retrieved_docs

            if self.enable_query_rewriting and self.chat_history:
                result["rewritten_query"] = search_query

            logger.info("查询完成")
            return result

        except Exception as e:
            logger.error(f"查询失败: {e}", exc_info=True)
            raise

    def _rewrite_query(
        self,
        query: str,
        chat_history: List[BaseMessage]
    ) -> str:
        """
        基于对话历史重写查询

        将简短或不完整的查询，结合对话历史重写为更明确的查询。

        Args:
            query: 原始查询
            chat_history: 对话历史

        Returns:
            str: 重写后的查询
        """
        try:
            # 获取最近的对话（限制数量以控制 token）
            recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history

            # 构建历史上下文
            history_text = "\n".join([
                f"{msg.__class__.__name__}: {msg.content}"
                for msg in recent_history
            ])

            # 使用 LLM 重写查询
            rewrite_prompt = ChatPromptTemplate.from_messages([
                ("system", """你是一个查询重写助手。基于对话历史，将用户的当前问题重写为一个更明确、更完整的独立查询。

规则:
1. 重写后的查询应该是一个独立的、完整的查询
2. 包含对话历史中相关的上下文信息
3. 保持原始问题的意图
4. 只返回重写后的查询，不要有其他内容

示例:
历史: User: 什么是机器学习？
      Assistant: 机器学习是...
当前问题: 它有哪些应用？
重写: 机器学习有哪些应用？"""),
                ("user", "对话历史:\n{history}\n\n当前问题: {question}\n\n重写后的查询:")
            ])

            chain = rewrite_prompt | self.model
            result = chain.invoke({
                "history": history_text,
                "question": query
            })

            rewritten = result.content if hasattr(result, 'content') else str(result)
            logger.debug(f"查询重写: '{query}' -> '{rewritten}'")
            return rewritten.strip()

        except Exception as e:
            logger.warning(f"查询重写失败，使用原始查询: {e}")
            return query

    def _build_context(self, documents: List[Document]) -> str:
        """
        构建文档上下文

        将检索到的文档组合成一个统一的上下文字符串。

        Args:
            documents: 检索到的文档列表

        Returns:
            str: 组合后的上下文
        """
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", doc.metadata.get("filename", "未知来源"))
            content = doc.page_content
            context_parts.append(f"[文档 {i}] (来源: {source})\n{content}\n")

        return "\n".join(context_parts)

    def _build_messages(
        self,
        question: str,
        context: str
    ) -> List[BaseMessage]:
        """
        构建完整的消息列表

        Args:
            question: 用户问题
            context: 检索到的文档上下文

        Returns:
            List[BaseMessage]: 消息列表
        """
        messages = []

        # 系统提示词
        messages.append(("system", self.system_prompt))

        # 添加压缩后的对话历史（如果有）
        if self.chat_history:
            messages.extend(self.chat_history[-10:])  # 限制历史数量

        # 构建用户消息
        user_message = f"""基于以下文档内容回答问题:

{context}

问题: {question}"""

        messages.append(("user", user_message))

        return messages

    def _compress_history(self):
        """
        压缩对话历史

        当对话历史超过 max_history_tokens 时，智能压缩历史记录。
        保留最近的对话和关键信息。
        """
        if not self.chat_history:
            return

        # 估算 token 数量（粗略估计：1 token ≈ 2 字符）
        total_chars = sum(len(msg.content) for msg in self.chat_history)
        estimated_tokens = total_chars // 2

        if estimated_tokens > self.max_history_tokens:
            # 保留最近的对话
            # 从后往前添加，直到接近 token 限制
            compressed = []
            current_tokens = 0

            for msg in reversed(self.chat_history):
                msg_tokens = len(msg.content) // 2 + 10

                if current_tokens + msg_tokens > self.max_history_tokens:
                    break

                compressed.insert(0, msg)
                current_tokens += msg_tokens

            self.chat_history = compressed
            logger.info(f"对话历史已压缩: {len(compressed)} 条消息")

    def _extract_sources(self, documents: List[Document]) -> List[str]:
        """
        提取文档来源

        Args:
            documents: 文档列表

        Returns:
            List[str]: 去重后的来源列表
        """
        sources = []
        seen = set()

        for doc in documents:
            source = doc.metadata.get("source") or doc.metadata.get("filename", "未知来源")
            if source not in seen:
                sources.append(source)
                seen.add(source)

        return sources

    def clear_history(self):
        """清除对话历史"""
        self.chat_history = []
        logger.info("对话历史已清除")

    def get_history(self) -> List[BaseMessage]:
        """
        获取当前对话历史

        Returns:
            List[BaseMessage]: 对话历史副本
        """
        return list(self.chat_history)

    def set_history(self, history: List[BaseMessage]):
        """
        设置对话历史

        Args:
            history: 新的对话历史
        """
        self.chat_history = list(history)
        logger.info(f"对话历史已设置: {len(history)} 条消息")
