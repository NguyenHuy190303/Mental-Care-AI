import os
from abc import ABC, ABCMeta, abstractmethod

import openai
from llama_index.core.workflow import Workflow


# Create a custom metaclass that combines WorkflowMeta and ABCMeta
class WorkflowABCMeta(type(Workflow), ABCMeta):
    pass


class BaseWorkflow(Workflow, ABC, metaclass=WorkflowABCMeta):
    """
    BaseWorkflow serves as an abstract base class for creating various workflows
    that interact with the OpenAI API. It provides a structure for initializing
    the workflow with a specified timeout and verbosity level, and it manages
    the OpenAI client for asynchronous operations.

    Attributes:
        client (AsyncOpenAI): An instance of the OpenAI client for making API calls.
        memory (Any): Placeholder for memory management, to be defined in subclasses.

    Args:
        timeout (int): The maximum time (in seconds) to wait for a response before timing out.
        verbose (bool): Flag to enable verbose logging for debugging purposes.
    """

    def __init__(self, timeout: int = 60, verbose: bool = True):
        """
        Initialize the BaseWorkflow.

        This constructor sets up the OpenAI client with the provided API key and base URL.
        It also initializes the memory attribute, which can be utilized by subclasses
        for managing conversation history or context.

        Args:
            timeout (int): The maximum time (in seconds) to wait for a response before timing out.
            verbose (bool): Flag to enable verbose logging for debugging purposes.
        """
        super().__init__(timeout=timeout, verbose=verbose)
        self.client = openai.AsyncOpenAI(
            api_key="anything",  # Don't need the real API key when using Litellm
            base_url=os.environ.get("LITELLM_BASE_URL", "http://localhost:4000"),
        )
        self.memory = None

    @abstractmethod
    async def execute_request_workflow(
        self,
        user_input: str,
    ) -> str:
        """
        Execute the request workflow.

        This method must be implemented by subclasses to define how user input is processed
        and how responses are generated. It should handle the logic for interacting with
        the OpenAI API and managing any necessary state or context.

        Args:
            user_input (str): The input provided by the user that needs to be processed.

        Returns:
            str: The response generated by the workflow after processing the user input.
        """
        pass