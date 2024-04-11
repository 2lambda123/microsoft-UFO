### NOTE
The lite version of the prompt is not fully optimized. To achieve better results, it is recommended that users adjust the prompt according to performance!!!
### If you use QWEN as the Agent

1. QWen (Tongyi Qianwen) is a LLM developed by Alibaba. Go to [QWen](https://dashscope.aliyun.com/) and register an account and get the API key. More details can be found [here](https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key?spm=a2c4g.11186623.0.0.7b5749d72j3SYU) (in Chinese).
2. Install the required packages dashscope.
```bash
pip install dashscope
```
3. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "Qwen" ,
    "API_KEY": "YOUR_KEY",  
    "API_MODEL": "YOUR_MODEL"
}
```
NOTE: `API_MODEL` is the model name of QWen LLM API. 
You can find the model name in the [QWen LLM model list](https://help.aliyun.com/zh/dashscope/developer-reference/model-square/?spm=a2c4g.11186623.0.0.35a36ffdt97ljI).

### If you use Ollama as the Agent
1. Go to [Ollama](https://github.com/jmorganca/ollama) and follow the instructions to serve a LLM model on your local environment.
We provide a short example to show how to configure the ollama in the following, which might change if ollama makes updates.

```bash title="install ollama and serve LLMs in local" showLineNumbers
## Install ollama on Linux & WSL2.
curl https://ollama.ai/install.sh | sh
## Run the serving
ollama serve
```
Open another terminal and run:
```bash
ollama run YOUR_MODEL
```

***info***
When serving LLMs via Ollama, it will by default start a server at `http://localhost:11434`, which will later be used as the API base in `config.yaml`.


2. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "Ollama" ,
    "API_BASE": "YOUR_ENDPOINT",   
    "API_MODEL": "YOUR_MODEL"
}
```
NOTE: `API_BASE` is the URL started in the Ollama LLM server and `API_MODEL` is the model name of Ollama LLM, it should be same as the one you served before. In addition, due to model limitations, you can use lite version of prompt to have a taste on UFO which can be configured in `config_dev.yaml`. Attention to the top ***note***.

### If you use your custom model as the Agent
1. Start a server with your model, which will later be used as the API base in `config.yaml`.

2. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "Custom" ,
    "API_BASE": "YOUR_ENDPOINT", 
    "API_KEY": "YOUR_KEY",  
    "API_MODEL": "YOUR_MODEL"
}
```

NOTE: You should create a new Python script `custom_model.py` in the ufo/llm folder like the format of the `placeholder.py`, which needs to inherit `BaseService` as the parent class, as well as the `__init__` and `chat_completion` methods. At the same time, you need to add the dynamic import of your file in the `get_service` method of `BaseService`.


Also, ufo provides the usage of ***LLaVA-1.5*** and ***CogAgent*** as the example.

1.1 Download the essential libs of your custom model.

#### If you use LLaVA-1.5 as the Agent

Please refer to the [LLaVA](https://github.com/haotian-liu/LLaVA) project to download and prepare the LLaVA-1.5 model, for example:

```bash
git clone https://github.com/haotian-liu/LLaVA.git
cd LLaVA
conda create -n llava python=3.10 -y
conda activate llava
pip install --upgrade pip  # enable PEP 660 support
pip install -e .
```

#### If you use CogAgent as the Agent

Please refer to the [CogVLM](https://github.com/THUDM/CogVLM) project to download and prepare the CogAgent model. Download the sat version of the CogAgent weights `cogagent-chat.zip` from [here](https://huggingface.co/THUDM/CogAgent/tree/main), unzip it.

1.2 Start your custom model. You must customize your model to support the interface of the UFO.
For simplicity, you have to configure `YOUR_ENDPOINT/chat/completions`.

#### If you use LLaVA as the Agent
Add the `direct_generate_llava` method and a new post interface `/chat/completions` from the `custom_model_worker.py` to the into the `llava/serve/model_worker.py` And start it with the following command:
```bash
python -m llava.serve.llava_model_worker --host YOUR_HOST --port YOUR_POINT --worker YOUR_ENDPOINT --model-path liuhaotian/llava-v1.5-13b --no-register
```

#### If you use CogAgent as the Agent
You can modify the model generate from the `basic_demo/cli_demo.py` with a new post interface `/chat/completions` to enjoy it with UFO.

3. Add following configuration to `config.yaml`:
```json showLineNumbers
{
    "API_TYPE": "Custom" ,
    "API_BASE": "YOUR_ENDPOINT",   
    "API_MODEL": "YOUR_MODEL"
}
```

***Note***: Only LLaVA and CogAgent are supported as open source models for now. If you want to use your own model, remember to modify the dynamic import of your model file in the `get_service` method of `BaseService` in `ufo/llm/base.py`.