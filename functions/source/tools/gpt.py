from langchain.chat_models import ChatOpenAI

class GPT:
  model_smart = ChatOpenAI(temperature=0, model_name="gpt-4")
  model_dumb = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo")