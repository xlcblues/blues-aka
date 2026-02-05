"""RAG Agent 模块

该模块提供了基于检索增强生成（RAG）的智能问答代理功能。
通过将向量检索器与语言模型结合，实现对知识库的智能问答。

主要功能:
    - create_rag_agent: 创建标准的 RAG Agent
    - create_conversational_rag_agent: 创建支持对话历史的 RAG Agent
    - query_rag_agent: 同步查询 RAG Agent
    - aquery_rag_agent: 异步查询 RAG Agent
    - format_rag_response: 格式化 RAG 响应结果

Example:
    >>> from blues_aka.rag.rag_agent import create_rag_agent, query_rag_agent
    >>> from blues_aka.rag.retrievers import create_retriever
    >>>
    >>> retriever = create_retriever(vector_store)
    >>> agent = create_rag_agent(retriever)
    >>> result = query_rag_agent(agent, "什么是机器学习？")
    >>> print(result["answer"])
"""
import logging
from typing import Optional, List, Any, Dict

from langchain.agents import create_agent
from langchain_core.retrievers import BaseRetriever

from blues_aka.core import get_model_string
from blues_aka.rag.retrievers import create_retriever_tool

logger = logging.getLogger(__name__)

# 默认的 RAG 系统提示词
DEFAULT_RAG_SYSTEM_PROMPT = """你是一个智能问答助手，专门回答基于知识库的问题。

你的任务：
1. 使用 knowledge_base 工具搜索相关信息
2. 基于检索到的文档内容回答用户问题
3. 如果文档中没有相关信息，诚实地告诉用户
4. 在回答中引用来源文档（如果有 source 信息）

回答要求：
- 准确：严格基于文档内容，不要编造信息
- 完整：尽可能提供详细的回答
- 清晰：使用简洁明了的语言
- 引用：在回答末尾列出参考的文档来源

示例回答格式：
[回答内容]

参考来源：
- 文档1: [来源信息]
- 文档2: [来源信息]
"""

def create_rag_agent(
    retriever: BaseRetriever,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tool_name: str = "knowledge_base",
    tool_description: Optional[str] = None,
    streaming: bool = True,
    **kwargs,
):
    """创建 RAG Agent

    创建一个基于检索增强生成的智能问答代理，可以使用知识库回答用户问题。

    Args:
        retriever (BaseRetriever): 向量检索器实例，用于从知识库中检索相关文档
        model (Optional[str]): 使用的语言模型名称，如果为 None 则使用配置文件中的默认模型
            默认值: None
        system_prompt (Optional[str]): 系统提示词，用于定义 Agent 的行为和回答风格
            如果为 None 则使用 DEFAULT_RAG_SYSTEM_PROMPT
            默认值: None
        tool_name (str): 检索工具的名称
            默认值: "knowledge_base"
        tool_description (Optional[str]): 检索工具的描述，帮助 Agent 理解何时使用该工具
            如果为 None 则使用默认描述
            默认值: None
        streaming (bool): 是否启用流式输出
            默认值: True
        **kwargs: 传递给 create_agent 的其他参数

    Returns:
        创建的 Agent 实例，可用于执行查询

    Note:
        - Agent 会自动创建一个检索工具，用于从知识库中获取信息
        - 默认系统提示词要求 Agent 基于文档内容回答，不要编造信息
        - Agent 会引用来源文档，提供可追溯的答案

    Example:
        >>> from blues_aka.rag.retrievers import create_retriever
        >>> retriever = create_retriever(vector_store)
        >>> agent = create_rag_agent(retriever, model="gpt-4")
        >>> result = agent.invoke({"messages": [{"role": "user", "content": "问题"}]})
    """
    logger.info("创建 RAG Agent")

    if model is None:
        model = get_model_string()

    if system_prompt is None:
        system_prompt = DEFAULT_RAG_SYSTEM_PROMPT

    if tool_description is None:
        tool_description = (
            "搜索知识库中的相关信息。"
            "当需要回答关于文档内容的问题时使用此工具。"
            "输入应该是一个搜索查询。"
        )

    retriever_tool = create_retriever_tool(
        retriever=retriever,
        name=tool_name,
        description=tool_description,
    )
    tools = [retriever_tool]
    logger.debug("创建 Agent...")
    agent = create_agent(
        model=model,
        system_prompt=system_prompt,
        tools=tools,
        **kwargs,
    )
    logger.info(f"RAG Agent 创建成功")
    logger.info(f"模型: {model}")
    logger.info(f"流式输出: {streaming}")
    return agent

def format_rag_response(
    output: str,
    intermediate_steps: Optional[List] = None,
) -> Dict[str, Any]:
    """格式化 RAG 响应，提取来源文档

    从 Agent 的执行结果中提取答案、来源文档和检索到的文档内容。

    Args:
        output (str): Agent 生成的回答文本
        intermediate_steps (Optional[List]): Agent 执行过程中的中间步骤，
            包含使用的工具和检索到的文档
            默认值: None

    Returns:
        Dict[str, Any]: 格式化的响应字典，包含:
            - answer (str): Agent 的回答
            - sources (List[str]): 来源文档列表（去重后的文件路径）
            - retrieved_documents (List): 检索到的文档对象列表

    Note:
        - 如果中间步骤为 None，返回只包含 answer 的字典
        - sources 从文档的 metadata.source 或 metadata.filename 字段提取
        - 只有当工具名称包含 "knowledge" 时才提取文档信息

    Example:
        >>> result = format_rag_response(
        >>>     output="这是一个答案...",
        >>>     intermediate_steps=agent_steps
        >>> )
        >>> print(result["answer"])
        >>> print(result["sources"])
    """
    response = {
        "answer": output,
        "sources": [],
        "retrieved_documents": [],
    }

    if not intermediate_steps:
        return response

    for step in intermediate_steps:
        if len(step) >= 2:
            action, observation = step[0], step[1]

            if hasattr(action, "tool") and "knowledge" in action.tool.lower():
                if isinstance(observation, list):
                    for doc in observation:
                        response["retrieved_documents"].append(doc)

                        if hasattr(doc, "metadata") and doc.metadata:
                            source = doc.metadata.get("source") or doc.metadata.get("filename")
                            if source and source not in response["sources"]:
                                response["sources"].append(source)

    return response

def create_conversational_rag_agent(
    retriever: BaseRetriever,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    **kwargs,
):
    """创建支持对话历史的 RAG Agent

    创建一个可以保持对话历史的 RAG Agent，实现多轮对话问答。

    Args:
        retriever (BaseRetriever): 向量检索器实例
        model (Optional[str]): 使用的语言模型名称
            默认值: None (使用配置文件中的默认模型)
        system_prompt (Optional[str]): 系统提示词
            默认值: None (使用默认提示词)
        **kwargs: 传递给 create_rag_agent 的其他参数

    Returns:
        支持对话历史的 Agent 实例

    Note:
        - 该函数是 create_rag_agent 的别名，专门用于支持对话场景
        - Agent 可以记住之前的对话上下文，实现连贯的多轮对话

    Example:
        >>> agent = create_conversational_rag_agent(retriever)
        >>> # 第一轮对话
        >>> result1 = agent.invoke({"messages": [{"role": "user", "content": "什么是AI？"}]})
        >>> # 第二轮对话（可以引用之前的内容）
        >>> result2 = agent.invoke({"messages": [
        >>>     {"role": "user", "content": "它有哪些应用？"}
        >>> ]})
    """
    logger.info("创建对话式 RAG Agent")
    return create_rag_agent(
        retriever=retriever,
        model=model,
        system_prompt=system_prompt,
        **kwargs,
    )


def query_rag_agent(
        agent,
        query: str,
        return_sources: bool = True,
) -> Dict[str, Any]:
    """查询 RAG Agent 的便捷函数

    向 RAG Agent 发送查询并获取格式化的响应结果。

    Args:
        agent: RAG Agent 实例
        query (str): 用户查询问题
        return_sources (bool): 是否返回来源信息（当前版本未使用此参数）
            默认值: True

    Returns:
        Dict[str, Any]: 格式化的响应字典，包含:
            - answer (str): Agent 的回答

    Raises:
        Exception: 查询执行失败时抛出异常

    Note:
        - 自动处理 Agent 的输入格式，使用 LangChain 1.0.3 的消息格式
        - 从返回结果中提取最后一条消息的内容作为答案
        - 查询前会记录日志（截取前50个字符）

    Example:
        >>> agent = create_rag_agent(retriever)
        >>> result = query_rag_agent(agent, "什么是深度学习？")
        >>> print(result["answer"])
    """
    logger.info(f"查询 RAG Agent: {query[:50]}...")

    try:
        # 执行查询 - LangChain 1.0.3 的 agent 需要字典输入
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})

        # 提取回答
        if isinstance(result, dict) and "messages" in result:
            # 获取最后一条消息
            messages = result["messages"]
            if messages:
                answer = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            else:
                answer = str(result)
        else:
            answer = str(result)

        # 格式化响应
        formatted = {"answer": answer}

        logger.info("查询完成")
        return formatted

    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise

async def aquery_rag_agent(
        agent,
        query: str,
        return_sources: bool = True,
) -> Dict[str, Any]:
    """异步查询 RAG Agent

    异步向 RAG Agent 发送查询并获取格式化的响应结果。

    Args:
        agent: RAG Agent 实例
        query (str): 用户查询问题
        return_sources (bool): 是否返回来源信息（当前版本未使用此参数）
            默认值: True

    Returns:
        Dict[str, Any]: 格式化的响应字典，包含:
            - answer (str): Agent 的回答

    Raises:
        Exception: 查询执行失败时抛出异常

    Note:
        - 这是 query_rag_agent 的异步版本，适用于需要异步处理的场景
        - 使用 agent.ainvoke 进行异步调用
        - 自动处理 Agent 的输入格式，使用 LangChain 1.0.3 的消息格式
        - 从返回结果中提取最后一条消息的内容作为答案

    Example:
        agent = create_rag_agent(retriever)
        result = await aquery_rag_agent(agent, "什么是深度学习？")
        print(result["answer"])
    """
    logger.info(f"异步查询 RAG Agent: {query[:50]}...")

    try:
        # 异步执行查询 - LangChain 1.0.3 的 agent 需要字典输入
        result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})

        # 提取回答
        if isinstance(result, dict) and "messages" in result:
            # 获取最后一条消息
            messages = result["messages"]
            if messages:
                answer = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            else:
                answer = str(result)
        else:
            answer = str(result)

        # 格式化响应
        formatted = {"answer": answer}

        logger.info("异步查询完成")
        return formatted

    except Exception as e:
        logger.error(f"异步查询失败: {e}")
        raise