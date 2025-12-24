import logging
from typing import Optional, Union, Sequence, Any, List, Iterator

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import BaseTool

from blues_aka.config import BaseConfig
from blues_aka.core.prompts import get_prompt_with_tools, get_system_prompt
from blues_aka.core.tools import BASIC_TOOLS

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(
            self,
            model: Optional[Union[str, BaseChatModel]] = None,
            tools: Optional[Sequence[BaseTool]] = None,
            system_prompt: Optional[str] = None,
            prompt_mode: str = "default",
            debug: bool = False,
            **kwargs: Any):

        # 初始化模型
        if model is None:
            self.model = f"default:{BaseConfig.default_model}"
        elif isinstance(model, str):
            self.model = model
        else:
            self.model = model

        # 初始化工具
        if tools is None:
            self.tools = BASIC_TOOLS
        else:
            self.tools = list(tools) if tools else []

        if self.tools:
            tool_names = [tool.name for tool in self.tools]
            logger.debug(f"   工具列表: {', '.join(tool_names)}")

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
            stream_mode: str = "messages",
            **kwargs: Any
    ) -> Iterator[str]:
        try:
            messages = []

            if chat_history:
                messages.extend(chat_history)

            messages.append(HumanMessage(content=input_text))
            graph_input = {"messages": messages}
            graph_input.update(kwargs)

            for chunk in self.graph.stream(input=graph_input, stream_mode=stream_mode):
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

                logger.info("✅ Agent 流式调用完成")

        except Exception as e:
            error_msg = f"Agent 流式执行失败: {str(e)}"
            logger.error(f"{error_msg}")
            yield f"\n\n抱歉，处理您的请求时出现错误: {str(e)}"
















