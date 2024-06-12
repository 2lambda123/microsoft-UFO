from flask import Flask, request, jsonify
import time, threading, sys, re

# # run this flask server under UFO folder: python -m ufo.app

app = Flask(__name__)

UFO_PATH = r"C:\Users\v-liuhengyu\OneDrive - Microsoft\Desktop\UFO"
terminate_signal = threading.Event()
plan_signal = threading.Event()
terminate_old_ufo = threading.Event()   

global plan_first_return
plan_first_return = []
global comment_to_return
comment_to_return = None



class Web_app():

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
            if terminate_old_ufo.is_set():
                return
            terminate_signal.set()
            self.finished = True 
            global comment_to_return
            comment_to_return = self.clean_ansi_codes(self.final_comment)
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

web_app_instance = Web_app()

global usr_confirmation
usr_confirmation = True

from ufo.module.interactor import web_input_manager
from ufo.module.sessions.session import Global_Session


def clear_cached_input() -> None:
    web_input_manager.clear_input('usr_request')
    web_input_manager.clear_input('confirmation')

@app.route('/ufo/start', methods=['POST'])
def start_ufo():
    task_name = request.form.get('task', 'web') 
    clear_cached_input()
    if not web_app_instance.ufo_running:
        web_app_instance.main_thread = threading.Thread(target=web_app_instance.ufo_start, args=(task_name,))
        web_app_instance.main_thread.start()
        web_app_instance.status = 'RUNNING'
        return jsonify({"response": "UFO instance started"}), 200
    else:
        return jsonify({"response": "UFO instance already running"}), 200


@app.route('/ufo/request', methods=['POST'])
def handle_request():
    if not web_app_instance.ufo_running:
        return jsonify({"response": "UFO not running"}), 200
    global plan_first_return
    plan_first_return = []
    usr_request = request.json.get('request', 'No Request, end UFO')
    if usr_request.upper() == 'Y' or usr_request.upper() == 'N':
        web_input_manager.set_input('confirmation', usr_request)
    elif usr_request.upper() == 'STOP':
        session_id = Global_Session.store_session()
        while web_app_instance.ufo_running:
            web_input_manager.set_input('confirmation', "N")
            time.sleep(1)
        return jsonify({"response": f"Session saved. Please enter your new request, or retrieve the saved session with 'Retrieve Session: {session_id}'"}), 200
    elif 'RETRIEVE SESSION' in usr_request.upper():
        parts = usr_request.split(': ')
        session_id = parts[1]
        Global_Session.load_session(session_id)
    else:
        web_input_manager.set_input('usr_request', usr_request)
    
    while True:
        if plan_signal.is_set():
            plan_ret = plan_first_return
            plan_first_return = []
            web_app_instance.status = 'CONFIRMATION'
            return jsonify(plan_ret), 200
        if terminate_signal.is_set() and usr_confirmation:
            terminate_signal.clear()
            global comment_to_return
            comment_ret = comment_to_return
            comment_to_return = None
            final_ret_str = f"{comment_ret}\nPlease enter your new request. Enter 'N' for exit."
            return jsonify({"response": final_ret_str}), 200


@app.route('/ufo/save_session', methods=['POST'])
def save_session():
    session_id = Global_Session.store_session()
    return jsonify({"response": f"Session saved with id {session_id}"}), 200


@app.route('/ufo/retrieve_session', methods=['POST'])
def retrieve_session():
    session_id = request.json.get('session_id')
    Global_Session.load_session(session_id)
    return jsonify({"response": "Session loaded"}), 200


@app.route('/ufo/get_status', methods=['GET'])
def get_status():
    return jsonify(web_app_instance.status), 200


@app.route('/ufo/get_session_state', methods=['GET'])
def get_session_state():
    if not web_app_instance.ufo_running:
        return jsonify({"response": "UFO not running"}), 200
    state = Global_Session.get_state()
    return jsonify(state), 200


@app.route('/ufo/pause', methods=['GET'])
def pause_ufo():
    if not web_app_instance.ufo_running:
        return jsonify({"response": "UFO not running"}), 200
    response = Global_Session.pause_session()
    if not response:
        return jsonify({"response": "Session paused"}), 200
    return jsonify(response), 200


@app.route('/ufo/resume', methods=['GET'])
def resume_ufo():
    if not web_app_instance.ufo_running:
        return jsonify({"response": "UFO not running"}), 200
    response = Global_Session.resume_session()
    if not response:
        return jsonify({"response": "Session resumed"}), 200
    return jsonify(response), 200


@app.route('/ufo/confirmation', methods=['POST'])
def confirmation():
    if not web_app_instance.ufo_running:
        return jsonify({"response": "UFO not running"}), 200
    usr_request = request.json.get('confirmation')
    web_input_manager.set_input('confirmation', usr_request)

    if plan_signal.is_set():
        web_input_manager.clear_input('confirmation')
        if usr_request == 'Y':
            plan_signal.clear()
            Global_Session.unlock_confirmation()
        else: 
            global usr_confirmation
            usr_confirmation = False
            plan_signal.clear()
            Global_Session.terminate_session()
            if terminate_signal.is_set():
                terminate_signal.clear()
            web_app_instance.status = 'CONFIRMATION or NEW REQUEST'
            return jsonify({"response": "Please enter your new request. Enter 'N' for exit."}), 200
    web_app_instance.status = 'RUNNING'
    return jsonify({"response": "Confirmation received"}), 200


if __name__ == '__main__':
    app.run(debug=True)