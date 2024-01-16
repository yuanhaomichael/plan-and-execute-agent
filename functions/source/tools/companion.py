from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
import os

class Companion:

  def chat(self, params, mode): 
    request = params.get("user_task", "tell me a joke")
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key="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", max_tokens=1000)
    return {
      "_text": llm.predict(request)
    }
