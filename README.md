# Automated Ethical Debate Framework

A Python-based framework for simulating nuanced ethical debates using Large Language Models (LLMs) and predefined, customizable ethical personas. This tool allows researchers and ethicists to explore how different ethical frameworks approach complex dilemmas.

## Overview

This project provides an `orchestrator.py` script that manages a debate between several AI-driven "ethicist" personas. Each persona operates based on a distinct ethical theory (e.g., Deontology, Utilitarianism, Virtue Ethics, etc.), defined in individual YAML configuration files stored in the `personas/` directory.

The simulation proceeds through several stages:
1.  **Case Presentation:** A specific ethical dilemma and a set of options are presented to the personas. These are defined in `options.yaml`.
2.  **Opening Statements:** Each persona provides an initial analysis and proposed solution based on its ethical framework.
3.  **Rebuttals:** Personas critique each other's opening statements.
4.  **Voting & Justification:** Personas vote on one of the predefined options from `options.yaml` and justify their choice.
5.  **Report Generation:** A detailed `debate_report.txt` (human-readable) and a `debate_output.json` (structured data) file are generated.

This framework is designed for:
* Exploring the application of various ethical theories to practical problems.
* Understanding points of convergence and divergence between different ethical viewpoints.
* Conducting methodological experiments on LLM behavior in ethical reasoning tasks.
* Educational purposes in applied ethics.

## "Plug and Play" Nature

The framework is designed to be flexible and easily customizable:

* **Ethical Dilemmas (`options.yaml`):**
    * The `options.yaml` file defines the ethical scenario (the "prompt") and the specific options the personas will debate and vote on.
    * Currently, it contains an example scenario: "covid_ventilator_triage."
    * **To use your own scenario:** Simply edit `options.yaml` to define your desired `case` name, `prompt`, and `options`. The `orchestrator.py` script will automatically use the content of this file.

* **Ethical Personas (`personas/` directory):**
    * The `personas/` directory contains individual `.yaml` files, each defining an ethical persona (e.g., `The_Principled.yaml`, `The_Aggregator.yaml`).
    * You can **modify existing personas** by editing their respective `.yaml` files.
    * You can **add new personas** by creating new `.yaml` files in this directory. The `orchestrator.py` script will automatically load any `.yaml` files found here. Ensure new persona files follow the same structure as the existing ones (including fields like `name`, `principle`, `approach`, etc.).
    * You can **use a subset of personas** by simply removing unwanted persona files from this directory before running the script. The current version includes [mention number, e.g., "four"] example personas.

* **LLM Configuration (`config.yaml`):**
    * The `config.yaml` file is used by `orchestrator.py` to determine which LLM to use (e.g., an OpenAI model).
    * **Important:** This file currently only needs to specify the model name. For example:
        ```yaml
        model: "gpt-4-turbo-preview"
        ```
    * You will need to create this `config.yaml` file in the main project directory yourself if it's not already present, or modify the existing one with your desired model.
    * **Note on `.gitignore`:** For more advanced users or if you plan to add sensitive information to `config.yaml` in the future (which is not the case currently), you would typically add `config.yaml` to a `.gitignore` file to prevent it from being tracked by Git. However, for simplicity with the current setup (where it only contains the model name), we are not using a `.gitignore` file in this basic version. Just be mindful not to add API keys or other secrets directly into this file if you modify its purpose later without also adding it to a `.gitignore`.

## Project Structure
