# OllamaAlpha_Evolve: Regenerating Autonomous Algorithmic Discovery 🚀 on your OWN SERVER via OLLAMA

![OllamaAlpha_Evolve_workflow](https://github.com/user-attachments/assets/9d4709ad-0072-44ae-bbb5-7eea1c5fa08c)

OllamaAlpha_Evolve is freeing you from API constraints by running Alpha_Evolve on your own local AI at no cost.
It is a fork of OpenAlpha_Evolve which is an open-source Python framework inspired by the groundbreaking research on autonomous coding agents like DeepMind's AlphaEvolve. It's a **regeneration** of the core idea: an intelligent system that iteratively writes, tests, and improves code using Large Language Models (LLMs) like Google's Gemini, guided by the principles of evolution.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

---

## ✨ The Vision: AI-Driven Algorithmic Innovation running on your private server

Imagine an agent that can power this by your own ollama instance:

*   Understand a complex problem description.
*   Generate initial algorithmic solutions.
*   Rigorously test its own code.
*   Learn from failures and successes.
*   Evolve increasingly sophisticated and efficient algorithms over time.

OllamaAlpha_Evolve is a step towards this vision. It's not just about generating code; it's about creating a system that *discovers* and *refines* solutions autonomously.

---

## 🧠 How It Works: The Evolutionary Cycle

OllamaAlpha_Evolve employs a modular, agent-based architecture to orchestrate an evolutionary process:

1.  **Task Definition**: You, the user, define the algorithmic "quest" – the problem to be solved, including examples of inputs and expected outputs.
2.  **Prompt Engineering (`PromptDesignerAgent`)**: This agent crafts intelligent prompts for the LLM. It designs:
    *   *Initial Prompts*: To generate the first set of candidate solutions.
    *   *Mutation Prompts*: To introduce variations and improvements to existing solutions, often requesting changes in a "diff" format.
    *   *Bug-Fix Prompts*: To guide the LLM in correcting errors from previous attempts, also typically expecting a "diff".
3.  **Code Generation (`CodeGeneratorAgent`)**: Powered by an LLM (currently configured for OLLAMA), this agent takes the prompts and generates Python code. If a "diff" is requested and received, it attempts to apply the changes to the parent code.
4.  **Evaluation (`EvaluatorAgent`)**: The generated code is put to the test!
    *   *Syntax Check*: Is the code valid Python?
    *   *Execution*: The code is run in a temporary, isolated environment against the input/output examples defined in the task.
    *   *Fitness Scoring*: Programs are scored based on correctness (how many test cases pass), efficiency (runtime), and other potential metrics.
5.  **Database (`DatabaseAgent`)**: All programs (code, fitness scores, generation, lineage) are stored, creating a record of the evolutionary history (currently in-memory).
6.  **Selection (`SelectionControllerAgent`)**: The "survival of the fittest" principle in action. This agent selects:
    *   *Parents*: Promising programs from the current generation to produce offspring.
    *   *Survivors*: The best programs from both the current population and new offspring to advance to the next generation.
7.  **Iteration**: This cycle repeats for a defined number of generations, with each new generation aiming to produce better solutions than the last.
8.  **Orchestration (`TaskManagerAgent`)**: The maestro of the operation, coordinating all other agents and managing the overall evolutionary loop.

---

## 🚀 Key Features

*   **LLM-Powered Code Generation**: Leverages state-of-the-art Large Language Models (Google Gemini integration included).
*   **Evolutionary Algorithm Core**: Implements iterative improvement through selection, LLM-driven mutation/bug-fixing (via diffs), and survival.
*   **Modular Agent Architecture**: Easily extend or replace individual components (e.g., use a different LLM, database, or evaluation strategy).
*   **Automated Program Evaluation**: Syntax checking and functional testing against user-provided examples with timeout mechanisms.
*   **Configuration Management**: Easily tweak parameters like population size, number of generations, LLM models, and API settings via `config/settings.py`.
*   **Detailed Logging**: Comprehensive logs provide insights into each step of the evolutionary process.
*   **Diff-based Mutations**: The system is designed to use diffs for mutations and bug fixes, allowing for more targeted code modifications by the LLM.
*   **Open Source & Extensible**: Built with Python, designed for experimentation and community contributions.

---

## 📂 Project Structure

```
./
├── agents/                  # Core intelligent agents (subdirectories for each)
│   ├── code_generator/
│   ├── database_agent/
│   ├── evaluator_agent/
│   ├── prompt_designer/
│   ├── selection_controller/
│   ├── task_manager/
│   ├── rl_finetuner/      # Placeholder for Reinforcement Learning Fine-Tuner
│   └── monitoring_agent/  # Placeholder for Monitoring Agent
├── config/                  # Configuration files (settings.py)
├── core/                    # Core interfaces, data models (Program, TaskDefinition)
├── utils/                   # Utility functions (if any, currently minimal)
├── tests/                   # Unit and integration tests (placeholders, to be expanded)
├── scripts/                 # Helper scripts (e.g., diagram generation)
├── main.py                  # Main entry point to run the system
├── requirements.txt         # Project dependencies
├── .gitignore               # Specifies intentionally untracked files that Git should ignore
├── LICENSE.md               # Project's license information (MIT License)
└── README.md                # This file!
```

---

## 🏁 Getting Started

1.  **Prerequisites**:
    *   Python 3.10+
    *   `pip` for package management
    *   `git` for cloning

2.  **Clone the Repository**:
    ```bash
    git clone https://github.com/xceleratio/OllamaAlpha_Evolve.git
    cd OllamaAlpha_Evolve
    ```

3.  **Set Up a Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure your OLLAMA in the settings / in case you have anything non standard:**:
    *   Open `config/settings.py`. Here you can:
        *   Change the default LLM models used for generation (`PRO_MODEL_NAME`) and evaluation (`EVALUATION_MODEL`).
        *   Adjust evolutionary parameters like `POPULATION_SIZE` and `GENERATIONS`.
        *   Modify your OLLAMA HOST API  settings

7.  **Run OllamaAlpha_Evolve!**
    The `main.py` file is configured with an example task (Dijkstra's algorithm). To run it:
    ```bash
    python -m main
    ```
    Watch the logs in your terminal to see the evolutionary process unfold! Log files are also saved to `alpha_evolve.log` (by default).

---

## 💡 Defining Your Own Algorithmic Quests!

Want to challenge OllamaAlpha_Evolve with a new problem? It's easy:

1.  **Open `main.py`**.
2.  **Modify the `TaskDefinition` object**:
    *   `id`: A unique string identifier for your task (e.g., "sort_list_task").
    *   `description`: A clear, detailed natural language description of the problem. This is crucial for the LLM to understand what to do. Be specific about function names, expected behavior, and constraints.
    *   `function_name_to_evolve`: The name of the Python function the agent should try to create/evolve (e.g., "custom_sort").
    *   `input_output_examples`: A list of dictionaries, each containing an `input` (arguments for your function) and the corresponding expected `output`. These are vital for evaluation.
        *   Inputs should be provided as a list if the function takes multiple positional arguments, or as a single value if it takes one.
        *   Use `float('inf')` or `float('-inf')` directly in your Python code defining these examples if needed by your problem (the evaluation harness handles JSON serialization/deserialization of these).
    *   `allowed_imports`: Specify a list of Python standard libraries that the generated code is allowed to import (e.g., `["heapq", "math", "sys"]`). This helps guide the LLM and can be important for the execution sandbox.
    *   (Optional) `evaluation_criteria`: Define how success is measured (currently primarily driven by correctness based on test cases).
    *   (Optional) `initial_code_prompt`: Override the default initial prompt if you need more specific instructions for the first code generation attempt.

3.  **Run the agent** as before: `python -m main`.

The quality of your `description` and the comprehensiveness of your `input_output_examples` significantly impact the agent's success!

---

## 🔮 The Horizon: Future Evolution

OllamaAlpha_Evolve is a living project. Here are some directions we're excited to explore (and invite contributions for!):

*   **Advanced Evaluation Sandboxing**: Implementing more robust, secure sandboxing (e.g., using Docker or `nsjail`) for code execution to handle potentially unsafe code and complex dependencies.
*   **Sophisticated Fitness Metrics**: Beyond correctness and basic runtime, incorporating checks for code complexity (e.g., cyclomatic complexity), style (linting), resource usage (memory), and custom domain-specific metrics.
*   **Reinforcement Learning for Prompt Strategy**: Implementing the `RLFineTunerAgent` to dynamically optimize prompt engineering strategies based on performance feedback.
*   **Enhanced Monitoring & Visualization**: Developing tools (via `MonitoringAgent`) to visualize the evolutionary process, track fitness landscapes, and understand agent behavior (e.g., using a simple web dashboard or plots).
*   **Broader LLM Support**: Adding easy integrations for other powerful LLMs (e.g., OpenAI models, Anthropic Claude).
*   **Self-Correction & Reflection**: Enabling the agent to analyze its own failures more deeply (e.g., analyze error messages, identify patterns in failed tests) and refine its problem-solving approach.
*   **Diverse Task Domains**: Applying OllamaAlpha_Evolve to a wider range of problems in science, engineering, data analysis, and creative coding.
*   **Community-Driven Task Library**: Building a collection of interesting and challenging tasks contributed by the community.
*   **Improved Diff Application**: Making the diff application more robust or exploring alternative ways for the LLM to suggest modifications.
*   **Crossover Implementation**: Adding a genetic crossover mechanism as an alternative or supplement to LLM-driven mutation.

---
## ALL MAIN INFO IS THE SAME AS THE ORIGINAL PROJECT OPENALPHA_EVOLVE , it just gives you more freedom on OLLAMA, than beeing forced on gemini.

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE.md` file for details.

---

## 🙏 Homage

OllamaAlpha_Evolve is proudly inspired by the pioneering work of the Google DeepMind team on AlphaEvolve and other related research in LLM-driven code generation and automated discovery. This project aims to make the core concepts more accessible for broader experimentation and learning. We stand on the shoulders of giants.

---

*Disclaimer: This is an experimental project. Generated code may not always be optimal, correct, or secure. Always review and test code thoroughly, especially before using it in production environments.* 
