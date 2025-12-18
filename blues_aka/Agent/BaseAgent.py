from typing import Optional, Union, Sequence, Any

from langchain_core.language_models import BaseChatModel


class BaseAgent:
    def __init__(
            self,
            model: Optional[Union[str, BaseChatModel]] = None,
            tools: Optional[Sequence[str]] = None,
            system_prompt: Optional[str] = None,
            prompt_mode: str = "default",
            debug: bool = False,
            **kwargs: Any):

        pass




