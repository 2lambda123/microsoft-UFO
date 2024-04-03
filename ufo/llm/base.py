# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import abc

class BaseService(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def chat_completion(self, *args, **kwargs):
        pass

    def get_cost_estimator(self, api_type, model, prices, prompt_tokens, completion_tokens) -> float:
        """
        Calculates the cost estimate for using a specific model based on the number of prompt tokens and completion tokens.

        Args:
            model (str): The name of the model.
            prices (dict): A dictionary containing the prices for different models.
            prompt_tokens (int): The number of prompt tokens used.
            completion_tokens (int): The number of completion tokens used.

        Returns:
            float: The estimated cost for using the model.
        """
        if api_type.lower() == "openai":
            name = str(api_type+'/'+model)
        elif api_type.lower() in ["aoai", "azure_ad"]:
            name = str('azure/'+model)
        elif api_type.lower() == "qwen":
            name = str('qwen/'+model)

        if name in prices:
            cost = prompt_tokens * prices[name]["input"]/1000 + completion_tokens * prices[name]["output"]/1000
        else:
            print(f"{name} not found in prices")
            return None
        return cost
