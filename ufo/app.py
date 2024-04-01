from flask import Flask, request, jsonify
import subprocess
import shlex, os, time, threading, sys
app = Flask(__name__)
usr_confirmation_signal = threading.Event()
ufo_termination_signal = threading.Event()
UFO_PATH = r"C:\Users\v-liuhengyu\OneDrive - Microsoft\Desktop\UFO"
terminate_signal = threading.Event()
class Web_app():

    def __init__(self) -> None:
        self.output_thread = None
        self.process = None
        self.plan_signal = threading.Event()

    def ufo_start(self, task_name):
        os.chdir(UFO_PATH)
        cmd = f"python -m ufo --task {task_name}"
        try:
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            # process = subprocess.run(cmd, shell=True, env=env, text=True, encoding='utf-8')
            self.process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, encoding='utf-8')
            self.output_thread = threading.Thread(target=self.display_output, args=(self.process,))
            self.output_thread.start()
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "An error occurred while executing the task"}), 500

        # self.post_proxy = post_proxy
        # old_stdout = sys.stdout
        # sys.stdout = StdoutWrapper(old_stdout, self.ufo_terminate)
        # self.simulate_args(task_name)
        # try:
            
        #     with self.working_directory(r"C:\Users\v-liuhengyu\OneDrive - Microsoft\Desktop\UFO"):
        #         from ufo.ufo import main as ufo_main
        #         ufo_main("taskweaver")  # Execution of UFO, with output captured and processed by custom_buffer
            
        #         self.ufo_terminate.set()
        #         print("UFO has been started successfully.")
        # finally:
        #     sys.stdout = old_stdout  # Restore original stdout

    def process_input(self, usr_request):
        self.process.stdin.write(usr_request)
        self.process.stdin.flush()
        self.process.stdin.close()
        print("Request sent")
        terminate_signal.wait()
        terminate_signal.clear()
        # usr_confirmation_signal.wait()
        # usr_confirmation_signal.clear()
        
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
                    self.plan_signal.set()  # Signal
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
    task_name = request.json.get('task', 'web_app')
    usr_request = request.json.get('request', 'No Request, end UFO')
    if confirmation != "Y":
        web_app_instance.ufo_start(task_name)
        web_app_instance.process_input(usr_request)
    
# else:

@app.route('/ufo/confirmation', methods=['POST'])
def ufo_confirmation_wrapper():
    confirmation = request.json.get('confirmation', 'No Confirmation')
    if confirmation == 'Y':
        usr_confirmation_signal.set()
        print("set the lock")
        # terminate_signal.wait()
        return jsonify({"message": "Confirmation received"}), 200
    else:
        return jsonify({"error": "Invalid confirmation"}), 400

if __name__ == '__main__':
    app.run(debug=True)
