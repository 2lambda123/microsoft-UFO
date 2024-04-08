# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
from datetime import datetime

import threading, sys, time

from .config.config import load_config
from .module import flow
from .utils import print_with_color



configs = load_config()


global cur_session
cur_session = None

termination_signal = threading.Event()
usr_confirmation_signal = threading.Event()
terminate_old_ufo_signal = threading.Event()



args = argparse.ArgumentParser()
args.add_argument("--task", help="The name of current task.",
                  type=str, default=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))

parsed_args = args.parse_args()

class InputIntegrater:
    def __init__(self):
        self.current_session = None

    def process_web_input(self, input_from_web):
        """
        Process an input coming from Taskweaver.
        :param input_from_taskweaver: The input to be processed.
        """
        if self.current_session is None:
            self.current_session = cur_session
        while self.current_session is None:
            pass
        if self.current_session is not None:
            self.current_session.update_query(input_from_web)
        else:
            print("No active session to process the input.")
    
    def terminate_ufo(self):
        termination_signal.set()

    def pass_confirmation(self):
        usr_confirmation_signal.set()

    def newrequest_listener(self):
        if self.current_session is None:
            self.current_session = cur_session
        print("new request signal received")
        terminate_old_ufo_signal.set()




def main(arg = ""):
    """
    Main function.
    """
    if arg == "web" or arg == "taskweaver":
        session = flow.Session(arg)
    else:
        session = flow.Session(parsed_args.task)
    global cur_session
    cur_session = session
    if arg == "web" or arg == "taskweaver":
        if session.request is None:
            while not session.query_updated.is_set():
                if terminate_old_ufo_signal.is_set():
                    terminate_old_ufo_signal.clear()
                    return
            if session.query_updated.is_set():
                session.query_updated.clear()
                session.request = session.usr_query
    step = 0
    status = session.get_status()
    round = session.get_round()

    if terminate_old_ufo_signal.is_set():
        terminate_old_ufo_signal.clear()
        return
    while status.upper() not in ["ALLFINISH", "ERROR", "MAX_STEP_REACHED"] and terminate_old_ufo_signal.is_set() == False:
        round = session.get_round()
        if terminate_old_ufo_signal.is_set():
            terminate_old_ufo_signal.clear()
            return
        if status == "FINISH":
            session.set_new_round()
            status = session.get_status()
            if status == "ALLFINISH":
                if session.experience_asker():
                    session.experience_saver()
                break
        if terminate_old_ufo_signal.is_set():
            terminate_old_ufo_signal.clear()
            return
# split main function
# merge open app / file

        while status.upper() not in ["FINISH", "ERROR"] and step <= configs["MAX_STEP"]:
            if terminate_old_ufo_signal.is_set():
                return
            session.process_application_selection()
            step = session.get_step()
            status = session.get_status()
            if arg == "web":
                print("start waiting for confirmation")
                usr_confirmation_signal.wait()
                usr_confirmation_signal.clear()
                print("end waiting for confirmation")
                print("check termination")
                if termination_signal.is_set():
                    print("termination signal received")
                    status = "FINISH"
            
            while status.upper() not in ["FINISH", "ERROR"] and step <= configs["MAX_STEP"]:

                session.process_action_selection()
                status = session.get_status()
                step = session.get_step()

                if status == "APP_SELECTION":
                    print_with_color(
                        "Step {step}: Switching to New Application".format(step=step), "magenta")
                    app_window = session.get_application_window()
                    app_window.minimize()
                    break

            if status == "FINISH":
                print_with_color("Task Completed.", "magenta")
                if session.task == "web":
                    return
                break

            if step > configs["MAX_STEP"]:
                print_with_color("Max step reached.", "magenta")
                status = "MAX_STEP_REACHED"
                break
        if terminate_old_ufo_signal.is_set():
            return
        result = session.get_results()
        round = session.get_round()


        # Print the result
        if result != "":
            print_with_color("Result for round {round}:".format(
                round=round), "magenta")
            print_with_color("{result}".format(result=result), "yellow")

    
    # Print the total cost
    total_cost = session.get_cost()
    if isinstance(total_cost, float):
        formatted_cost = '${:.2f}'.format(total_cost)
        print_with_color(f"Request total cost is {formatted_cost}", "yellow")
    return status


    
if __name__ == "__main__":
    main()
