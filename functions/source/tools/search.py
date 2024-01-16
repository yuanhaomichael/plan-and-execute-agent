from langchain.utilities import SerpAPIWrapper
from langchain.tools import BaseTool
from typing import Optional
from langchain.callbacks.manager import CallbackManagerForToolRun
import os

class SearchTool():
    name = "current_search"
    description = """
                  Useful for when you need to answer questions about current events 
                  or the current state of the world
                  """

    def _run(
        self, request: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        result = SerpAPIWrapper().run(request=request, serpapi_api_key=os.environ.get("SERPAPI_API_KEY"))
        return result
    

