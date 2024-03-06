# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import requests
import time
from ..config.config import load_config
from ..utils import print_with_color
from .azure_ad import get_chat_completion


configs = load_config()


def get_gptv_completion(messages, headers):
    """
    Get GPT-V completion from messages.
    messages: The messages to be sent to GPT-V.
    headers: The headers of the request.
    endpoint: The endpoint of the request.
    max_tokens: The maximum number of tokens to generate.
    temperature: The sampling temperature.
    model: The model to use.
    max_retry: The maximum number of retries.
    return: The response of the request.
    """
    aad = configs['API_TYPE'].lower() == 'azure_ad'
    if not aad:
        payload = {
            "messages": messages,
            "temperature": configs["TEMPERATURE"],
            "max_tokens": configs["MAX_TOKENS"],
            "top_p": configs["TOP_P"],
            "model": configs["OPENAI_API_MODEL"]
        }

    for _ in range(configs["MAX_RETRY"]):
        try:
            if not aad :
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
                
                if "error" not in response:
                    usage = response.usage
                    prompt_tokens = usage.prompt_tokens
                    completion_tokens = usage.completion_tokens
                response_json = response

            cost = prompt_tokens / 1000 * 0.01 + completion_tokens / 1000 * 0.03
             
            return response_json, cost
        except requests.RequestException as e:
            print_with_color(f"Error making API request: {e}", "red")
            print_with_color(str(response_json), "red")
            try:
                print_with_color(response.json(), "red")
            except:
                _ 
            time.sleep(3)
            continue
