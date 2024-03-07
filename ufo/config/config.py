# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os
import yaml


def load_config(config_path="ufo/config/config.yaml"):
    """
    Load the configuration from a YAML file and environment variables.

    :param config_path: The path to the YAML config file. Defaults to "./config.yaml".
    :return: Merged configuration from environment variables and YAML file.
    """
    # Copy environment variables to avoid modifying them directly
    configs = dict(os.environ)

    try:
        with open(config_path, "r") as file:
            yaml_data = yaml.safe_load(file)
        # Update configs with YAML data
        if yaml_data:
            configs.update(yaml_data)
    except FileNotFoundError:
        print(
            f"Warning: Config file not found at {config_path}. Using only environment variables.")

    # Update the API base URL for AOAI
    if configs["API_TYPE"].lower() == "aoai":
        configs["OPENAI_API_BASE"] = "{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}".format(
            endpoint=configs["OPENAI_API_BASE"][:-1] if configs["OPENAI_API_BASE"].endswith(
                "/") else configs["OPENAI_API_BASE"],
            deployment_name=configs["AOAI_DEPLOYMENT"],
            api_version="2024-02-15-preview"
        )

    return configs
