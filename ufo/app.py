from flask import Flask, request, jsonify
import time, threading, sys, re

# run this flask server under UFO folder: python -m ufo.app

app = Flask(__name__)

UFO_PATH = r"C:\Users\v-liuhengyu\OneDrive - Microsoft\Desktop\UFO"
terminate_signal = threading.Event()
plan_signal = threading.Event()
terminate_old_ufo = threading.Event()   
global_input_manager = None
ufo_running = False 

global plan_first_return
plan_first_return = []
global comment_to_return
comment_to_return = None


class Web_app():

    def __init__(self) -> None:
        self.ufo_running = False
        from ufo.ufo import InputIntegrater
        self.input_manager = InputIntegrater()
        self.main_thread = None
        self.input_thread = None

    def simulate_args(self, task: str):
        sys.argv = ['ufo.py', '--task', task]
        print(sys.argv)

    def ufo_start(self, task_name, usr_request):
        old_stdout = sys.stdout
        sys.stdout = StdoutWrapper(old_stdout)
        self.simulate_args(task_name)
        try:
            from ufo.ufo import main as ufo_main
            self.ufo_running = True
            ufo_main(arg = "web")  # Execution of UFO, with output captured and processed by custom_buffer
            time.sleep(2)
            print("UFO finished")
            self.ufo_running = False
        finally:
            sys.stdout = old_stdout
            pass

    def process_input(self, usr_request):

        self.input_manager.process_web_input(usr_request)
        return
        


class StdoutWrapper:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.accumulated_output = ""
        self.terminate_signal = terminate_signal
        self.finished = False
        self.plans = []
        self.current_plan = None
        self.output_plan = False
        self.final_comment = None


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
            if not self.output_plan:
                global plan_first_return
                plan_first_return = self.get_cleaned_plans()
                self.output_plan = True
            return  
        if self.current_plan:
            self.current_plan['plan'] += line
        if "Please enter your new request. Enter 'N' for exit." in line or "Request total cost is" in line or "[Input Required:]" in line:
            if terminate_old_ufo.is_set():
                return
            terminate_signal.set()
            self.finished = True 
            global comment_to_return
            comment_to_return = self.clean_ansi_codes(self.final_comment)
            return
    
    def clean_ansi_codes(self, text):
        # print(text)
        ansi_escape = re.compile(r'\x1b\[.*?m')
        return ansi_escape.sub('', text)
    def get_cleaned_plans(self):
        combined_plans = '\n'.join([self.clean_ansi_codes(plan['plan']) for plan in self.plans])
        response_data = {"response": combined_plans}
        return response_data
    def __getattr__(self, attr):
        return getattr(self.original_stdout, attr)
    


web_app_instance = Web_app()
# Define a wrapper function for your route that calls your instance 

@app.route('/ufo', methods=['POST'])
def ufo_command_wrapper():
    global web_app_instance
    if web_app_instance.ufo_running:
        web_app_instance.input_manager.newrequest_listener()
        terminate_old_ufo.set()
        while terminate_old_ufo.is_set():
            pass
        web_app_instance = Web_app()
        # return jsonify({"response": "UFO instance terminated, starting new instance"}), 200

    task_name = request.json.get('task', 'web')
    usr_request = request.json.get('request', 'No Request, end UFO')
    web_app_instance.main_thread = threading.Thread(target=web_app_instance.ufo_start, args=(task_name, usr_request))
    web_app_instance.input_thread = threading.Thread(target=web_app_instance.process_input, args=(usr_request,))
    web_app_instance.main_thread.start()
    time.sleep(5)
    if not terminate_old_ufo.is_set():
        web_app_instance.input_thread.start()
    else:
        pass

    while not terminate_old_ufo.is_set():
        if plan_signal.is_set():
            plan_signal.clear()
            break
    if not terminate_old_ufo.is_set():
        pass
    else:
        terminate_old_ufo.clear()
        web_app_instance.ufo_running = False
        global plan_first_return
        plan_first_return = []
        web_app_instance.main_thread.join()
        if web_app_instance.input_thread.is_alive():
            web_app_instance.input_thread.join()
        terminate_old_ufo.clear()
    return jsonify(plan_first_return), 200


@app.route('/ufo/confirmation', methods=['POST'])
def ufo_confirmation_wrapper():
    confirmation = request.json.get('confirmation', 'No Confirmation')
    if confirmation == 'Y':
        web_app_instance.input_manager.pass_confirmation()
        terminate_signal.wait()
        global plan_first_return
        plan_first_return = []
        global comment_to_return
        comment_to_return = None
        return jsonify({"response": comment_to_return}), 200
    else:
        web_app_instance.input_manager.terminate_ufo()
        web_app_instance.input_manager.pass_confirmation()
        global plan_first_return
        plan_first_return = []
        global comment_to_return
        comment_to_return = None
        return jsonify({"response": "Action canceled, terminating UFO instance"}), 200

if __name__ == '__main__':
    app.run(debug=True)
