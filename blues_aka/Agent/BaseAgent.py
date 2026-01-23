import logging
from typing import Optional, Union, Sequence, Any, List, Iterator, Literal, AsyncIterator

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langgraph.types import Command

from blues_aka.config.config import ConfigFactory
from blues_aka.core.prompts import get_prompt_with_tools, get_system_prompt
from blues_aka.core.tools import BASIC_TOOLS
from blues_aka.core.models import get_chat_model
from blues_aka.rag.embeddings import get_embeddings
from blues_aka.rag.index_manager import IndexManager
from blues_aka.rag.retrievers import create_retriever, create_retriever_tool

logger = logging.getLogger(__name__)

# 获取配置实例
_config = ConfigFactory.get_config()

class BaseAgent:
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
            **kwargs: Any):

        # 初始化模型 - 将字符串转换为模型实例
        if model is None:
            # 使用默认模型
            self.model = get_chat_model(model_name=_config.default_model)
            logger.info(f"使用默认模型: {_config.default_model}")
        elif isinstance(model, str):
            # 如果是字符串，创建模型实例
            # 检查是否已经有提供商前缀 (如 "zhipuai:glm-4.5")
            if ':' in model:
                # 有前缀，直接使用
                self.model = get_chat_model(model_name=model.split(':', 1)[1])
                logger.info(f"使用模型（带前缀）: {model}")
            else:
                # 没有前缀，使用模型名称
                self.model = get_chat_model(model_name=model)
                logger.info(f"使用模型: {model}")
        else:
            # 已经是模型实例，直接使用
            self.model = model
            logger.info("使用传入的模型实例")

        # 初始化工具
        if tools is None:
            self.tools = BASIC_TOOLS
        else:
            self.tools = list(tools) if tools else []

        if self.tools:
            tool_names = [tool.name for tool in self.tools]
            logger.debug(f"   工具列表: {', '.join(tool_names)}")

        # RAG


        # 初始化提示词
        if system_prompt is None:
            if self.tools:
                self.system_prompt = get_prompt_with_tools(mode=prompt_mode)
            else:
                self.system_prompt = get_system_prompt(mode=prompt_mode)
        else:
            self.system_prompt = system_prompt

        self.debug = debug

        try:
            # 创建Agent
            self.graph = create_agent(
                model=self.model,
                tools=self.tools if self.tools else None,
                system_prompt=self.system_prompt,
                debug=self.debug,
                **kwargs,
            )
            logger.info("Agent 创建成功（CompiledStateGraph）")
            logger.debug(f"配置: debug={self.debug}, tools={len(self.tools)}")
        except Exception as e:
            logger.error(e)
            raise e

    # 普通输出
    def invoke(
        self,
        input_text: str,
        chat_history: Optional[List[BaseMessage]] = None,
        **kwargs: Any) -> str:

        try:
            messages = []

            if chat_history:
                messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))

            graph_input = {"messages": messages}
            graph_input.update(kwargs)

            result = self.graph.invoke(**graph_input)
            output_messages = result.get("messages", [])

            ai_response = ""
            for msg in reversed(output_messages):
                if isinstance(msg, AIMessage):
                    ai_response = msg.content
                    break

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
            stream_mode: Union[
                Literal["values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"],
                Sequence[Literal["values", "updates", "checkpoints", "tasks", "debug", "messages", "custom"]]
            ] = "messages",
            **kwargs: Any
    ) -> Iterator[str]:
        try:
            messages = []

            if chat_history:
                messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))
            graph_input = {"messages": messages}
            graph_input.update(kwargs)
            command_input = Command(update=graph_input)

            for chunk in self.graph.stream(input=command_input, stream_mode=stream_mode):
                if stream_mode == "messages":
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        message, metadata = chunk
                        if isinstance(message, AIMessage) and message.content:
                            logger.debug(f"流式输出: {message.content[:50]}...")
                            yield message.content
                    elif isinstance(chunk, AIMessage) and chunk.content:
                            logger.debug(f"流式输出: {chunk.content[:50]}...")
                            yield chunk.content

                elif stream_mode == "updates":
                    if isinstance(chunk, dict) and "message" in chunk:
                        message_update = chunk["message"]
                        if message_update:
                            last_msg = message_update[-1]
                            if isinstance(last_msg, AIMessage) and last_msg.content:
                                yield last_msg.content

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
        try:
            messages = []
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
        try:
            messages = []
            if chat_history:
                messages.extend(chat_history)
            messages.append(HumanMessage(content=input_text))
            graph_input = {"messages": messages}
            graph_input.update(kwargs)
            command_input = Command(update=graph_input)

            for chunk in self.graph.astream(input=command_input, stream_mode=stream_mode):
                if stream_mode == "messages":
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        message, metadata = chunk
                        if isinstance(message, AIMessage) and message.content:
                            yield message.content
                    elif isinstance(chunk, AIMessage) and chunk.content:
                        yield chunk.content
                elif stream_mode == "updates":
                    if isinstance(chunk, dict) and "message" in chunk:
                        message_update = chunk["message"]
                        if message_update:
                            last_msg = message_update[-1]
                            if isinstance(last_msg, AIMessage) and last_msg.content:
                                yield last_msg.content

            logger.info("Agent 异步流式调用完成")

        except Exception as e:
            error_msg = f"Agent 异步流式执行失败: {str(e)}"
            logger.error(f"{error_msg}")
            yield f"\n\n抱歉，处理您的请求时出现错误: {str(e)}"

    def _create_rag_tool(self, index_name: str, config: Optional[dict] = None):
        """创建RAG检索工具"""
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

# 创建智能体
def create_base_agent(
        model: Optional[Union[str, BaseChatModel]] = None,
        tools: Optional[Sequence[BaseTool]] = None,
        prompt_mode: str = "default",
        debug: bool = False,
        **kwargs: Any
) -> BaseAgent:
    logger.info("正在建立智能体")
    return BaseAgent(
        model=model,
        tools=tools,
        prompt_mode=prompt_mode,
        debug=debug,
        **kwargs,
    )
















