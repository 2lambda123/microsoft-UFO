# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from logging import Logger
from typing import Optional
import os, dill, uuid, copy
from typing import List
from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.states.app_agent_state import ContinueAppAgentState
from ufo.agents.states.host_agent_state import ContinueHostAgentState
from ufo.config.config import Config
from ufo.module import interactor
from ufo.module.basic import BaseRound, BaseSession
from ufo.module.sessions.plan_reader import PlanReader
from ufo.module.context import ContextNames

configs = Config.get_instance().config_data

global session_id
session_id = ''


class SessionManager:
    """
    The manager for the UFO sessions.
    """
    def __init__(self):
        self.sessions = {}
        self.confirmation_locked = False
        self.session_id = None


    def generate_session_id(self) -> str:
        """
        Generate a unique session ID.
        """
        return str(uuid.uuid4())
    

    def get_state(self) -> dict:
        """
        Get the state of the current session.
        """
        if self.sessions[self.session_id][0].current_round is None:
            return {"response": "No session running"}
        state_info = {
            "state_name": self.sessions[self.session_id][0].current_round.state.name()  # Assuming state has a 'name' attribute
        }
        return state_info
    

    def get_session_file_path(self, session_id: str = '') -> str:
        """
        Get the absolute file path for the session.
        """
        current_working_dir = os.path.join(os.getcwd(), 'stored_sessions')
        if session_id == '':
            return os.path.join(current_working_dir, f'session_{self.session_id}.pkl')
        return os.path.join(current_working_dir, f'session_{session_id}.pkl')


    def store_session(self) -> None:
        """
        Store the session in memory.
        :param session_id: The ID of the session to store.
        """
        new_session_id = self.generate_session_id()
        session = self.sessions[self.session_id][0]
        session_copy = copy.deepcopy(session)  # Create a deep copy of the session
        self.sessions[new_session_id] = [session_copy]
        print(f"Session {new_session_id} stored in memory.")
        self.terminate_session()  # 


    def load_session(self, session_id):
        """
        Load the session from a file.
        :param session_id: The ID of the session to load.
        """
        if session_id in self.sessions:
            print(f"Session {session_id} already loaded.")
            return self.sessions[session_id]
        ValueError(f"No session found with ID: {session_id}")
        
        # file_path = self.get_session_file_path(session_id)
        # if os.path.exists(file_path):
        #     with open(file_path, 'rb') as f:
        #         sessions = dill.load(f)
        #         sessions[0].initialize_logger()  # Reinitialize logger after deserialization
        #         self.sessions[session_id] = sessions
        #         self.session_id = session_id
        # else:
        #     print(f"No session found with ID: {session_id}")
        #     self.sessions[session_id] = None
        # return self.sessions[session_id]


    def unlock_confirmation(self) -> None:
        """
        Unlock the confirmation for a specific session.
        :param session_id: The ID of the session to unlock confirmation.
        """
        self.sessions[self.session_id][0]._host_agent.usr_confirmation_lock.set()


    def terminate_session(self) -> None:
        """
        Terminate a specific session.
        :param session_id: The ID of the session to terminate.
        """
        print("terminated")
        self.sessions[self.session_id][0]._host_agent.status = "FINISH"
        self.sessions[self.session_id][0]._host_agent.usr_confirmation_lock.set()

    def pause_session(self) -> Optional[dict]:
        round = self.sessions[self.session_id][0].current_round
        if round is not None:
            round.pause_event.clear()
        else:
            return {'response': 'No session running'}


    def resume_session(self) -> Optional[dict]:
        round = self.sessions[self.session_id][0].current_round
        if round is not None:
            round.pause_event.set()
        else:
            return {'response': 'No session running'}


Global_Session = SessionManager()

class SessionFactory:
    """
    The factory class to create a session.
    """
    def create_session(self, task: str, mode: str, plan: str) -> str:
        """
        Create a new session with a unique ID.
        """
        session_id = Global_Session.generate_session_id()
        Global_Session.session_id = session_id
        if mode == "normal":
            Global_Session.sessions[session_id] = [Session(task, configs.get("EVA_SESSION", False), id=session_id)]
        elif mode == "follower":
            if self.is_folder(plan):
                Global_Session.sessions[session_id] = self.create_follower_session_in_batch(task, plan, session_id)
            else:
                Global_Session.sessions[session_id] = [
                    FollowerSession(task, plan, configs.get("EVA_SESSION", False), id=session_id)
                ]
        else:
            raise ValueError(f"The {mode} mode is not supported.")
        print(f"New session created with ID: {session_id}")
        return Global_Session.sessions[session_id], session_id

    def create_follower_session_in_batch(
        self, task: str, plan: str
    ) -> List[BaseSession]:
        """
        Create a follower session.
        :param task: The name of current task.
        :param plan: The path folder of all plan files.
        :return: The list of created follower sessions.
        """
        plan_files = self.get_plan_files(plan)
        file_names = [self.get_file_name_without_extension(f) for f in plan_files]
        sessions = [
            FollowerSession(
                f"{task}/{file_name}",
                plan_file,
                configs.get("EVA_SESSION", False),
                id=i,
            )
            for i, (file_name, plan_file) in enumerate(zip(file_names, plan_files))
        ]

        return sessions

    @staticmethod
    def is_folder(path: str) -> bool:
        """
        Check if the path is a folder.
        :param path: The path to check.
        :return: True if the path is a folder, False otherwise.
        """
        return os.path.isdir(path)

    @staticmethod
    def get_plan_files(path: str) -> List[str]:
        """
        Get the plan files in the folder. The plan file should have the extension ".json".
        :param path: The path of the folder.
        :return: The plan files in the folder.
        """
        return [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".json")]

    def get_file_name_without_extension(self, file_path: str) -> str:
        """
        Get the file name without extension.
        :param file_path: The path of the file.
        :return: The file name without extension.
        """
        return os.path.splitext(os.path.basename(file_path))[0]


class Session(BaseSession):
    """
    A session for UFO.
    """

    def __deepcopy__(self, memo):
        # Create a new instance of Session
        new_session = self.__class__.__new__(self.__class__)
        
        # Add the new instance to the memo dictionary
        memo[id(self)] = new_session
        
        # Copy each attribute
        for key, value in self.__dict__.items():
            if key == 'uia_wrapper':
                # Store element_info instead of the UIAWrapper instance
                setattr(new_session, 'uia_wrapper', None)
            else:
                setattr(new_session, key, copy.deepcopy(value, memo))
        
        # Restore the UIAWrapper instance after deepcopy
        if self._original_application_window.element_info:
            new_session.uia_wrapper = UIAWrapper(self.element_info)
        
        return new_session


    def run(self) -> None:
        """
        Run the session.
        """
        super().run()
        # Save the experience if the user asks so.
        if interactor.experience_asker():
            self.experience_saver()

    def init_logger(self) -> None:
        super().init_logger()
    
    def remove_logger(self) -> None:
        super().remove_logger()

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "normal")

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.next_request()

        # Create a new round and return None if the session is finished.

        if self.is_finished():
            return None

        self._host_agent.set_state(ContinueHostAgentState())

        round = BaseRound(
            request=request,
            agent=self._host_agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def next_request(self) -> str:
        """
        Get the request for the host agent.
        :return: The request for the host agent.
        """

        if self.total_rounds == 0:
            utils.print_with_color(interactor.WELCOME_TEXT, "cyan")
            return interactor.first_request()
        else:
            request, iscomplete = interactor.new_request()
            if iscomplete:
                self._finish = True
            return request

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """
        request_memory = self._host_agent.blackboard.requests
        return request_memory.to_json()

    def remove_nonserializable(self):
        """
        Remove or convert non-serializable attributes to serializable format.
        """
        # self._original_application_window = self.context.get(ContextNames.APPLICATION_WINDOW)
        # if isinstance(self._original_application_window, UIAWrapper):
        print(type(self.context.get(ContextNames.APPLICATION_WINDOW)), self.context.get(ContextNames.APPLICATION_WINDOW))
        self._original_application_window = self.context.get(ContextNames.APPLICATION_WINDOW)
        if isinstance(self._original_application_window, UIAWrapper):
            self.context.set(ContextNames.APPLICATION_WINDOW, self._original_application_window.element_info)
        # self.context.set(ContextNames.APPLICATION_WINDOW, self.context.get(ContextNames.APPLICATION_WINDOW).element_info)
        self._original_host_agent_application_window = self._host_agent.processor.application_window
        if isinstance(self._original_host_agent_application_window, UIAWrapper):
            self._host_agent.processor.application_window = self._original_host_agent_application_window.element_info
        self._original_logger = self.context.get(ContextNames.LOGGER)
        self._original_request_logger = self.context.get(ContextNames.REQUEST_LOGGER)
        self._original_evaluation_logger = self.context.get(ContextNames.EVALUATION_LOGGER)
        
        self.context.set(ContextNames.LOGGER, None)
        self.context.set(ContextNames.REQUEST_LOGGER, None)
        self.context.set(ContextNames.EVALUATION_LOGGER, None)


    def restore_nonserializable(self):
        """
        Restore non-serializable attributes from their serializable format.
        """

        if isinstance(self.context.get(ContextNames.APPLICATION_WINDOW), UIAWrapper):
            self.context.set(ContextNames.APPLICATION_WINDOW, UIAWrapper(self.context.get(ContextNames.APPLICATION_WINDOW)))
        self._host_agent.processor.application_window = UIAWrapper(self._host_agent.processor.application_window)
        self.context.set(ContextNames.LOGGER, self._original_logger)
        self.context.set(ContextNames.REQUEST_LOGGER, self._original_request_logger)
        self.context.set(ContextNames.EVALUATION_LOGGER, self._original_evaluation_logger)
    def __getstate__(self):
        state = self.__dict__.copy()
        self.remove_nonserializable()
        return state


    def __setstate__(self, state):
        print("ERROR")
        self.__dict__.update(state)
        print("Restoring non-serializable attributes")
        self.restore_nonserializable()

class FollowerSession(BaseSession):
    """
    A session for following a list of plan for action taken.
    This session is used for the follower agent, which accepts a plan file to follow using the PlanReader.
    """

    def __init__(
        self, task: str, plan_file: str, should_evaluate: bool, id: int
    ) -> None:
        """
        Initialize a session.
        :param task: The name of current task.
        :param plan_dir: The path of the plan file to follow.
        :param should_evaluate: Whether to evaluate the session.
        :param id: The id of the session.
        """

        super().__init__(task, should_evaluate, id)

        self.plan_reader = PlanReader(plan_file)

    def _init_context(self) -> None:
        """
        Initialize the context.
        """
        super()._init_context()

        self.context.set(ContextNames.MODE, "follower")

    def create_new_round(self) -> None:
        """
        Create a new round.
        """

        # Get a request for the new round.
        request = self.next_request()

        # Create a new round and return None if the session is finished.
        if self.is_finished():
            return None

        if self.total_rounds == 0:
            utils.print_with_color("Complete the following request:", "yellow")
            utils.print_with_color(self.plan_reader.get_initial_request(), "cyan")
            agent = self._host_agent
        else:
            agent = self._host_agent.get_active_appagent()

            # Clear the memory and set the state to continue the app agent.
            agent.clear_memory()
            agent.blackboard.requests.clear()

            agent.set_state(ContinueAppAgentState())

            utils.print_with_color(
                "Starting step {round}:".format(round=self.total_rounds), "yellow"
            )
            utils.print_with_color(request, "cyan")

        round = BaseRound(
            request=request,
            agent=agent,
            context=self.context,
            should_evaluate=configs.get("EVA_ROUND", False),
            id=self.total_rounds,
        )

        self.add_round(round.id, round)

        return round

    def next_request(self) -> str:
        """
        Get the request for the new round.
        """

        # If the task is finished, return an empty string.
        if self.plan_reader.task_finished():
            self._finish = True
            return ""

        # Get the request from the plan reader.
        if self.total_rounds == 0:
            return self.plan_reader.get_host_agent_request()
        else:
            return self.plan_reader.next_step()

    def request_to_evaluate(self) -> bool:
        """
        Check if the session should be evaluated.
        :return: True if the session should be evaluated, False otherwise.
        """

        return self.plan_reader.get_task()
