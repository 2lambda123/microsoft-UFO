<h1 align="center">
    <b>UFO</b> <img src="./assets/ufo_blue.png" alt="UFO Image" width="40">: A <b>U</b>I-<b>F</b>ocused Agent for Windows <b>O</b>S Interaction
</h1>


<div align="center">

[![arxiv](https://img.shields.io/badge/Paper-arXiv:202402.07939-b31b1b.svg)](https://arxiv.org/abs/2402.07939)&ensp;
![Python Version](https://img.shields.io/badge/Python-3776AB?&logo=python&logoColor=white-blue&label=3.10%20%7C%203.11)&ensp;
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)&ensp;
![Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)&ensp;
[![X (formerly Twitter) Follow](https://img.shields.io/twitter/follow/UFO_Agent)](https://twitter.com/intent/follow?screen_name=UFO_Agent)

</div>

**UFO** is a **UI-Focused** dual-agent framework to fulfill user requests on **Windows OS** by seamlessly navigating and operating within individual or spanning multiple applications.

<h1 align="center">
    <img src="./assets/overview_n.png"/> 
</h1>


## 🕌 Framework
<b>UFO</b> <img src="./assets/ufo_blue.png" alt="UFO Image" width="24"> operates as a dual-agent framework, encompassing:
- <b>AppAgent 🤖</b>, tasked with choosing an application for fulfilling user requests. This agent may also switch to a different application when a request spans multiple applications, and the task is partially completed in the preceding application. 
- <b>ActAgent 👾</b>, responsible for iteratively executing actions on the selected applications until the task is successfully concluded within a specific application. 
- <b>Control Interaction 🎮</b>, is tasked with translating actions from AppAgent and ActAgent into interactions with the application and its UI controls. It's essential that the targeted controls are compatible with the Windows **UI Automation** API.

Both agents leverage the multi-modal capabilities of GPT-Vision to comprehend the application UI and fulfill the user's request. For more details, please consult our [technical report](https://arxiv.org/abs/2402.07939).
<h1 align="center">
    <img src="./assets/framework.png"/> 
</h1>


## 📢 News
- 📅 2024-03-XX: New Release for v0.0.1! Check out our exciting new features:
    1. Our UFO framework now support RAG from offline document and online Bing search. 
    2. We now support creating your help documents for each Windows app to become an app expert. Check XX for more details!
    3. UFO now support more LLMs and customized models.
- 📅 2024-02-14: Our [technical report](https://arxiv.org/abs/2402.07939) is online!
- 📅 2024-02-10: UFO is released on GitHub🎈. Happy Chinese New year🐉!



## 💥 Highlights

- [x] **First Windows Agent** - UFO is the pioneering agent framework capable of translating user requests in natural language into actionable operations on Windows OS.
- [x] **RAG Enhanced** - UFO is enhanced by Retrieval Augmented Generation (RAG) from heterogeneous sources to promote its ability, including offling help documents and online search engine.
- [x] **Interactive Mode** - UFO facilitates multiple sub-requests from users within the same session, enabling the completion of complex tasks seamlessly.
- [x] **Action Safeguard** - UFO incorporates safeguards to prompt user confirmation for sensitive actions, enhancing security and preventing inadvertent operations.
- [x] **Easy Extension** - UFO offers extensibility, allowing for the integration of additional functionalities and control types to tackle diverse and intricate tasks with ease.


## ✨ Getting Started


### 🛠️ Step 1: Installation
UFO requires **Python >= 3.10** running on **Windows OS >= 10**. It can be installed by running the following command:
```bash
# [optional to create conda environment]
# conda create -n ufo python=3.10
# conda activate ufo

# clone the repository
git clone https://github.com/microsoft/UFO.git
cd UFO
# install the requirements
pip install -r requirements.txt
```

### ⚙️ Step 2: Configure the LLMs
Before running UFO, you need to provide your LLM configurations. You can configure create a config file `ufo/config/config.yaml` by copying the `ufo/config/config.yaml.template` edited as follows. 

#### OpenAI
```
API_TYPE: "openai" 
OPENAI_API_BASE: "https://api.openai.com/v1/chat/completions" # The base URL for the OpenAI API
OPENAI_API_KEY: "YOUR_API_KEY"  # Set the value to the openai key for the llm model
OPENAI_API_MODEL: "GPTV_MODEL_NAME"  # The only OpenAI model by now that accepts visual input
```

#### Azure OpenAI (AOAI)
```
API_TYPE: "aoai" 
OPENAI_API_BASE: "YOUR_ENDPOINT" # The AOAI API address. Format: https://{your-resource-name}.openai.azure.com/openai/deployments/{deployment-id}/chat/completions?api-version={api-version}
OPENAI_API_KEY: "YOUR_API_KEY"  # Set the value to the openai key for the llm model
OPENAI_API_MODEL: "GPTV_MODEL_NAME"  # The only OpenAI model by now that accepts visual input
```


### 🎉 Step 3: Start UFO

#### ⌨️ You can execute the following on your Windows command Line (CLI):

```bash
# assume you are in the cloned UFO folder
python -m ufo --task <your_task_name>
```

This will start the UFO process and you can interact with it through the command line interface. 
If everything goes well, you will see the following message:

```bash
Welcome to use UFO🛸, A UI-focused Agent for Windows OS Interaction. 
 _   _  _____   ___
| | | ||  ___| / _ \
| | | || |_   | | | |
| |_| ||  _|  | |_| |
 \___/ |_|     \___/
Please enter your request to be completed🛸:
```
#### ⚠️Reminder:  ####
- Before UFO executing your request, please make sure the targeted applications are active on the system.
- The GPT-V accepts screenshots of your desktop and application GUI as input. Please ensure that no sensitive or confidential information is visible or captured during the execution process. For further information, refer to [DISCLAIMER.md](./DISCLAIMER.md).


###  Step 4 🎥: Execution Logs 

You can find the screenshots taken and request & response logs in the following folder:
```
./ufo/logs/<your_task_name>/
```
You may use them to debug, replay, or analyze the agent output.


## ❓Get help 
* ❔GitHub Issues (prefered)
* For other communications, please contact ufo-agent@microsoft.com
---

## 🎬 Demo Examples

We present two demo videos that complete user request on Windows OS using UFO. For more case study, please consult our [technical report](https://arxiv.org/abs/2402.07939).

#### 1️⃣🗑️ Example 1: Deleting all notes on a PowerPoint presentation.
In this example, we will demonstrate how to efficiently use UFO to delete all notes on a PowerPoint presentation with just a few simple steps. Explore this functionality to enhance your productivity and work smarter, not harder!


https://github.com/microsoft/UFO/assets/11352048/cf60c643-04f7-4180-9a55-5fb240627834



#### 2️⃣📧 Example 2: Composing an email using text from multiple sources.
In this example, we will demonstrate how to utilize UFO to extract text from Word documents, describe an image, compose an email, and send it seamlessly. Enjoy the versatility and efficiency of cross-application experiences with UFO!


https://github.com/microsoft/UFO/assets/11352048/aa41ad47-fae7-4334-8e0b-ba71c4fc32e0




## 📊 Evaluation

Please consult the [WindowsBench](https://arxiv.org/pdf/2402.07939.pdf) provided in Section A of the Appendix within our technical report. Here are some tips (and requirements) to aid in completing your request:

- Prior to UFO execution of your request, ensure that the targeted application is active (though it may be minimized).
- Occasionally, requests to GPT-V may trigger content safety measures. UFO will attempt to retry regardless, but adjusting the size or scale of the application window may prove helpful. We are actively solving this issue.
- Currently, UFO supports a limited set of applications and UI controls that are compatible with the Windows **UI Automation** API. Our future plans include extending support to the Win32 API to enhance its capabilities.
- Please note that the output of GPT-V may not consistently align with the same request. If unsuccessful with your initial attempt, consider trying again.



## 📚 Citation
Our technical report paper can be found [here](https://arxiv.org/abs/2402.07939). 
If you use UFO in your research, please cite our paper:
```
@article{ufo,
  title={{UFO: A UI-Focused Agent for Windows OS Interaction}},
  author={Zhang, Chaoyun and Li, Liqun and He, Shilin and  Zhang, Xu and Qiao, Bo and  Qin, Si and Ma, Minghua and Kang, Yu and Lin, Qingwei and Rajmohan, Saravan and Zhang, Dongmei and  Zhang, Qi},
  journal={arXiv preprint arXiv:2402.07939},
  year={2024}
}
```

## 📝 Todo List
- ⏩ Documentation.
- ⏩ Support local host GUI interaction model.
- ⏩ Support more control using Win32 API.
- ⏩ RAG enhanced UFO.
- ⏩ Chatbox GUI for UFO.



## 🎨 Related Project
You may also find [TaskWeaver](https://github.com/microsoft/TaskWeaver?tab=readme-ov-file) useful, a code-first LLM agent framework for seamlessly planning and executing data analytics tasks.


## ⚠️ Disclaimer
By choosing to run the provided code, you acknowledge and agree to the following terms and conditions regarding the functionality and data handling practices in [DISCLAIMER.md](./DISCLAIMER.md)


## <img src="./assets/ufo_blue.png" alt="logo" width="30"> Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
