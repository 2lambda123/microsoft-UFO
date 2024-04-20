# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


from typing import Dict, List, Type
from PIL import Image
import re

from .. import utils
from ..automator import puppeteer
from ..prompter.agent_prompter import (HostAgentPrompter,
                                       AppAgentPrompter)
from .basic import BasicAgent, Memory

# Lazy import the retriever factory to aviod long loading time.
retriever_factory = utils.LazyImport("..rag.retriever_factory")
control_filter_factory = utils.LazyImport("..automator.ui_control.control_filter_factory")


class HostAgent(BasicAgent):
    """
    The HostAgent class the manager of AppAgents.
    """

    def __init__(self, name: str, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str) -> None:
        """
        Initialize the HostAgent.
        :name: The name of the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        """
        super().__init__(name=name)
        self.prompter = self.get_prompter(is_visual, main_prompt, example_prompt, api_prompt)
        self._memory = Memory()
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None



    def get_prompter(self, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str) -> HostAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The prompter instance.
        """
        return HostAgentPrompter(is_visual, main_prompt, example_prompt, api_prompt)
    

    def message_constructor(self, image_list: List, request_history: str, action_history: str, os_info: str, plan: str, request: str) -> list:
        """
        Construct the message.
        :param image_list: The list of screenshot images.
        :param request_history: The request history.
        :param action_history: The action history.
        :param os_info: The OS information.
        :param plan: The plan.
        :param request: The request.
        :return: The message.
        """
        hostagent_prompt_system_message = self.prompter.system_prompt_construction()
        hostagent_prompt_user_message = self.prompter.user_content_construction(image_list, request_history, action_history, 
                                                                                                  os_info, plan, request)
        
        hostagent_prompt_message = self.prompter.prompt_construction(hostagent_prompt_system_message, hostagent_prompt_user_message)
        
        return hostagent_prompt_message
    

    def print_response(self, response_dict: Dict):
        """
        Print the response.
        :param response: The response.
        """
        
        application = response_dict.get("ControlText")
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        plan = response_dict.get("Plan")
        status = response_dict.get("Status")
        comment = response_dict.get("Comment")

        utils.print_with_color("Observations👀: {observation}".format(observation=observation), "cyan")
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        utils.print_with_color("Selected application📲: {application}".format(application=application), "yellow")
        utils.print_with_color("Status📊: {status}".format(status=status), "blue")
        utils.print_with_color("Next Plan📚: {plan}".format(plan=str(plan).replace("\\n", "\n")), "cyan")
        utils.print_with_color("Comment💬: {comment}".format(comment=comment), "green")



class AppAgent(BasicAgent):
    """
    The HostAgent class the manager of AppAgents.
    """

    def __init__(self, name: str, process_name: str, app_root_name: str, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str, ui_control_interface: Type) -> None:
        """
        Initialize the AppAgent.
        :name: The name of the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :param ui_control_interface: The UI control interface in pywinauto.
        """
        super().__init__(name=name)
        self.prompter = self.get_prompter(is_visual, main_prompt, example_prompt, api_prompt)
        self._memory = Memory()
        self._ui_control_interface = ui_control_interface
        self._process_name = process_name
        self._app_root_name = app_root_name
        self.offline_doc_retriever = None
        self.online_doc_retriever = None
        self.experience_retriever = None
        self.human_demonstration_retriever = None
        self.Puppeteer = self.create_puppteer_interface()


    def get_prompter(self, is_visual: bool, main_prompt: str, example_prompt: str, api_prompt: str) -> AppAgentPrompter:
        """
        Get the prompt for the agent.
        :param is_visual: The flag indicating whether the agent is visual or not.
        :param main_prompt: The main prompt file path.
        :param example_prompt: The example prompt file path.
        :param api_prompt: The API prompt file path.
        :return: The prompter instance.
        """
        return AppAgentPrompter(is_visual, main_prompt, example_prompt, api_prompt)
    

    def message_constructor(self, dynamic_examples: str, dynamic_tips: str, dynamic_knowledge: str, image_list: List,
                             request_history: str, action_history: str, control_info: str, plan: str, request: str, include_last_screenshot: bool) -> list:
        """
        Construct the prompt message for the AppAgent.
        :param dynamic_examples: The dynamic examples retrieved from the self-demonstration and human demonstration.
        :param dynamic_tips: The dynamic tips retrieved from the self-demonstration and human demonstration.
        :param dynamic_knowledge: The dynamic knowledge retrieved from the external knowledge base.
        :param image_list: The list of screenshot images.
        :param request_history: The request history.
        :param action_history: The action history.
        :param control_info: The control information.
        :param plan: The plan.
        :param request: The request.
        :param include_last_screenshot: The flag indicating whether to include the last screenshot.
        :return: The prompt message.
        """
        appagent_prompt_system_message = self.prompter.system_prompt_construction(dynamic_examples, dynamic_tips)
        appagent_prompt_user_message = self.prompter.user_content_construction(image_list, request_history, action_history, 
                                                                                                        control_info, plan, request, dynamic_knowledge, include_last_screenshot)
        
        appagent_prompt_message = self.prompter.prompt_construction(appagent_prompt_system_message, appagent_prompt_user_message)

        return appagent_prompt_message
    


    def print_response(self, response_dict: Dict) -> None:
        """
        Print the response.
        :param response: The response dictionary.
        """
        
        control_text = response_dict.get("ControlText")
        control_label = response_dict.get("ControlLabel")
        observation = response_dict.get("Observation")
        thought = response_dict.get("Thought")
        plan = response_dict.get("Plan")
        status = response_dict.get("Status")
        comment = response_dict.get("Comment")
        function_call = response_dict.get("Function")
        args = utils.revise_line_breaks(response_dict.get("Args"))

        # Generate the function call string
        action = utils.generate_function_call(function_call, args)

        utils.print_with_color("Observations👀: {observation}".format(observation=observation), "cyan")
        utils.print_with_color("Thoughts💡: {thought}".format(thought=thought), "green")
        utils.print_with_color("Selected item🕹️: {control_text}, Label: {label}".format(control_text=control_text, label=control_label), "yellow")
        utils.print_with_color("Action applied⚒️: {action}".format(action=action), "blue")
        utils.print_with_color("Status📊: {status}".format(status=status), "blue")
        utils.print_with_color("Next Plan📚: {plan}".format(plan=str(plan).replace("\\n", "\n")), "cyan")
        utils.print_with_color("Comment💬: {comment}".format(comment=comment), "green")


    def external_knowledge_prompt_helper(self, request: str, offline_top_k: int, online_top_k: int) -> str:
        """
        Retrieve the external knowledge and construct the prompt.
        :param request: The request.
        :param offline_top_k: The number of offline documents to retrieve.
        :param online_top_k: The number of online documents to retrieve.
        :return: The prompt message.
        """

        retrieved_docs = ""

        # Retrieve offline documents and construct the prompt
        if self.offline_doc_retriever:
            offline_docs = self.offline_doc_retriever.retrieve("How to {query} for {app}".format(query=request, app=self._process_name), offline_top_k, filter=None)
            offline_docs_prompt = self.prompter.retrived_documents_prompt_helper("Help Documents", "Document", [doc.metadata["text"] for doc in offline_docs])
            retrieved_docs += offline_docs_prompt

        # Retrieve online documents and construct the prompt
        if self.online_doc_retriever:
            online_search_docs = self.online_doc_retriever.retrieve(request, online_top_k, filter=None)
            online_docs_prompt = self.prompter.retrived_documents_prompt_helper("Online Search Results", "Search Result", [doc.page_content for doc in online_search_docs])
            retrieved_docs += online_docs_prompt

        return retrieved_docs
    

    def rag_experience_retrieve(self, request: str, experience_top_k: int) -> str:
        """
        Retrieving experience examples for the user request.
        :param request: The user request.
        :param experience_top_k: The number of documents to retrieve.
        :return: The retrieved examples and tips string.
        """
        
        # Retrieve experience examples. Only retrieve the examples that are related to the current application.
        experience_docs = self.experience_retriever.retrieve(request, experience_top_k,
                                                                filter=lambda x: self._app_root_name.lower() in [app.lower() for app in x["app_list"]])
        
        if experience_docs:
            examples = [doc.metadata.get("example", {}) for doc in experience_docs]
            tips = [doc.metadata.get("Tips", "") for doc in experience_docs]
        else:
            examples = []
            tips = []

        return examples, tips
    
    
    def rag_demonstration_retrieve(self, request:str, demonstration_top_k: int) -> str:
        """
        Retrieving demonstration examples for the user request.
        :param request: The user request.
        :param demonstration_top_k: The number of documents to retrieve.
        :return: The retrieved examples and tips string.
        """
        
        # Retrieve demonstration examples.
        demonstration_docs = self.human_demonstration_retriever.retrieve(request, demonstration_top_k)
        
        if demonstration_docs:
            examples = [doc.metadata.get("example", {}) for doc in demonstration_docs]
            tips = [doc.metadata.get("Tips", "") for doc in demonstration_docs]
        else:
            examples = []
            tips = []

        return examples, tips
    

    def create_puppteer_interface(self) -> puppeteer.AppPuppeteer:
        """
        Create the Puppeteer interface to automate the app.
        :return: The Puppeteer interface.
        """
        return puppeteer.AppPuppeteer(self._process_name, self._app_root_name, self._ui_control_interface)



    def build_offline_docs_retriever(self) -> None:
        """
        Build the offline docs retriever.
        """
        self.offline_doc_retriever = retriever_factory.OfflineDocRetriever(self._process_name)


    def build_online_search_retriever(self, request: str, top_k: int) -> None:
        """
        Build the online search retriever.
        :param request: The request for online Bing search.
        :param top_k: The number of documents to retrieve.
        """
        self.online_doc_retriever = retriever_factory.OnlineDocRetriever(request, top_k)

    
    def build_experience_retriever(self, db_path: str) -> None:
        """
        Build the experience retriever.
        :param db_path: The path to the experience database.
        :return: The experience retriever.
        """
        self.experience_retriever = retriever_factory.ExperienceRetriever(db_path)


    def build_human_demonstration_retriever(self, db_path: str) -> None:
        """
        Build the human demonstration retriever.
        :param db_path: The path to the human demonstration database.
        :return: The human demonstration retriever.
        """
        self.human_demonstration_retriever = retriever_factory.DemonstrationRetriever(db_path)
        
    def control_filter(self, control_info: list, plan: str, annotation_coor_dict: dict, screenshot: Image, control_filter_type:list,
                        semantic_model_name, semantic_top_k, icon_model_name, icon_top_k) -> list:
        """
        Filters the control information based on the specified control filter type.

        Args:
            control_info (list): The list of control information to be filtered.
            plan (str): The plan string.
            annotation_coor_dict (dict): The dictionary containing annotation coordinates.
            screenshot (Image): The screenshot image.
            control_filter_type (list): The type of control filter to be applied.
            semantic_model_name: The name of the semantic model.
            semantic_top_k: The top k value for semantic filtering.
            icon_model_name: The name of the icon model.
            icon_top_k: The top k value for icon filtering.

        Returns:
            list: The filtered control information.

        Raises:
            ValueError: If an unsupported control filter type is provided.
        """
        
        control_filter_type_lower = [control_filter_type_lower.lower() for control_filter_type_lower in control_filter_type]
        is_text_required = 'text' in control_filter_type_lower
        is_semantic_required = 'semantic' in control_filter_type_lower
        is_icon_required = 'icon' in control_filter_type_lower
        
        if control_filter_type and not (is_text_required or is_semantic_required or is_icon_required):
            
            raise ValueError(f"Unsupported CONTROL_FILTER_TYPE: {control_filter_type}")
        
        elif not control_filter_type:
            
            return control_info
        else:
            filtered_control_info = []
            
            keywords = self.plan_to_keywords(plan)
            
            if is_text_required:
                self.text_control_filter(filtered_control_info, control_info, keywords)
            
            if is_semantic_required:
                self.semantic_control_filter(filtered_control_info, control_info, keywords, semantic_model_name, semantic_top_k)
            
            if is_icon_required:                
                self.icon_control_filter(filtered_control_info, control_info, annotation_coor_dict, screenshot, icon_model_name, icon_top_k, keywords)

        return filtered_control_info

    

    def text_control_filter(self, filtered_control_info: list, control_info: list, keywords: list) -> list:
        """
        Filters the control information based on the text control filter.

        Args:
            filtered_control_info (list): The list of already filtered control items.
            control_info (list): The list of control information to be filtered.
            plan (str): A list of keywords extracted from the plan.
        """
        control_filter_factory.TextControlFilter.control_filter(filtered_control_info, control_info, keywords)
    
    def semantic_control_filter(self, filtered_control_info: list, control_info: list, keywords: list, semantic_model_name: str, semantic_top_k: int) -> list:
        """
        Filters the control information based on the semantic control filter.

        Args:
            filtered_control_info (list): The list of already filtered control items.
            control_info (list): The list of control information to be filtered.
            keywords (list): A list of keywords.
            semantic_model_name: The name of the semantic model.
            semantic_top_k: The top k value for semantic filtering.
        """
        model_semantic = control_filter_factory.SemanticControlFilter(semantic_model_name)
        model_semantic.control_filter(filtered_control_info, control_info, keywords, semantic_top_k)
    
    def icon_control_filter(self, filtered_control_info: list, control_info: list, annotation_coor_dict: dict, screenshot: Image, icon_model_name: str, icon_top_k: int, keywords: list) -> list:
        """
        Filters the control information based on the icon control filter.

        Args:
            filtered_control_info (list): The list of already filtered control items.
            control_info (list): The list of control information to be filtered.
            annotation_coor_dict (dict): The dictionary containing annotation coordinates.
            screenshot (Image): The screenshot image.
            icon_model_name: The name of the icon model.
            icon_top_k: The top k value for icon filtering.
            filtered_control_info (list): The list of already filtered control items.
            keywords (list): A list of keywords.
        """
        model_icon = control_filter_factory.IconControlFilter(icon_model_name)
        model_icon.control_filter(filtered_control_info, control_info, annotation_coor_dict, screenshot, keywords, icon_top_k)
    
    def plan_to_keywords(self, plan):
            """
            Gets keywords from the plan.

            Args:
                plan (str): The plan to be parsed.

            Returns:
                list: A list of keywords extracted from the plan.
            """
            plans = plan.split("\n")
            keywords = []
            for plan in plans:
                words = plan.replace("'", "").strip(".").split()
                words = [word for word in words if word.isalpha() or bool(re.fullmatch(r'[\u4e00-\u9fa5]+', word))]
                keywords.extend(words)
            return keywords

    