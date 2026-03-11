from typing import Optional, Dict, Any
from pydantic import Field
from langchain_community.chat_models import ChatZhipuAI

class ChatZhipuAIWithThinking(ChatZhipuAI):
    """
    一个支持 'thinking' 参数的 ChatZhipuAI 子类。
    """
    thinking: Optional[dict[str, str]] = Field(
        default = None,
        description = "用于开启模型的思考模式。"
    )

    @property
    def _default_params(self) -> Dict[str, Any]:
        params = super()._default_params  # 调用父类方法
        if self.thinking is not None:
            params["thinking"] = self.thinking
        return params
