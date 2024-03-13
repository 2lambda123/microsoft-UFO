# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import requests
import time
from ..config.config import load_config
from ..utils import print_with_color
from .azure_ad import get_chat_completion
import json


configs = load_config()


def get_request_header():
    """
    Get the header for the request.
    return: The header for the request.
    """
    if configs["API_TYPE"].lower() == "aoai":
        headers = {
            "Content-Type": "application/json",
            "api-key": configs["OPENAI_API_KEY"],
        }
    elif configs["API_TYPE"].lower() == "openai":
        headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer {key}".format(key=configs["OPENAI_API_KEY"]),
            }
    elif configs["API_TYPE"].lower() == "azure_ad":
        headers = {}
    else:
        raise ValueError("API_TYPE should be either 'openai' or 'aoai' or 'azure_ad'.")
    
    return headers


def get_gptv_completion(messages):
    """
    Get GPT-V completion from messages.
    messages: The messages to be sent to GPT-V.
    endpoint: The endpoint of the request.
    max_tokens: The maximum number of tokens to generate.
    temperature: The sampling temperature.
    model: The model to use.
    max_retry: The maximum number of retries.
    return: The response of the request.
    """
    is_aad = configs['API_TYPE'].lower() == 'azure_ad'
    headers = get_request_header()

    if not is_aad:
        payload = {
            "messages": messages,
            "temperature": configs["TEMPERATURE"],
            "max_tokens": configs["MAX_TOKENS"],
            "top_p": configs["TOP_P"],
            "model": configs["OPENAI_API_MODEL"]
        }

    for _ in range(configs["MAX_RETRY"]):
        try:
            if not is_aad :
                response = requests.post(configs["OPENAI_API_BASE"], headers=headers, json=payload)

                response_json = response.json()
                response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
                

                if "choices" not in response_json:
                    print_with_color(f"GPT Error: No Reply", "red")
                    continue

                if "error" not in response_json:
                    usage = response_json.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
            else:
                response = get_chat_completion(
                    engine=configs["OPENAI_API_MODEL"],
                    messages = messages,
                    max_tokens = configs["MAX_TOKENS"],
                    temperature = configs["TEMPERATURE"],
                    top_p = configs["TOP_P"],
                )
                response_json = json.loads(response.model_dump_json())
                
                if "error" not in response_json:
                    usage = response.usage
                    prompt_tokens = usage.prompt_tokens
                    completion_tokens = usage.completion_tokens
                
            cost = prompt_tokens / 1000 * 0.01 + completion_tokens / 1000 * 0.03
             
            return response_json, cost
        except requests.RequestException as e:
            error_code = response_json["error"]["code"]
            # print(error_code)
            if error_code == "429":
                print_with_color(f"Rate Limit Exceeded, sleep 15 seconds and retry", "green")
                time.sleep(15)
                continue
            if error_code == "BadRequest":
                print_with_color(f"Bad Request, please retry", "green")
                break
            print_with_color(f"Error making API request: {e}", "red")
            try:
                print_with_color(response_json, "red")
            except:
                pass
            time.sleep(5)
            continue
