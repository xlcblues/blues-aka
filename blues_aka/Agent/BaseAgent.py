"""
BaseAgent 智能体基类模块

本模块提供了智能体（Agent）的核心实现，基于 LangChain 和 LangGraph 框架构建。
支持同步/异步调用、流式输出、工具调用和 RAG（检索增强生成）功能。

主要功能：
    1. 智能体管理
       - 支持多种大语言模型（通过模型名称或实例）
       - 自动工具管理和调用
       - 可配置的系统提示词
       - 调试模式支持

    2. 调用模式
       - 同步调用（invoke）
       - 异步调用（ainvoke）
       - 流式输出（streaming）
       - 异步流式输出（astreaming）

    3. RAG 支持
       - 自动创建 RAG 检索工具
       - 支持自定义检索配置
       - 向量索引管理

    4. 工具系统
       - 内置基础工具集
       - 支持自定义工具
       - 自动工具描述生成

使用示例：
    # 创建基础智能体
    agent = BaseAgent(model="glm-4.5")
    response = agent.invoke("你好")

    # 创建带 RAG 的智能体
    agent = BaseAgent(
        model="glm-4.5",
        enable_rag=True,
        rag_index_name="my_knowledge_base"
    )

    # 流式输出
    for chunk in agent.streaming("请介绍自己"):
        print(chunk, end="")

Author: Blues AKA Team
"""

import logging
from importlib.metadata import metadata
from typing import Optional, Union, Sequence, Any, List, Iterator, Literal, AsyncIterator, Tuple, Dict
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langgraph.types import Command
from langchain_classic.memory import ConversationTokenBufferMemory
from langgraph.checkpoint.memory import MemorySaver

from blues_aka.config.config import ConfigFactory
from blues_aka.core.prompts import get_prompt_with_tools, get_system_prompt
from blues_aka.core.tools import BASIC_TOOLS
from blues_aka.core.models import get_chat_model
from blues_aka.rag.embeddings import get_embeddings
from blues_aka.rag.index_manager import IndexManager
from blues_aka.rag.retrievers import create_retriever, create_retriever_tool

logger = logging.getLogger(__name__)

# SqliteSaver 需要单独安装，可选导入
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    SQLITE_SAVER_AVAILABLE = True
except ImportError:
    SQLITE_SAVER_AVAILABLE = False
    logger.warning("SqliteSaver 不可用，如需使用 SQLite 持久化，请安装: pip install langgraph-checkpoint-sqlite")

# 获取配置实例
_config = ConfigFactory.get_config()

class BaseAgent:
    """
    智能体基类

    提供了一个功能完整的 AI 智能体实现，支持多种调用模式、工具使用和 RAG 功能。
    基于 LangChain 框架构建，使用 LangGraph 实现状态图管理。

    主要特性：
        1. 多模型支持：支持通过模型名称或模型实例初始化
        2. 工具系统：内置基础工具集，支持自定义工具
        3. RAG 集成：可选的检索增强生成功能
        4. 多种调用模式：同步、异步、流式输出
        5. 灵活配置：支持自定义系统提示词和调试模式

    初始化参数：
        model: 模型配置（字符串、模型实例或 None 使用默认）
        tools: 工具列表（None 使用基础工具集）
        system_prompt: 系统提示词（None 自动生成）
        prompt_mode: 提示词模式（default/creative/precise 等）
        debug: 是否启用调试模式
        enable_rag: 是否启用 RAG 功能
        rag_index_name: RAG 知识库索引名称
        rag_config: RAG 检索配置参数

    使用示例：
        # 基础使用
        agent = BaseAgent(model="glm-4.5")
        response = agent.invoke("你好，请介绍一下自己")

        # 带工具的智能体
        agent = BaseAgent(
            model="glm-4.5",
            tools=[custom_tool],
            system_prompt="你是一个专业的助手"
        )

        # RAG 增强
        agent = BaseAgent(
            model="glm-4.5",
            enable_rag=True,
            rag_index_name="tech_docs"
        )

        # 流式输出
        for chunk in agent.streaming("写一首诗"):
            print(chunk, end="")

    属性：
        model: 语言模型实例
        tools: 可用工具列表
        system_prompt: 系统提示词
        enable_rag: 是否启用 RAG
        rag_index_name: RAG 索引名称
        rag_config: RAG 配置
        graph: LangGraph 状态图实例
        debug: 调试模式标志
    """

    def __init__(
            self,
            model: Optional[Union[str, BaseChatModel]] = None,
            tools: Optional[Sequence[BaseTool]] = None,
            system_prompt: Optional[str] = None,
            prompt_mode: str = "default",
            debug: bool = False,
            enable_rag: bool = False,
            rag_index_name: Optional[str] = None,
            rag_config: Optional[dict] = None,
            enable_thinking: bool = False,
            max_token_limit: int = 2000,
            enable_memory: bool = False,
            enable_checkpointing: bool = False,
            checkpoint_db_path: Optional[str] = None,
            **kwargs: Any):
        """
        初始化智能体实例

        创建一个配置完整的智能体，支持模型选择、工具集成和 RAG 功能。

        Args:
            model: 模型配置，支持以下格式：
                - None: 使用系统默认模型
                - str: 模型名称（如 "glm-4.5"）或带提供商前缀（如 "zhipuai:glm-4.5"）
                - BaseChatModel: 已初始化的模型实例
            tools: 工具列表
                - None: 使用内置基础工具集（BASIC_TOOLS）
                - Sequence[BaseTool]: 自定义工具列表
                - []: 空列表，不使用任何工具
            system_prompt: 系统提示词
                - None: 根据是否有工具自动生成
                - str: 自定义系统提示词
            prompt_mode: 提示词模式，影响自动生成的提示词风格
                - "default": 默认模式
                - "creative": 创意模式
                - "precise": 精确模式
                - 其他自定义模式
            debug: 是否启用调试模式，启用后会输出详细的执行信息
            enable_rag: 是否启用 RAG（检索增强生成）功能
            rag_index_name: RAG 知识库索引名称
                - 当 enable_rag=True 时必填
                - 必须是已创建的知识库索引
            rag_config: RAG 检索配置参数
                - search_type: 检索类型（"similarity", "mmr"）
                - k: 检索的文档数量
                - score_threshold: 相似度阈值
                - 其他检索参数
            max_token_limit: 记忆组件的 token 限制
                - 默认 2000，用于限制对话历史的 token 数量
                - 超过此限制时会自动截断早期对话
                - 仅在 enable_memory=True 时有效
            enable_memory: 是否启用记忆组件
                - 默认 False，禁用以避免性能问题
                - 启用后会使用 ConversationTokenBufferMemory 管理对话历史
                - 注意: 每次创建新 Agent 实例时记忆会重置
            enable_checkpointing: 是否启用 Checkpointing 状态持久化
                - 默认 False，禁用以避免额外的存储开销
                - 启用后会使用 LangGraph 的 Checkpointing 功能持久化会话状态
                - 支持跨请求的会话状态保持，使用 thread_id 标识会话
                - 比 enable_memory 更强大，支持状态快照和回滚
            checkpoint_db_path: Checkpoint 数据库路径
                - None: 使用内存存储 (MemorySaver)
                - str: SQLite 数据库路径 (SqliteSaver)
                - 建议生产环境使用 SQLite 持久化
            **kwargs: 传递给 create_agent 的额外参数

        Raises:
            Exception: 当模型初始化失败或 Agent 创建失败时抛出异常

        初始化流程：
            1. 模型初始化：根据 model 参数创建或使用模型实例
            2. 工具配置：设置可用工具列表
            3. RAG 配置：如果启用 RAG，创建并添加检索工具
            4. 提示词配置：设置或生成系统提示词
            5. Agent 创建：使用 LangGraph 创建状态图

        示例：
            # 使用默认模型和工具
            agent = BaseAgent()

            # 指定模型
            agent = BaseAgent(model="glm-4.5")

            # 自定义工具
            agent = BaseAgent(tools=[my_tool])

            # 启用 RAG
            agent = BaseAgent(
                enable_rag=True,
                rag_index_name="my_kb",
                rag_config={"k": 5, "score_threshold": 0.7}
            )

            # 完整配置
            agent = BaseAgent(
                model="glm-4.5",
                tools=[search_tool],
                system_prompt="你是一个专业的助手",
                prompt_mode="precise",
                debug=True
            )
        """

        # 初始化模型 - 将字符串转换为模型实例
        if model is None:
            if enable_thinking:
                self.model = get_chat_model(
                    model_name=_config.default_model,
                    thinking_type="enabled"
                )
                logger.info(f"使用默认模型（启用深度思考）: {_config.default_model}")
            else:
                self.model = get_chat_model(model_name=_config.default_model)
                logger.info(f"使用默认模型: {_config.default_model}")

        elif isinstance(model, str):
            # 如果是字符串，创建模型实例
            # 检查是否已经有提供商前缀 (如 "zhipuai:glm-4.5")
            if ':' in model:
                # 有前缀，直接使用
                if enable_thinking:
                    self.model = get_chat_model(model_name=model.split(':', 1)[1], thinking_type="enabled")
                    logger.info(f"使用模型（带前缀）: {model}")
                else:
                    self.model = get_chat_model(model_name=model.split(':', 1)[1], thinking_type="disabled")
            else:
                # 没有前缀，使用模型名称
                if enable_thinking:
                    self.model = get_chat_model(model_name=model, thinking_type="enabled")
                    logger.info(f"使用模型: {model}")
                else:
                    self.model = get_chat_model(model_name=model, thinking_type="disabled")

        else:
            self.model = model
            self.model = model
            if enable_thinking:
                logger.warning("传入的是模型实例，无法自动启用深度思考")

        # 初始化工具
        if tools is None:
            self.tools = BASIC_TOOLS
        else:
            self.tools = list(tools) if tools else []

        if self.tools:
            tool_names = [tool.name for tool in self.tools]
            logger.debug(f"   工具列表: {', '.join(tool_names)}")

        # RAG 配置处理
        self.enable_rag = enable_rag
        self.rag_index_name = rag_index_name
        self.rag_config = rag_config or {}

        if enable_rag and rag_index_name:
            logger.info(f"启用 RAG 模式，索引名称: {rag_index_name}")
            rag_tool = self._create_rag_tool(rag_index_name, rag_config)
            if rag_tool:
                self.tools.append(rag_tool)
                logger.info(f"RAG 工具已添加到工具列表: {rag_tool.name}")
            else:
                logger.warning(f"RAG 工具创建失败，将继续使用基础工具")

        # 初始化提示词
        if system_prompt is None:
            if self.tools:
                self.system_prompt = get_prompt_with_tools(mode=prompt_mode)
            else:
                self.system_prompt = get_system_prompt(mode=prompt_mode)
        else:
            self.system_prompt = system_prompt

        self.debug = debug
        self.enable_thinking = enable_thinking
        self.max_token_limit = max_token_limit
        self.enable_memory = enable_memory
        self.enable_checkpointing = enable_checkpointing
        self.checkpoint_db_path = checkpoint_db_path

        # 初始化记忆组件 - 使用 LangChain 的 ConversationTokenBufferMemory
        # 注意: 默认禁用,因为每次创建新 Agent 实例时记忆会重置
        # 只有在需要长期保持状态的场景下才启用
        if enable_memory:
            self.memory = ConversationTokenBufferMemory(
                max_token_limit=max_token_limit,  # 限制记忆的 token 数量
                return_messages=True,  # 返回消息对象而非字符串，保持格式一致性
                llm=self.model  # 传递模型用于准确计算 token 数量
            )
            logger.info(f"记忆组件已初始化，max_token_limit={max_token_limit}")
        else:
            self.memory = None
            logger.info("记忆组件未启用(默认)")

        # 初始化 Checkpointer - 支持 LangGraph Checkpointing
        # Checkpointing 提供了更强大的状态持久化能力，支持:
        # 1. 跨请求的会话状态保持 (使用 thread_id)
        # 2. 状态快照和回滚
        # 3. 断点续传
        # 4. 多会话管理
        self.checkpointer = None
        if enable_checkpointing:
            if checkpoint_db_path:
                # 使用 SQLite 持久化存储（推荐生产环境）
                if SQLITE_SAVER_AVAILABLE:
                    try:
                        self.checkpointer = SqliteSaver.from_conn_string(checkpoint_db_path)
                        logger.info(f"Checkpointing 已启用（SQLite）: {checkpoint_db_path}")
                    except Exception as e:
                        logger.warning(f"SQLite Checkpointer 初始化失败: {e}，回退到内存存储")
                        self.checkpointer = MemorySaver()
                        logger.info("Checkpointing 已启用（内存存储）")
                else:
                    logger.warning("SqliteSaver 不可用，使用内存存储。建议安装: pip install langgraph-checkpoint-sqlite")
                    self.checkpointer = MemorySaver()
                    logger.info("Checkpointing 已启用（内存存储）")
            else:
                # 使用内存存储（适合开发环境）
                self.checkpointer = MemorySaver()
                logger.info("Checkpointing 已启用（内存存储）")
        else:
            logger.info("Checkpointing 未启用(默认)")

        try:
            # 创建Agent，传入 checkpointer
            self.graph = create_agent(
                model=self.model,
                tools=self.tools if self.tools else None,
                system_prompt=self.system_prompt,
                debug=self.debug,
                checkpointer=self.checkpointer,  # 添加 checkpointer
                **kwargs,
            )
            logger.info("Agent 创建成功（CompiledStateGraph）")
            logger.debug(f"配置: debug={self.debug}, tools={len(self.tools)}, checkpointing={enable_checkpointing}")
        except Exception as e:
            logger.error(e)
            raise e

    # 普通输出
    def invoke(
        self,
        input_text: str,
        chat_history: Optional[List[BaseMessage]] = None,
        thread_id: Optional[str] = None,
        **kwargs: Any) -> str:
        """
        同步调用智能体

        以同步方式调用智能体处理输入文本，返回完整的响应结果。
        适用于不需要实时输出的场景。

        Args:
            input_text (str): 用户输入的文本内容
            chat_history (Optional[List[BaseMessage]]): 聊天历史记录
                - None: 不使用历史记录
                - List[BaseMessage]: 包含 HumanMessage 和 AIMessage 的列表
                - 注意: 如果启用了 checkpointing 并提供 thread_id，chat_history 会被忽略
                        因为状态会从 checkpointer 中自动加载
            thread_id (Optional[str]): 会话线程ID
                - 用于标识和持久化会话状态
                - 当启用 checkpointing 时，相同的 thread_id 会自动恢复之前的会话状态
                - 格式建议: "conv_{conversation_id}" 或 "user_{user_id}_{timestamp}"
                - 如果为 None，则不使用持久化状态
            **kwargs: 传递给 Agent 的额外参数

        Returns:
            str: 智能体的响应文本

        Raises:
            Exception: 当 Agent 执行失败时抛出异常

        处理流程：
            1. 构建消息列表：
               - 如果提供 chat_history，将其添加到消息列表
               - 将 input_text 包装为 HumanMessage 并添加到列表
            2. 调用 Agent：将消息列表传递给 LangGraph
            3. 提取响应：从返回的消息中提取最后一条 AI 消息
            4. 返回结果：返回 AI 消息的内容

        示例：
            # 基础调用
            agent = BaseAgent(model="glm-4.5")
            response = agent.invoke("你好")
            print(response)

            # 带历史记录的调用
            history = [
                HumanMessage(content="我叫张三"),
                AIMessage(content="你好张三，很高兴认识你")
            ]
            response = agent.invoke("我叫什么名字？", chat_history=history)

            # 带额外参数
            response = agent.invoke(
                "帮我查询天气",
                temperature=0.7,
                max_tokens=1000
            )

        注意事项：
            - 这是一个同步方法，会阻塞直到收到完整响应
            - 对于长响应，建议使用 streaming() 方法获得更好的用户体验
            - chat_history 中的消息顺序应为时间正序（从早到晚）
        """

        try:
            messages = []

            # 如果启用了 checkpointing 并提供了 thread_id，使用 checkpointer 的状态
            # 否则，使用传统的 chat_history 或 memory 方式
            config = None
            if self.enable_checkpointing and thread_id:
                config = {"configurable": {"thread_id": thread_id}}
                logger.debug(f"使用 Checkpointing 状态管理: thread_id={thread_id}")
                # 不需要手动添加 chat_history，checkpointer 会自动加载历史状态
            else:
                # 只有启用记忆组件时才使用
                if self.enable_memory and self.memory:
                    # 方案1: 如果提供了 chat_history，先将其添加到记忆组件
                    if chat_history:
                        # 将传入的历史记录添加到记忆中
                        for msg in chat_history:
                            if isinstance(msg, HumanMessage):
                                self.memory.chat_memory.add_user_message(msg.content)
                            elif isinstance(msg, AIMessage):
                                self.memory.chat_memory.add_ai_message(msg.content)

                    # 从记忆组件加载智能截断后的历史记录
                    # 这样可以控制传递给模型的 token 数量，避免成本随对话长度线性增长
                    memory_variables = self.memory.load_memory_variables({})
                    memory_history = memory_variables.get("history", [])

                    # 将记忆中的历史添加到消息列表
                    if memory_history:
                        messages.extend(memory_history)
                else:
                    # 如果未启用记忆组件，直接使用传入的 chat_history
                    if chat_history:
                        messages.extend(chat_history)

            # 添加当前用户输入
            messages.append(HumanMessage(content=input_text))

            graph_input = {"messages": messages}
            graph_input.update(kwargs)

            # 调用 graph，传入 config (如果使用了 checkpointing)
            result = self.graph.invoke(graph_input, config=config)
            output_messages = result.get("messages", [])

            ai_response = ""
            for msg in reversed(output_messages):
                if isinstance(msg, AIMessage):
                    ai_response = msg.content
                    break

            # 如果未使用 checkpointing，手动保存到记忆组件
            if not (self.enable_checkpointing and thread_id):
                if self.enable_memory and self.memory:
                    # 将当前交互保存到记忆组件
                    # 这样可以在下次调用时自动使用，而无需手动传递完整历史
                    self.memory.save_context(
                        {"input": input_text},
                        {"output": ai_response}
                    )
                    logger.debug(f"记忆中的消息数: {len(self.memory.chat_memory.messages)}")

            logger.info(f"Agent 调用完成，输出长度: {len(ai_response)} 字符")
            logger.debug(f"输出: {ai_response[:100]}...")

            return ai_response


        except Exception as e:
            error_msg = f"Agent 执行失败: {str(e)}"
            logger.error(f"{error_msg}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    # 流式输出
    def streaming(
            self,
            input_text: str,
            chat_history: Optional[List[BaseMessage]] = None,
            thread_id: Optional[str] = None,
            stream_mode: Union[
                Literal["values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"],
                Sequence[Literal["values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"]]
            ] = "messages",
            **kwargs: Any
    ) -> Iterator[str]:
        """
        流式调用智能体

        以流式方式调用智能体，实时生成并返回响应内容。
        适用于需要实时显示或处理响应的场景。

        Args:
            input_text (str): 用户输入的文本内容
            chat_history (Optional[List[BaseMessage]]): 聊天历史记录
                - None: 不使用历史记录
                - List[BaseMessage]: 包含 HumanMessage 和 AIMessage 的列表
                - 注意: 如果启用了 checkpointing 并提供 thread_id，chat_history 会被忽略
            thread_id (Optional[str]): 会话线程ID
                - 用于标识和持久化会话状态
                - 当启用 checkpointing 时，相同的 thread_id 会自动恢复之前的会话状态
                - 格式建议: "conv_{conversation_id}" 或 "user_{user_id}_{timestamp}"
            stream_mode (Union[str, Sequence[str]]): 流式输出模式
                - "messages": 按消息流式输出（默认，推荐）
                - "updates": 按更新流式输出
                - "values": 按值流式输出
                - "checkpoints": 按检查点流式输出
                - "debug": 调试信息流式输出
                - 可以组合多个模式：["messages", "updates"]
            **kwargs: 传递给 Agent 的额外参数

        Yields:
            Iterator[str]: 智能体响应的文本片段
                - 每次yield返回一个或多个文本片段
                - 片段按生成顺序返回
                - 可以实时处理和显示

        Raises:
            Exception: 当 Agent 执行失败时抛出异常

        处理流程：
            1. 构建消息列表（与 invoke 相同）
            2. 创建 Command 对象包装输入
            3. 启动流式处理循环
            4. 根据 stream_mode 解析不同类型的流式数据
            5. 提取并 yield AI 消息内容

        流式模式说明：
            - "messages" 模式：
                * 返回完整的消息对象
                * 最常用，适合大多数场景
                * 自动过滤非 AI 消息

            - "updates" 模式：
                * 返回状态更新信息
                * 适合监控 Agent 执行过程
                * 需要手动提取消息内容

        示例：
            # 基础流式输出
            agent = BaseAgent(model="glm-4.5")
            for chunk in agent.streaming("请介绍自己"):
                print(chunk, end="")

            # 带历史记录的流式输出
            history = [
                HumanMessage(content="我叫张三"),
                AIMessage(content="你好张三")
            ]
            for chunk in agent.streaming("我叫什么？", chat_history=history):
                print(chunk, end="")

            # 实时流式传输（HTTP SSE）
            from flask import Response, stream_with_context
            response = Response(
                stream_with_context(
                    agent.streaming("写一首诗")
                ),
                mimetype='text/event-stream'
            )

            # 收集所有片段
            full_response = ""
            for chunk in agent.streaming("讲一个故事"):
                full_response += chunk
                print(chunk, end="", flush=True)

        使用场景：
            - 实时聊天界面
            - HTTP Server-Sent Events (SSE)
            - WebSocket 实时通信
            - 长文本生成（避免等待）
            - 进度显示和反馈

        优势：
            - 用户体验更好：实时看到响应，无需等待完整生成
            - 降低延迟：首字符响应时间（TTFB）更短
            - 节省内存：不需要在内存中缓存完整响应
            - 可中断：用户可以提前终止流式输出

        注意事项：
            - 这是一个生成器函数，使用 for 循环或 list() 消费
            - stream_mode="messages" 是最常用的模式
            - 异常会在流式过程中抛出，需要适当处理
            - 不同模型对流式输出的支持程度不同
        """
        try:
            messages = []

            # 如果启用了 checkpointing 并提供了 thread_id，使用 checkpointer 的状态
            config = None
            if self.enable_checkpointing and thread_id:
                config = {"configurable": {"thread_id": thread_id}}
                logger.debug(f"使用 Checkpointing 状态管理: thread_id={thread_id}")
            else:
                # 只有启用记忆组件时才使用
                if self.enable_memory and self.memory:
                    # 如果提供了 chat_history，先将其添加到记忆组件
                    if chat_history:
                        for msg in chat_history:
                            if isinstance(msg, HumanMessage):
                                self.memory.chat_memory.add_user_message(msg.content)
                            elif isinstance(msg, AIMessage):
                                self.memory.chat_memory.add_ai_message(msg.content)

                    # 从记忆组件加载智能截断后的历史记录
                    memory_variables = self.memory.load_memory_variables({})
                    memory_history = memory_variables.get("history", [])

                    # 将记忆中的历史添加到消息列表
                    if memory_history:
                        messages.extend(memory_history)
                else:
                    # 如果未启用记忆组件，直接使用传入的 chat_history
                    if chat_history:
                        messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))
            graph_input = {"messages": messages}
            graph_input.update(kwargs)
            command_input = Command(update=graph_input)

            # 收集完整的 AI 响应用于保存到记忆
            full_response = ""

            for chunk in self.graph.stream(input=command_input, stream_mode=stream_mode, config=config):
                if stream_mode == "messages":
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        message, metadata = chunk
                        if isinstance(message, AIMessage) and message.content:
                            logger.debug(f"流式输出: {message.content[:50]}...")
                            yield message.content
                            full_response += message.content
                    elif isinstance(chunk, AIMessage) and chunk.content:
                            logger.debug(f"流式输出: {chunk.content[:50]}...")
                            yield chunk.content
                            full_response += chunk.content

                elif stream_mode == "updates":
                    if isinstance(chunk, dict) and "message" in chunk:
                        message_update = chunk["message"]
                        if message_update:
                            last_msg = message_update[-1]
                            if isinstance(last_msg, AIMessage) and last_msg.content:
                                yield last_msg.content
                                full_response += last_msg.content

            # 如果未使用 checkpointing，手动保存到记忆组件
            if not (self.enable_checkpointing and thread_id):
                if self.enable_memory and self.memory and full_response:
                    self.memory.save_context(
                        {"input": input_text},
                        {"output": full_response}
                    )

            logger.info("Agent 流式调用完成")

        except Exception as e:
            error_msg = f"Agent 流式执行失败: {str(e)}"
            logger.error(f"{error_msg}")
            yield f"\n\n抱歉，处理您的请求时出现错误: {str(e)}"

    async def ainvoke(
            self,
            input_text: str,
            chat_history: Optional[List[BaseMessage]] = None,
            config: Optional[dict[str, Any]] = None,
            **kwargs: Any
    ) -> str:
        """
        异步调用智能体

        以异步方式调用智能体处理输入文本，返回完整的响应结果。
        适用于需要高并发或非阻塞 I/O 的场景，是 invoke 方法的异步版本。

        Args:
            input_text (str): 用户输入的文本内容
            chat_history (Optional[List[BaseMessage]]): 聊天历史记录
                - None: 不使用历史记录
                - List[BaseMessage]: 包含 HumanMessage 和 AIMessage 的列表
                - 消息顺序应为时间正序（从早到晚）
            config (Optional[dict[str, Any]]): LangGraph 运行配置
                - None: 使用默认配置
                - dict: 可包含以下配置项：
                    * recursion_limit: 递归深度限制
                    * timeout: 执行超时时间
                    * tags: 执行标签
                    * metadata: 元数据
                    * 其他 LangGraph 配置参数
            **kwargs: 传递给 Agent 的额外参数
                - temperature: 温度参数（控制随机性）
                - max_tokens: 最大生成 token 数
                - top_p: nucleus sampling 参数
                - 其他模型特定参数

        Returns:
            str: 智能体的响应文本
                - 完整的 AI 消息内容
                - 不包含历史记录
                - 仅返回最后一条 AI 消息

        Raises:
            Exception: 当 Agent 执行失败时抛出异常
                - 网络连接错误
                - 模型 API 错误
                - 超时错误
                - 其他运行时异常

        处理流程：
            1. 构建消息列表：
               - 如果提供 chat_history，将其添加到消息列表
               - 将 input_text 包装为 HumanMessage 并添加到列表
            2. 创建输入对象：
               - 构建图输入字典
               - 合并额外的 kwargs 参数
               - 创建 Command 对象包装输入
            3. 异步调用：使用 await 调用 LangGraph 的异步方法
            4. 提取响应：从返回的消息中提取最后一条 AI 消息
            5. 返回结果：返回 AI 消息的内容

        与 invoke 的区别：
            - 异步执行：使用 async/await 语法
            - 非阻塞 I/O：不会阻塞事件循环
            - 高并发支持：可同时处理多个请求
            - 配置参数：支持 config 参数进行更细粒度的控制

        示例：
            # 基础异步调用
            import asyncio

            async def main():
                agent = BaseAgent(model="glm-4.5")
                response = await agent.ainvoke("你好")
                print(response)

            asyncio.run(main())

            # 带历史记录的异步调用
            async def chat_with_history():
                agent = BaseAgent(model="glm-4.5")
                history = [
                    HumanMessage(content="我叫张三"),
                    AIMessage(content="你好张三，很高兴认识你")
                ]
                response = await agent.ainvoke("我叫什么名字？", chat_history=history)
                print(response)  # 应该回答"张三"

            asyncio.run(chat_with_history())

            # 带配置的异步调用
            response = await agent.ainvoke(
                "帮我写一段代码",
                config={
                    "recursion_limit": 50,
                    "timeout": 30
                },
                temperature=0.3,
                max_tokens=2000
            )

            # 并发处理多个请求
            async def process_multiple_requests():
                agent = BaseAgent(model="glm-4.5")
                questions = [
                    "什么是人工智能？",
                    "什么是机器学习？",
                    "什么是深度学习？"
                ]
                tasks = [agent.ainvoke(q) for q in questions]
                answers = await asyncio.gather(*tasks)
                for q, a in zip(questions, answers):
                    print(f"Q: {q}\nA: {a}\n")

            asyncio.run(process_multiple_requests())

        使用场景：
            - Web 应用：FastAPI、Flask 异步视图
            - 高并发服务：需要同时处理多个请求
            - 实时系统：聊天机器人、客服系统
            - 微服务架构：异步调用链
            - I/O 密集型应用：减少等待时间

        性能优势：
            - 更高的吞吐量：可以同时处理多个请求
            - 更低的延迟：不阻塞其他任务
            - 更好的资源利用：充分利用 I/O 等待时间
            - 可扩展性：易于扩展到分布式系统

        注意事项：
            - 必须在异步上下文中调用（async 函数或事件循环）
            - 使用 asyncio.run() 或 await 调用
            - 异常处理需要使用 try-except 块
            - config 参数的格式取决于 LangGraph 版本
            - 不适合 CPU 密集型任务（应使用同步版本）
        """
        try:
            messages = []

            # 只有启用记忆组件时才使用
            if self.enable_memory and self.memory:
                # 如果提供了 chat_history，先将其添加到记忆组件
                if chat_history:
                    for msg in chat_history:
                        if isinstance(msg, HumanMessage):
                            self.memory.chat_memory.add_user_message(msg.content)
                        elif isinstance(msg, AIMessage):
                            self.memory.chat_memory.add_ai_message(msg.content)

                # 从记忆组件加载智能截断后的历史记录
                memory_variables = self.memory.load_memory_variables({})
                memory_history = memory_variables.get("history", [])

                # 将记忆中的历史添加到消息列表
                if memory_history:
                    messages.extend(memory_history)
            else:
                # 如果未启用记忆组件，直接使用传入的 chat_history
                if chat_history:
                    messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))

            graph_input = {"messages": messages}
            graph_input.update(kwargs)
            command_input = Command(update=graph_input)
            result = await self.graph.ainvoke(command_input, config=config)

            output_messages = result.get("messages", [])
            ai_response = ""
            for msg in reversed(output_messages):
                if isinstance(msg, AIMessage):
                    ai_response = msg.content
                    break

            # 只有启用记忆组件时才保存
            if self.enable_memory and self.memory:
                # 将当前交互保存到记忆组件
                self.memory.save_context(
                    {"input": input_text},
                    {"output": ai_response}
                )

            logger.info("异步调用成功")
            return ai_response


        except Exception as e:
            error_msg = f"Agent 异步执行失败: {str(e)}"
            logger.error(f"{error_msg}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    async def astreaming(
            self,
            input_text: str,
            chat_history: Optional[List[BaseMessage]] = None,
            stream_mode: Union[
                Literal["values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"],
                Sequence[Literal["values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"]]
            ] = "messages",
            **kwargs: Any
    ) -> AsyncIterator[str]:
        """
        异步流式调用智能体

        以异步流式方式调用智能体，实时生成并返回响应内容。
        结合了异步和流式的优势，适用于需要高并发实时输出的场景。

        Args:
            input_text (str): 用户输入的文本内容
            chat_history (Optional[List[BaseMessage]]): 聊天历史记录
                - None: 不使用历史记录
                - List[BaseMessage]: 包含 HumanMessage 和 AIMessage 的列表
                - 消息顺序应为时间正序（从早到晚）
            stream_mode (Union[str, Sequence[str]]): 流式输出模式
                - "messages": 按消息流式输出（默认，推荐）
                - "updates": 按更新流式输出
                - "values": 按值流式输出
                - "checkpoints": 按检查点流式输出
                - "debug": 调试信息流式输出
                - 可以组合多个模式：["messages", "updates"]
            **kwargs: 传递给 Agent 的额外参数
                - temperature: 温度参数（控制随机性）
                - max_tokens: 最大生成 token 数
                - 其他模型特定参数

        Yields:
            AsyncIterator[str]: 智能体响应的文本片段
                - 异步生成器，每次返回一个或多个文本片段
                - 片段按生成顺序返回
                - 可以实时处理和显示
                - 使用 async for 循环消费

        Raises:
            Exception: 当 Agent 执行失败时抛出异常
                - 网络连接错误
                - 模型 API 错误
                - 超时错误
                - 其他运行时异常

        处理流程：
            1. 构建消息列表（与 ainvoke 相同）
            2. 创建 Command 对象包装输入
            3. 启动异步流式处理循环
            4. 根据 stream_mode 解析不同类型的流式数据
            5. 异步提取并 yield AI 消息内容

        流式模式说明：
            - "messages" 模式：
                * 返回完整的消息对象
                * 最常用，适合大多数场景
                * 自动过滤非 AI 消息

            - "updates" 模式：
                * 返回状态更新信息
                * 适合监控 Agent 执行过程
                * 需要手动提取消息内容

        与 streaming 的区别：
            - 异步生成器：使用 async for 而非 for
            - 非阻塞 I/O：不阻塞事件循环
            - 高并发支持：可同时处理多个流式请求
            - 更适合现代异步 Web 框架

        示例：
            # 基础异步流式输出
            import asyncio

            async def main():
                agent = BaseAgent(model="glm-4.5")
                async for chunk in agent.astreaming("请介绍自己"):
                    print(chunk, end="")

            asyncio.run(main())

            # 带历史记录的异步流式输出
            async def chat_with_history():
                agent = BaseAgent(model="glm-4.5")
                history = [
                    HumanMessage(content="我叫张三"),
                    AIMessage(content="你好张三")
                ]
                async for chunk in agent.astreaming("我叫什么？", chat_history=history):
                    print(chunk, end="", flush=True)

            asyncio.run(chat_with_history())

            # 在 FastAPI 中使用异步流式输出
            from fastapi import FastAPI
            from fastapi.responses import StreamingResponse

            app = FastAPI()
            agent = BaseAgent(model="glm-4.5")

            @app.post("/chat")
            async def chat_endpoint(question: str):
                async def generate():
                    async for chunk in agent.astreaming(question):
                        yield f"data: {chunk}\n\n"

                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream"
                )

            # 收集所有片段
            async def collect_response():
                full_response = ""
                async for chunk in agent.astreaming("讲一个故事"):
                    full_response += chunk
                    print(chunk, end="", flush=True)
                return full_response

            # 并发处理多个流式请求
            async def process_multiple_streams():
                agent = BaseAgent(model="glm-4.5")
                questions = [
                    "写一首诗",
                    "讲个笑话",
                    "介绍一下Python"
                ]

                async def process_question(q):
                    response = ""
                    async for chunk in agent.astreaming(q):
                        response += chunk
                    return q, response

                tasks = [process_question(q) for q in questions]
                results = await asyncio.gather(*tasks)
                for q, a in results:
                    print(f"Q: {q}\nA: {a[:50]}...\n")

            asyncio.run(process_multiple_streams())

        使用场景：
            - 异步 Web 应用：FastAPI、Starlette
            - WebSocket 实时通信：异步 WebSocket 服务器
            - 高并发聊天系统：同时服务多个用户
            - 实时 API 服务：SSE（Server-Sent Events）
            - 异步流数据处理：实时数据流分析

        性能优势：
            - 异步非阻塞：不阻塞其他协程
            - 高并发能力：可同时处理数千个流式连接
            - 低内存占用：不需要缓存完整响应
            - 实时响应：首字符响应时间（TTFB）更短

        与 streaming 的选择：
            - 使用 streaming：同步应用、简单脚本
            - 使用 astreaming：异步应用、高并发场景、现代 Web 框架

        注意事项：
            - 这是一个异步生成器函数，使用 async for 循环消费
            - 必须在异步上下文中调用
            - stream_mode="messages" 是最常用的模式
            - 异常会在流式过程中抛出，需要适当处理
            - 不同模型对流式输出的支持程度不同
            - 客户端需要支持流式数据处理（如 SSE、WebSocket）
        """
        try:
            messages = []

            # 只有启用记忆组件时才使用
            if self.enable_memory and self.memory:
                # 如果提供了 chat_history，先将其添加到记忆组件
                if chat_history:
                    for msg in chat_history:
                        if isinstance(msg, HumanMessage):
                            self.memory.chat_memory.add_user_message(msg.content)
                        elif isinstance(msg, AIMessage):
                            self.memory.chat_memory.add_ai_message(msg.content)

                # 从记忆组件加载智能截断后的历史记录
                memory_variables = self.memory.load_memory_variables({})
                memory_history = memory_variables.get("history", [])

                # 将记忆中的历史添加到消息列表
                if memory_history:
                    messages.extend(memory_history)
            else:
                # 如果未启用记忆组件，直接使用传入的 chat_history
                if chat_history:
                    messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))
            graph_input = {"messages": messages}
            graph_input.update(kwargs)
            command_input = Command(update=graph_input)

            # 收集完整的 AI 响应用于保存到记忆
            full_response = ""

            for chunk in self.graph.astream(input=command_input, stream_mode=stream_mode):
                if stream_mode == "messages":
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        message, metadata = chunk
                        if isinstance(message, AIMessage) and message.content:
                            yield message.content
                            full_response += message.content
                    elif isinstance(chunk, AIMessage) and chunk.content:
                        yield chunk.content
                        full_response += chunk.content
                elif stream_mode == "updates":
                    if isinstance(chunk, dict) and "message" in chunk:
                        message_update = chunk["message"]
                        if message_update:
                            last_msg = message_update[-1]
                            if isinstance(last_msg, AIMessage) and last_msg.content:
                                yield last_msg.content
                                full_response += last_msg.content

            # 只有启用记忆组件时才保存
            if self.enable_memory and self.memory and full_response:
                self.memory.save_context(
                    {"input": input_text},
                    {"output": full_response}
                )

            logger.info("Agent 异步流式调用完成")

        except Exception as e:
            error_msg = f"Agent 异步流式执行失败: {str(e)}"
            logger.error(f"{error_msg}")
            yield f"\n\n抱歉，处理您的请求时出现错误: {str(e)}"

    def _create_rag_tool(self, index_name: str, config: Optional[dict] = None):
        """
        创建 RAG 检索工具（私有方法）

        为智能体创建一个基于向量检索的 RAG（Retrieval-Augmented Generation）工具。
        该工具允许智能体在生成响应时从知识库中检索相关信息，增强回答的准确性。

        Args:
            index_name (str): 知识库索引名称
                - 必须是已经创建并索引的向量存储
                - 索引通常通过 IndexManager 创建
                - 同一个索引可以被多个 Agent 实例共享
                - 索引名称区分大小写
            config (Optional[dict]): RAG 检索配置参数
                - None: 使用默认检索配置
                - dict: 可包含以下配置项：
                    * search_type: 检索类型
                      - "similarity": 相似度检索（默认）
                      - "mmr": 最大边际相关性检索（多样性）
                    * k: 检索的文档数量（默认：4）
                      - 太少可能导致信息不足
                      - 太多可能引入噪声
                      - 建议：3-10 之间
                    * score_threshold: 相似度阈值（0-1）
                      - 只返回相似度高于此值的文档
                      - None 表示不设置阈值
                    * fetch_k: 在 MMR 检索前获取的文档数
                    * lambda_mult: MMR 多样性参数（0-1）
                      - 0: 最大多样性
                      - 1: 最大相关性
                    * 其他检索器特定参数

        Returns:
            BaseTool | None: RAG 检索工具实例
                - 成功：返回配置好的检索工具
                - 失败：返回 None，并记录错误日志
                - 工具名称固定为 "knowledge_base"
                - 工具描述说明如何使用知识库

        Raises:
            本方法不抛出异常，而是返回 None 并记录错误

        处理流程：
            1. 初始化组件：
               - 获取嵌入模型（get_embeddings）
               - 创建索引管理器（IndexManager）

            2. 验证索引：
               - 检查索引是否存在
               - 如果不存在，记录错误并返回 None

            3. 加载向量存储：
               - 从索引中加载向量存储
               - 使用嵌入模型进行向量化

            4. 创建检索器：
               - 使用向量存储创建检索器
               - 应用检索配置参数
               - 支持多种检索策略

            5. 创建工具：
               - 将检索器包装为 LangChain 工具
               - 设置工具名称和描述
               - 返回可用的工具实例

        检索策略说明：
            - 相似度检索（similarity）：
                * 根据向量相似度返回最相关的文档
                * 适合精确匹配场景
                * 可能返回重复内容

            - MMR 检索：
                * 在相关性和多样性之间平衡
                * 避免返回过于相似的文档
                * 适合需要广泛信息的场景

        使用示例：
            # 在 BaseAgent 初始化中使用（内部方法）
            agent = BaseAgent(
                model="glm-4.5",
                enable_rag=True,
                rag_index_name="tech_docs",
                rag_config={
                    "search_type": "similarity",
                    "k": 5,
                    "score_threshold": 0.7
                }
            )

            # 直接调用（通常不推荐，仅供内部使用）
            agent = BaseAgent(model="glm-4.5")
            rag_tool = agent._create_rag_tool(
                index_name="my_knowledge_base",
                config={
                    "search_type": "mmr",
                    "k": 5,
                    "lambda_mult": 0.5
                }
            )
            if rag_tool:
                agent.tools.append(rag_tool)

        工具特性：
            - 自动向量化：查询会自动转换为向量
            - 语义搜索：基于语义相似度而非关键词
            - 可配置：支持多种检索策略
            - 集成友好：作为 LangChain 工具无缝集成

        性能考虑：
            - 索引大小：大型索引可能需要更多检索时间
            - k 值选择：较大的 k 值会增加处理时间
            - 检索模式：MMR 比 similarity 慢但质量更高
            - 缓存：考虑缓存频繁查询的结果

        最佳实践：
            1. 索引管理：
               - 定期更新索引以保持最新
               - 使用有意义的索引名称
               - 为不同主题创建独立索引

            2. 配置优化：
               - 根据文档特点调整 k 值
               - 使用 score_threshold 过滤低质量结果
               - 在相关性和多样性之间选择合适的检索模式

            3. 错误处理：
               - 检查返回值是否为 None
               - 记录创建失败的日志
               - 提供降级方案（如不使用 RAG）

        注意事项：
            - 这是一个私有方法（以 _ 开头），仅供内部使用
            - 索引必须预先创建和索引
            - 嵌入模型必须与索引创建时使用的模型一致
            - 检索结果质量取决于索引质量和检索参数
            - 如果索引不存在，方法会返回 None 而非抛出异常
            - 工具名称固定为 "knowledge_base"，不可自定义

        相关方法：
            - __init__: 初始化时会调用此方法（当 enable_rag=True 时）
            - IndexManager.index_exists: 检查索引是否存在
            - create_retriever: 创建检索器实例
            - create_retriever_tool: 将检索器包装为工具
        """
        try:
            embeddings = get_embeddings()
            index_manager = IndexManager()

            if not index_manager.index_exists(index_name):
                logger.error(f"RAG索引不存在: {index_name}")
                return None

            vector_store = index_manager.load_index(index_name, embeddings=embeddings)
            retriever_config = config or {}
            retriever = create_retriever(vector_store=vector_store, **retriever_config)
            tool = create_retriever_tool(
                retriever=retriever,
                name="knowledge_base",
                description="搜索知识库中的相关信息，用于回答基于文档的问题"
            )

            logger.info(f"RAG工具创建成功: {index_name}")
            return tool

        except Exception as e:
            logger.error(f"创建RAG工具失败: {e}")
            return None

    def streaming_with_thinking(
            self,
            input_text: str,
            chat_history: Optional[List[BaseMessage]] = None,
            thread_id: Optional[str] = None,
            **kwargs: Any
    ) -> Iterator[Dict[str, Any]]:
        """
        流式调用智能体（支持深度思考）

        返回包含推理内容和最终内容的字典

        Args:
            input_text: 用户输入
            chat_history: 聊天历史
                - 注意: 如果启用了 checkpointing 并提供 thread_id，chat_history 会被忽略
            thread_id: 会话线程ID
                - 用于标识和持久化会话状态
                - 当启用 checkpointing 时，相同的 thread_id 会自动恢复之前的会话状态
            **kwargs: 额外参数

        Yields:
            Dict[str, Any]: 包含 type 和 content/data 的字典
                - type: "reasoning" | "content" | "error"
                - content: 文本内容
                - data: 额外数据（可选）

        Example:
            >>> for event in agent.streaming_with_thinking("分析这个问题"):
            ...     if event['type'] == 'reasoning':
            ...         print(f"思考: {event['content']}")
            ...     elif event['type'] == 'content':
            ...         print(f"回答: {event['content']}")
        """
        try:
            messages = []

            # 如果启用了 checkpointing 并提供了 thread_id，使用 checkpointer 的状态
            config = None
            if self.enable_checkpointing and thread_id:
                config = {"configurable": {"thread_id": thread_id}}
                logger.debug(f"使用 Checkpointing 状态管理: thread_id={thread_id}")
            else:
                # 只有启用记忆组件时才使用
                if self.enable_memory and self.memory:
                    # 如果提供了 chat_history，先将其添加到记忆组件
                    if chat_history:
                        for msg in chat_history:
                            if isinstance(msg, HumanMessage):
                                self.memory.chat_memory.add_user_message(msg.content)
                            elif isinstance(msg, AIMessage):
                                self.memory.chat_memory.add_ai_message(msg.content)

                    # 从记忆组件加载智能截断后的历史记录
                    memory_variables = self.memory.load_memory_variables({})
                    memory_history = memory_variables.get("history", [])

                    # 将记忆中的历史添加到消息列表
                    if memory_history:
                        messages.extend(memory_history)
                else:
                    # 如果未启用记忆组件，直接使用传入的 chat_history
                    if chat_history:
                        messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))

            graph_input = {"messages": messages}
            graph_input.update(kwargs)
            command_input = Command(update=graph_input)

            # 收集完整响应用于保存到记忆
            full_response = ""

            for chunk in self.graph.stream(
                    input=command_input,
                    stream_mode="messages",
                    config=config,
            ):
                logger.info(chunk)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    message, metadata_t = chunk
                    if isinstance(message, AIMessage):
                        yield from self._yield_message_content(message)
                        # 收集最终内容到完整响应
                        if hasattr(message, 'content') and message.content:
                            if not (self.enable_thinking and hasattr(message, 'reasoning_content')):
                                full_response += message.content
                elif isinstance(chunk, AIMessage):
                    yield from self._yield_message_content(chunk)
                    # 收集最终内容到完整响应
                    if hasattr(chunk, 'content') and chunk.content:
                        if not (self.enable_thinking and hasattr(chunk, 'reasoning_content')):
                            full_response += chunk.content

            # 如果未使用 checkpointing，手动保存到记忆组件
            if not (self.enable_checkpointing and thread_id):
                if self.enable_memory and self.memory and full_response:
                    self.memory.save_context(
                        {"input": input_text},
                        {"output": full_response}
                    )

            logger.info("Agent 流式调用完成")

        except Exception as e:
            error_msg = f"Agent 执行失败: {str(e)}"
            logger.error(error_msg)
            yield {
                "type": "error",
                "content": f"抱歉，处理您的请求时出现错误: {str(e)}"
            }

    def _yield_message_content(self, message: AIMessage):
        """
        提取并 yield 消息中的推理内容和最终内容

        Args:
            message: AIMessage 对象
        """

        if hasattr(message, "content_blocks") and message.content_blocks:
            for block in message.content_blocks:
                if isinstance(block, dict) and block.get("type") == "reasoning":
                    yield {
                        "type": "reasoning",
                        "content": block.get("text", ""),
                        "timestamp": self._get_timestamp()
                    }
                elif isinstance(block, dict) and block.get("type") == "text":
                    # 最终内容
                    yield {
                        "type": "content",
                        "content": block.get("text", ""),
                        "timestamp": self._get_timestamp()
                    }

        elif self.enable_thinking and hasattr(message, 'reasoning_content'):
            if message.reasoning_content:
                yield {
                    "type": "reasoning",
                    "content": message.reasoning_content,
                    "timestamp": self._get_timestamp()
                }
            yield {
                "type": "content",
                "content": message.content,
                "timestamp": self._get_timestamp()
            }

        else:
            yield {
                "type": "content",
                "content": message.content,
                "timestamp": self._get_timestamp()
            }

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().isoformat()

    def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定 thread_id 的当前状态

        当启用 Checkpointing 时，可以查询指定会话的当前状态。
        这对于调试、监控和恢复会话非常有用。

        Args:
            thread_id (str): 会话线程ID
                - 用于标识会话
                - 格式建议: "conv_{conversation_id}" 或 "user_{user_id}_{timestamp}"

        Returns:
            Optional[Dict[str, Any]]: 当前状态字典，包含:
                - values: 当前状态值（包含 messages 等）
                - next: 下一步要执行的操作
                - config: 配置信息
                - metadata: 元数据
                如果未启用 Checkpointing 或 thread_id 不存在，返回 None

        Raises:
            无异常抛出，出错时返回 None 并记录日志

        使用示例：
            # 获取对话的当前状态
            agent = BaseAgent(enable_checkpointing=True, checkpoint_db_path="checkpoints.db")
            state = agent.get_state("conv_123")

            if state:
                print(f"消息数量: {len(state['values'].get('messages', []))}")
                print(f"最后一条消息: {state['values']['messages'][-1]}")

        注意事项：
            - 必须启用 enable_checkpointing 才能使用
            - 返回的状态包含完整的消息历史
            - 状态是只读的，不应直接修改
            - 可以使用 get_state_history() 查看历史状态
        """
        if not self.enable_checkpointing or not self.checkpointer:
            logger.warning("Checkpointing 未启用，无法获取状态")
            return None

        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = self.graph.get_state(config)
            logger.debug(f"成功获取状态: thread_id={thread_id}")
            return state
        except Exception as e:
            logger.error(f"获取状态失败: thread_id={thread_id}, error={e}")
            return None

    def get_state_history(self, thread_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取指定 thread_id 的状态历史

        当启用 Checkpointing 时，可以查询会话的所有历史状态快照。
        这对于审计、调试和回溯非常有用。

        Args:
            thread_id (str): 会话线程ID
                - 用于标识会话
                - 格式建议: "conv_{conversation_id}" 或 "user_{user_id}_{timestamp}"
            limit (Optional[int]): 返回的最大状态数量
                - None: 返回所有历史状态（默认）
                - int: 只返回最近的 N 个状态
                - 按时间倒序排列（最新的在前）

        Returns:
            List[Dict[str, Any]]: 状态历史列表，每个状态包含:
                - values: 该时间点的状态值
                - next: 下一步操作
                - config: 配置信息
                - metadata: 元数据（包含时间戳等）
                如果未启用 Checkpointing 或 thread_id 不存在，返回空列表

        Raises:
            无异常抛出，出错时返回空列表并记录日志

        使用示例：
            # 获取完整的状态历史
            agent = BaseAgent(enable_checkpointing=True, checkpoint_db_path="checkpoints.db")
            history = agent.get_state_history("conv_123")

            for state in history:
                timestamp = state.get('metadata', {}).get('source', 'unknown')
                print(f"状态快照: {timestamp}")

            # 只获取最近 10 个状态
            recent_states = agent.get_state_history("conv_123", limit=10)

        使用场景：
            - 审计：查看会话的完整历史
            - 调试：了解状态如何随时间变化
            - 回溯：找到之前的状态快照
            - 分析：统计会话的演进模式

        注意事项：
            - 必须启用 enable_checkpointing 才能使用
            - 历史状态是只读的
            - 较长的会话可能产生大量历史状态
            - 使用 limit 参数限制返回数量以提高性能
        """
        if not self.enable_checkpointing or not self.checkpointer:
            logger.warning("Checkpointing 未启用，无法获取状态历史")
            return []

        try:
            config = {"configurable": {"thread_id": thread_id}}
            state_history = list(self.graph.get_state_history(config))

            # 应用 limit
            if limit and len(state_history) > limit:
                state_history = state_history[:limit]

            logger.debug(f"成功获取状态历史: thread_id={thread_id}, count={len(state_history)}")
            return state_history
        except Exception as e:
            logger.error(f"获取状态历史失败: thread_id={thread_id}, error={e}")
            return []

# 创建智能体
def create_base_agent(
        model: Optional[Union[str, BaseChatModel]] = None,
        tools: Optional[Sequence[BaseTool]] = None,
        prompt_mode: str = "default",
        debug: bool = False,
        **kwargs: Any
) -> BaseAgent:
    """
    创建智能体（工厂函数）

    这是一个便捷的工厂函数，用于创建 BaseAgent 实例。
    提供了与 BaseAgent 构造函数类似的接口，但更适合函数式编程风格。

    Args:
        model: 模型配置，支持以下格式：
            - None: 使用系统默认模型
            - str: 模型名称（如 "glm-4.5"）
            - BaseChatModel: 已初始化的模型实例
        tools: 工具列表
            - None: 使用内置基础工具集（BASIC_TOOLS）
            - Sequence[BaseTool]: 自定义工具列表
            - []: 空列表，不使用任何工具
        prompt_mode: 提示词模式，影响自动生成的提示词风格
            - "default": 默认模式（平衡）
            - "creative": 创意模式（更灵活）
            - "precise": 精确模式（更严格）
            - 其他自定义模式字符串
        debug: 是否启用调试模式
            - False: 正常模式（默认）
            - True: 输出详细的执行信息
        **kwargs: 传递给 BaseAgent 的额外参数
            - enable_rag: 是否启用 RAG 功能
            - rag_index_name: RAG 知识库索引名称
            - rag_config: RAG 检索配置参数
            - system_prompt: 自定义系统提示词
            - 其他 BaseAgent 支持的参数

    Returns:
        BaseAgent: 配置好的智能体实例
            - 已初始化并可立即使用
            - 包含所有指定的工具和配置
            - 可调用 invoke、streaming 等方法

    Raises:
        Exception: 当智能体创建失败时抛出异常
            - 模型初始化错误
            - 工具配置错误
            - RAG 配置错误
            - 其他初始化异常

    创建流程：
        1. 记录日志：记录智能体创建请求
        2. 参数传递：将所有参数传递给 BaseAgent 构造函数
        3. 实例化：创建并返回 BaseAgent 实例
        4. 返回结果：返回完全配置的智能体对象

    与直接使用 BaseAgent 的区别：
        - 函数式风格：更适合函数式编程
        - 日志记录：自动记录创建日志
        - 简洁性：参数列表更简洁（不包含 RAG 相关参数）
        - 灵活性：可以在未来添加额外的配置逻辑

    使用示例：
        # 基础使用
        from blues_aka.Agent.BaseAgent import create_base_agent

        agent = create_base_agent(model="glm-4.5")
        response = agent.invoke("你好")

        # 带自定义工具
        from langchain_core.tools import tool

        @tool
        def my_tool(query: str) -> str:
            return f"处理查询: {query}"

        agent = create_base_agent(
            model="glm-4.5",
            tools=[my_tool],
            debug=True
        )

        # 使用提示词模式
        agent = create_base_agent(
            model="glm-4.5",
            prompt_mode="creative"
        )

        # 启用 RAG
        agent = create_base_agent(
            model="glm-4.5",
            enable_rag=True,
            rag_index_name="my_knowledge_base",
            rag_config={"k": 5}
        )

        # 完整配置
        agent = create_base_agent(
            model="glm-4.5",
            tools=[my_tool],
            prompt_mode="precise",
            debug=True,
            enable_rag=True,
            rag_index_name="tech_docs",
            system_prompt="你是一个专业的技术顾问"
        )

    使用场景：
        - 快速原型开发：快速创建智能体实例
        - 函数式编程：集成到函数式代码中
        - 配置管理：通过配置文件创建智能体
        - 动态创建：根据条件动态创建不同配置的智能体
        - 批量创建：创建多个相似的智能体实例

    设计模式：
        - 工厂模式：封装对象创建逻辑
        - 简化接口：提供比直接构造更简洁的接口
        - 关注点分离：将创建逻辑与使用逻辑分离

    最佳实践：
        1. 参数选择：
           - 为生产环境明确指定 model
           - 根据需求选择合适的 prompt_mode
           - 在开发时启用 debug，生产时关闭

        2. 工具管理：
           - 只添加必要的工具
           - 为工具提供清晰的名称和描述
           - 测试工具与模型的兼容性

        3. 错误处理：
           - 捕获创建异常
           - 提供降级方案
           - 记录详细的错误信息

        4. 性能优化：
           - 重用智能体实例而非重复创建
           - 考虑使用单例模式管理长期运行的智能体
           - 合理配置工具数量

    注意事项：
        - 每次调用都会创建新的智能体实例
        - 智能体实例不是线程安全的，避免多线程共享
        - RAG 功能需要预先创建知识库索引
        - 模型 API 密钥需要在配置中正确设置
        - 不同的 prompt_mode 会影响智能体的行为

    相关函数：
        - BaseAgent.__init__: 底层构造函数
        - get_chat_model: 获取模型实例
        - get_prompt_with_tools: 生成带工具的提示词

    扩展建议：
        - 可以创建特定领域的工厂函数
        - 可以添加配置验证逻辑
        - 可以实现智能体池管理
        - 可以添加智能体缓存机制
    """
    logger.info("正在建立智能体")
    return BaseAgent(
        model=model,
        tools=tools,
        prompt_mode=prompt_mode,
        debug=debug,
        **kwargs,
    )
















