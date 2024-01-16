from typing import Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from llama_index import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage
from llama_index.llms import OpenAI
from pydantic import BaseModel, Field

class DocumentationResearcherInput(BaseModel):
    """Inputs for research_documentation"""

    user_request: str = Field(description="User request")
    user_context: str = Field(description="User context, all neccessary data that could used for as data to generate code")
    instruction: str = Field(description="The instruction that I should provide documentation for")


class DocumentationResearcher(BaseTool):
    name = "research_documentation"
    description = """
        Useful for research of API documentation of services.
        You should enter the user request that user provided before.
        You should enter the user context, the result provided by user_context_provider.
        You should enter the instruction by instructions_provider that I should provide documentation for.
        Output will be all neccessary information for code generator to generate proper code.
        """
    args_schema: Type[BaseModel] = DocumentationResearcherInput

    def _run(
        self, user_request: str, user_context: str, instruction: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""

        prompt = f"""You are an expert in API documentation.
        Provide helpful information to achieve complete instruction: {instruction}; 
        Use only information provided in the files that provided.
        Provide multiple examples of code and detailed explenation.
        Provide useful information and examples for code_generator.

        user_request: {user_request};
        User context: {user_context};

        Read authorization.pdf and include authorization flow into the code.
        """

        reader = SimpleDirectoryReader(
            input_dir="/Users/azatian/projects/Jarvis-AI/calendar_api_docs")

        docs = reader.load_data()
        index = VectorStoreIndex.from_documents(docs)

        index.storage_context.persist()

        storage_context = StorageContext.from_defaults(persist_dir="./storage")
        index = load_index_from_storage(storage_context)
        query_engine = index.as_query_engine()
        response = query_engine.query(prompt)

        return response


# def search_context_in_docs(userRequest):

#     setup_api_key()

#     reader = SimpleDirectoryReader(
#         input_files=["/Users/azatian/projects/Jarvis-AI/calendar_api_docs/python_quick_start.pdf",
#                      "/Users/azatian/projects/Jarvis/calendar_api_docs/insert_event.pdf"]
#     )

#     docs = reader.load_data()
#     index = VectorStoreIndex.from_documents(docs)


#     storage_context = StorageContext.from_defaults(persist_dir="./storage")
#     index = load_index_from_storage(storage_context)

#     query_engine = index.as_query_engine()
#     response = query_engine.query(userRequest)

#     return response
