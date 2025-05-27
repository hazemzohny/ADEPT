# AI Deliberative Ethics Protocol Toolkit (ADEPT)

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

## Getting Started

### Prerequisites
* Python 3.8+ (or a recent version of Python 3)
* An OpenAI API key (or an API key for the LLM service you intend to use, if you modify the script)

### Installation & Setup

1.  **Download Files:**
    * Click the green "<> Code" button on this GitHub repository page.
    * Select "Download ZIP."
    * Extract the ZIP file to a folder on your computer.

2.  **Install Dependencies:**
    * Open a terminal or command prompt.
    * Navigate to the project folder (where you extracted the files).
    * You'll need to install the `openai` and `pyyaml` Python libraries. If you have `pip` (Python's package installer) installed, you can run:
        ```bash
        pip install openai pyyaml python-dotenv
        ```
    * *(Alternatively, a `requirements.txt` file might be added later for easier installation).*

3.  **Set Up API Key:**
    * The `orchestrator.py` script expects your OpenAI API key to be available as an environment variable named `OPENAI_API_KEY`.
    * The simplest way to do this for a single session is to set it in your terminal before running the script:
        * On Windows (Command Prompt): `set OPENAI_API_KEY=your_actual_api_key_here`
        * On Windows (PowerShell): `$env:OPENAI_API_KEY="your_actual_api_key_here"`
        * On macOS/Linux: `export OPENAI_API_KEY='your_actual_api_key_here'`
    * For a more permanent solution without setting it every time, you can create a file named `.env` (note the dot at the beginning) in the main project directory and add the following line:
        ```
        OPENAI_API_KEY="your_actual_api_key_here"
        ```
        The script uses `python-dotenv` to load this. **Ensure this `.env` file is NEVER uploaded to GitHub or shared.**

4.  **Prepare `config.yaml`:**
    * Make sure you have a `config.yaml` file in the main project directory. It should contain:
        ```yaml
        model: "your_chosen_openai_model_name" # e.g., "gpt-4-turbo-preview" or "gpt-3.5-turbo"
        ```

### Running the Simulation
To run the debate simulation:
1.  Open your terminal or command prompt.
2.  Navigate to the project directory.
3.  Run the orchestrator script:
    ```bash
    python orchestrator.py
    ```
This will generate `debate_report.txt` and `debate_output.json` in the project's root directory.

## Example Output
The `debate_report.txt` file produced by the script contains the full transcript of the ethical debate, including each persona's opening statement, rebuttals, final vote, and justification, along with a summary of the debate outcomes.

## License
This project is licensed under the [MIT License](LICENSE).

## Citation
If you use this framework or its methodology in your research or work, please cite it as follows:

Zohny, H. (2025). *ADEPT - AI Deliberative Ethics Protocol Toolkit*. [Software]. Retrieved from https://github.com/hazemzohny/AutomatedEthicalDebate

**BibTeX:**
```bibtex
@software{Zohny_ADEPT_2025,
  author = {Zohny, Hazem},
  title = {{AI Deliberative Ethics Protocol Toolkit}},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{[https://github.com/hazemzohny/ADEPT](https://github.com/hazemzohny/ADEPT)}}
}
