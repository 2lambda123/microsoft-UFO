import signal
import asyncio
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time, threading, sys, re
from typing import Optional, Dict, Literal


UFO_PATH = r"C:\Users\v-liuhengyu\OneDrive - Microsoft\Desktop\UFO"
terminate_signal = threading.Event()
plan_signal = threading.Event()
save_exp = threading.Event()
device_login = threading.Event()

global plan_first_return
plan_first_return = []
global comment_to_return
comment_to_return = None
global login_info
login_info = None


class WebApp:
    def __init__(self) -> None:
        self.ufo_running = False
        self.main_thread = None
        self.input_thread = None
        self.output_plan = False
        self.error = None
        self.status = "AWAITING"

    def simulate_args(self, task: str):
        sys.argv = ['ufo.py', '--task', task]
        print(sys.argv)

    def ufo_start(self, task_name):
        old_stdout = sys.stdout
        sys.stdout = StdoutWrapper(old_stdout)
        self.simulate_args(task_name)
        try:
            from ufo.ufo import main as ufo_main
            self.ufo_running = True
            ufo_main()  # Execution of UFO, with output captured and processed by custom_buffer
            print("UFO finished")
            self.status = "AWAITING"
            self.ufo_running = False
        except Exception as e:
            self.error = e
            self.ufo_running = False
        finally:
            sys.stdout = old_stdout
            pass


class StdoutWrapper:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.accumulated_output = ""
        self.terminate_signal = terminate_signal
        self.finished = False
        self.plans = []
        self.current_plan = None
        self.final_comment = None
        self.state = None

    def write(self, s):
        self.accumulated_output += s
        if "\n" in self.accumulated_output:  
            lines = self.accumulated_output.split("\n")
            for line in lines[:-1]:  
                self.process_line(line)
            self.accumulated_output = lines[-1]  

    def flush(self):
        self.original_stdout.flush()

    def process_line(self, line):
        self.original_stdout.write(line + '\n')
        
        if "Observations" in line or "Selected item" in line or "Thoughts" in line:
            return

        if 'Next Plan' in line:
            self.current_plan = {'plan': line}
            self.plans.append(self.current_plan)  
            return  

        if 'Comment' in line:
            self.final_comment = line
            self.current_plan = None  
            plan_signal.set() 
            self.original_stdout.write(str(self.plans))
            global plan_first_return
            plan_first_return = self.get_cleaned_plans()
            self.plans = []
            return  
        
        if self.current_plan:
            self.current_plan['plan'] += line

        if "Please enter your new request. Enter 'N' for exit." in line or "Request total cost is" in line or "[Input Required:]" in line or "Task Completed" in line:
            terminate_signal.set()
            self.finished = True 
            global comment_to_return
            comment_to_return = self.clean_ansi_codes(self.final_comment)
            return
        
        if "Would you like to save the current conversation flow for future reference by the agent?" in line:
            save_exp.set()
            return
        
        if "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code" in line:
            device_login.set()
            global login_info
            login_info = line
            return
    
    def clean_ansi_codes(self, text):
        ansi_escape = re.compile(r'\x1b\[.*?m')
        return ansi_escape.sub('', text)
    
    def get_cleaned_plans(self):
        combined_plans = '\n'.join([self.clean_ansi_codes(plan['plan']) for plan in self.plans])
        response_data = {"response": combined_plans}
        return response_data
    
    def __getattr__(self, attr):
        return getattr(self.original_stdout, attr)


class Status:
    AWAITING = "AWAITING"
    WAITINGREQUEST = "WAITINGREQUEST"
    RUNNING = "RUNNING"
    CONFIRMATION = "CONFIRMATION"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    ROUNDFINISHED = "ROUNDFINISHED"
    EVALUATING = "EVALUATING"
    SAVEEXP = "SAVEEXP"



class ApiResponse(BaseModel):
    status: Literal[
        "AWAITING", "WAITINGREQUEST", "RUNNING", "CONFIRMATION", 
        "COMPLETED", "ERROR", "ROUNDFINISHED", "EVALUATING", "SAVEEXP"
    ]
    message: Optional[str] = None
    data: Optional[Dict] = None

    class Config:
        schema_extra = {
            "example": {
                "status": "RUNNING",
                "message": "Operation successful",
                "data": {"key": "value"}
            }
        }

class StartRequest(BaseModel):
    task: str

    class Config:
        schema_extra = {
            "example": {
                "task": "your_task_name"
            }
        }

class UserRequest(BaseModel):
    request: str

    class Config:
        schema_extra = {
            "example": {
                "request": "Open outlook and initiate an email to Peter."
            }
        }

class ConfirmationRequest(BaseModel):
    confirmation: str

    class Config:
        schema_extra = {
            "example": {
                "confirmation": "Y"
            }
        }

class RetrieveSessionRequest(BaseModel):
    session_id: str

    class Config:
        schema_extra = {
            "example": {
                "session_id": "12345"
            }
        }


def shutdown():
    print("Shutting down gracefully...")
    asyncio.get_event_loop().stop()



web_app_instance = WebApp()

global usr_confirmation
usr_confirmation = True

from ufo.module.interactor import web_input_manager
from ufo.module.sessions.session import Global_Session


def clear_cached_input() -> None:
    web_input_manager.clear_input('usr_request')
    web_input_manager.clear_input('confirmation')


app = FastAPI()

@app.post("/ufo/start", response_model=ApiResponse, response_description="Start the UFO instance.")
async def start_ufo(request: StartRequest):
    """
    Start the UFO instance with a given task.

    - **task**: Name of the task to start
    """
    clear_cached_input()
    if not web_app_instance.ufo_running:
        web_app_instance.main_thread = threading.Thread(target=web_app_instance.ufo_start, args=(request.task,))
        web_app_instance.main_thread.start()
        web_app_instance.status = Status.WAITINGREQUEST
        return ApiResponse(status=web_app_instance.status, message="UFO instance started")
    else:
        return ApiResponse(status=Status.ERROR, message="UFO instance already running")


@app.post("/ufo/request", response_model=ApiResponse, response_description="Handle user request.")
async def handle_request(request: UserRequest):
    """
    Handle user request.

    - **request**: JSON object with the user's request
    """
    if not web_app_instance.ufo_running:
        return ApiResponse(status=Status.AWAITING, message="UFO not running")
    global plan_first_return
    plan_first_return = []
    usr_request = request.request
    if web_app_instance.status != Status.WAITINGREQUEST and web_app_instance.status != Status.ROUNDFINISHED and web_app_instance.status != Status.COMPLETED:
        return ApiResponse(status=web_app_instance.status, message="No request expected")
    if usr_request.upper() == 'Y' or usr_request.upper() == 'N':
        web_input_manager.set_input('confirmation', usr_request)
        if web_app_instance.status == Status.ROUNDFINISHED:
            web_app_instance.status = Status.EVALUATING
    else:
        web_input_manager.set_input('usr_request', usr_request)
        web_app_instance.status = Status.RUNNING
    return ApiResponse(status=web_app_instance.status, message="Request received")


@app.post("/ufo/save_session", response_model=ApiResponse, response_description="Save the current session.")
async def save_session():
    """
    Save the current session.
    """
    session_id = Global_Session.store_session()
    return ApiResponse(status=web_app_instance.status, data={"session_id": session_id})


@app.post("/ufo/retrieve_session", response_model=ApiResponse, response_description="Retrieve a saved session.")
async def retrieve_session(request: RetrieveSessionRequest):
    """
    Retrieve a saved session using the session ID.

    - **session_id**: The ID of the session to retrieve
    """
    session_id = request.session_id
    Global_Session.load_session(session_id)
    return ApiResponse(status=web_app_instance.status, message="Session loaded")


@app.get("/ufo/get_status", response_model=ApiResponse, response_description="Get the current status of the UFO instance.")
async def get_status():
    """
    Get the current status of the UFO instance.
    """
    if not web_app_instance.ufo_running:
        web_app_instance.status = Status.AWAITING
    status = ApiResponse(status=web_app_instance.status)
    if plan_signal.is_set():
        plan_signal.clear()
        status.message = plan_first_return
        status.status = Status.CONFIRMATION
        web_app_instance.status = Status.CONFIRMATION
    if terminate_signal.is_set():
        terminate_signal.clear()
        global comment_to_return
        comment_ret = comment_to_return
        comment_to_return = None
        final_ret_str = f"{comment_ret}\nPlease enter your new request. Enter 'N' for exit."
        status.message = final_ret_str
        status.status = Status.ROUNDFINISHED
        web_app_instance.status = Status.ROUNDFINISHED
    if save_exp.is_set():
        save_exp.clear()
        status.status = Status.SAVEEXP
        web_app_instance.status = Status.SAVEEXP
    if device_login.is_set():
        status.message = login_info
        device_login.clear()
    return status


@app.get("/ufo/get_session_state", response_model=ApiResponse, response_description="Get the current state of the session.")
async def get_session_state():
    """
    Get the current state of the session.
    """
    if not web_app_instance.ufo_running:
        return ApiResponse(web_app_instance.status, message="UFO not running")
    state = Global_Session.get_state()
    return ApiResponse(web_app_instance.status, data=state)


@app.get("/ufo/pause", response_model=ApiResponse, response_description="Pause the current session.")
async def pause_ufo():
    """
    Pause the current session.
    """
    if not web_app_instance.ufo_running:
        return ApiResponse(web_app_instance.status, message="UFO not running")
    response = Global_Session.pause_session()
    if not response:
        return ApiResponse(web_app_instance.status, message="Session paused")
    return ApiResponse(status=Status.ERROR, message=response)


@app.get("/ufo/resume", response_model=ApiResponse, response_description="Resume the current session.")
async def resume_ufo():
    """
    Resume the current session.
    """
    if not web_app_instance.ufo_running:
        return ApiResponse(web_app_instance.status, message="UFO not running")
    response = Global_Session.resume_session()
    if not response:
        return ApiResponse(web_app_instance.status, message="Session resumed")
    return ApiResponse(status=Status.ERROR, message=response)


@app.post("/ufo/confirmation", response_model=ApiResponse, response_description="The confirmation response.")
async def confirmation(request: ConfirmationRequest):
    """
    Handle user confirmation.

    - **confirmation**: The user confirmation, expected values are 'Y' or 'N'
    """
    if not web_app_instance.ufo_running:
        return ApiResponse(web_app_instance.status, message="UFO not running")
    web_input_manager.set_input('confirmation', request.confirmation)

    if web_app_instance.status == Status.CONFIRMATION:
        web_input_manager.clear_input('confirmation')
        if request.confirmation == 'Y':
            plan_signal.clear()
            Global_Session.unlock_confirmation()
        else: 
            global usr_confirmation
            usr_confirmation = False
            Global_Session.terminate_session()
            if terminate_signal.is_set():
                terminate_signal.clear()
            web_app_instance.status = Status.ROUNDFINISHED
            return ApiResponse(status=web_app_instance.status, message="Please enter your new request. Enter 'N' for exit.")
        
    if web_app_instance.status == Status.SAVEEXP:
        web_app_instance.status = Status.COMPLETED
        return ApiResponse(status=web_app_instance.status, message="TASK COMPLETED")
    web_app_instance.status = Status.RUNNING
    return ApiResponse(status=web_app_instance.status, message="Confirmation received")


if __name__ == '__main__':
    import uvicorn
    signal.signal(signal.SIGINT, lambda s, f: shutdown())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown())
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
