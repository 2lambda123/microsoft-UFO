from flask import Flask, request, jsonify
import subprocess
import shlex, os, time, threading, sys, re

app = Flask(__name__)
usr_confirmation_signal = threading.Event()
UFO_PATH = r"C:\Users\v-liuhengyu\OneDrive - Microsoft\Desktop\UFO"
terminate_signal = threading.Event()
plan_signal = threading.Event()
global plan_first_return
plan_first_return = []
global comment_to_return
comment_to_return = None

class StdoutWrapper:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.accumulated_output = ""
        self.terminate_signal = terminate_signal
        self.security_check_flag = False
        self.finished = False
        self.plans = []
        self.current_plan = None
        self.output_plan = False
        self.final_comment = None

    def write(self, s):
        self.accumulated_output += s
        if "\n" in self.accumulated_output:  # 假设输出是按行分隔的
            lines = self.accumulated_output.split("\n")
            for line in lines[:-1]:  # 处理除最后一行外的所有完整行
                self.process_line(line)
            self.accumulated_output = lines[-1]  # 将未完成的行留在缓冲区中

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
            terminate_signal.set()
            self.finished = True  # 标记为完成
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
    
class Web_app():

    def __init__(self) -> None:
        self.output_thread = None
        self.process = None

    def simulate_args(self, task: str):
        sys.argv = ['ufo.py', '--task', task]
        print(sys.argv)

    def ufo_start(self, task_name, usr_request):
        old_stdout = sys.stdout
        sys.stdout = StdoutWrapper(old_stdout)
        self.simulate_args(task_name)
        try:
            from .ufo import main as ufo_main
            ufo_main(arg = "web", signal = usr_confirmation_signal)  # Execution of UFO, with output captured and processed by custom_buffer
        except Exception as e:
            print(e)
    def process_input(self, usr_request):
        # print("Processing input")
        from.ufo import InputIntegrater
        input_manager = InputIntegrater()
        input_manager.process_web_input(usr_request)
        
    def display_output(self, process):
        accumulated_output = ''
        finished = False
        for line in iter(process.stdout.readline, ''):
            print(line)
            if "Observations" in line or "Selected item" in line or "Thoughts" in line:
                continue
            if 'FINISH' in line:
                accumulated_output = ''
                finished = True
            if 'Next Plan' in line:
                accumulated_output = ''
            if not finished:
                if 'Comment' in line:
                    plan_signal.set()  # Signal
                    print(accumulated_output)
                    accumulated_output = ''
                accumulated_output += line
            else:
                accumulated_output += line
                if 'Comment' in line:
                    print(accumulated_output)
                    accumulated_output = ''
            if "Please enter your new request. Enter 'N' for exit." in line or "Request total cost is" in line or "[Input Required:]" in line:
                terminate_signal.set() 
                accumulated_output = ''



web_app_instance = Web_app()

# Define a wrapper function for your route that calls your instance 
@app.route('/ufo', methods=['POST'])
def ufo_command_wrapper():
    confirmation = request.json.get('confirmation', 'No Confirmation')
    task_name = request.json.get('task', 'web')
    usr_request = request.json.get('request', 'No Request, end UFO')
    if confirmation != "Y":
        main_thread = threading.Thread(target=web_app_instance.ufo_start, args=(task_name, usr_request))
        input_thread = threading.Thread(target=web_app_instance.process_input, args=(usr_request,))
        main_thread.start()
        time.sleep(5)
        input_thread.start()
        plan_signal.wait()
        plan_signal.clear()
    return jsonify(plan_first_return), 200
# else:

@app.route('/ufo/confirmation', methods=['POST'])
def ufo_confirmation_wrapper():
    confirmation = request.json.get('confirmation', 'No Confirmation')
    if confirmation == 'Y':
        usr_confirmation_signal.set()
        terminate_signal.wait()
        return jsonify({"response": comment_to_return}), 200
    else:
        return jsonify({"error": "Invalid confirmation"}), 400

if __name__ == '__main__':
    app.run(debug=True)
