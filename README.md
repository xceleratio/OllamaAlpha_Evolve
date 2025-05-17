# OpenAplha_Evolve: Regenerating Autonomous Algorithmic Discovery 🚀

**Unlock the power of Large Language Models and Evolutionary Computation to tackle complex algorithmic challenges!**

OpenAplha_Evolve is an open-source Python framework inspired by the groundbreaking research on autonomous coding agents like DeepMind's AlphaEvolve. It's a **regeneration** of the core idea: an intelligent system that iteratively writes, tests, and improves code using Large Language Models (LLMs) like Google's Gemini, guided by the principles of evolution.
![image](https://github.com/user-attachments/assets/f988bb2f-3a9b-454f-ac13-b25f6087c6b5)


Our mission is to provide an accessible, understandable, and extensible platform for researchers, developers, and enthusiasts to explore the fascinating intersection of AI, code generation, and automated problem-solving.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ The Vision: AI-Driven Algorithmic Innovation

Imagine an agent that can:

*   Understand a complex problem description.
*   Generate initial algorithmic solutions.
*   Rigorously test its own code.
*   Learn from failures and successes.
*   Evolve increasingly sophisticated and efficient algorithms over time.

OpenAplha_Evolve is a step towards this vision. It's not just about generating code; it's about creating a system that *discovers* and *refines* solutions autonomously.

---

## 🧠 How It Works: The Evolutionary Cycle

OpenAplha_Evolve employs a modular, agent-based architecture to orchestrate an evolutionary process:

1.  **Task Definition**: You, the user, define the algorithmic "quest" – the problem to be solved, including examples of inputs and expected outputs.
2.  **Prompt Engineering (`PromptDesignerAgent`)**: This agent crafts intelligent prompts for the LLM. It designs:
    *   *Initial Prompts*: To generate the first set of candidate solutions.
    *   *Mutation Prompts*: To introduce variations and improvements to existing solutions.
    *   *Bug-Fix Prompts*: To guide the LLM in correcting errors from previous attempts.
3.  **Code Generation (`CodeGeneratorAgent`)**: Powered by an LLM (currently configured for Gemini), this agent takes the prompts and generates Python code.
4.  **Evaluation (`EvaluatorAgent`)**: The generated code is put to the test!
    *   *Syntax Check*: Is the code valid Python?
    *   *Execution*: The code is run against the input/output examples defined in the task.
    *   *Fitness Scoring*: Programs are scored based on correctness, efficiency (runtime), and other potential metrics.
5.  **Database (`DatabaseAgent`)**: All programs (code, fitness, generation, lineage) are stored, creating a record of the evolutionary history.
6.  **Selection (`SelectionControllerAgent`)**: The "survival of the fittest" principle in action. This agent selects:
    *   *Parents*: Promising programs from the current generation to produce offspring.
    *   *Survivors*: The best programs from both the current population and new offspring to advance to the next generation.
7.  **Iteration**: This cycle repeats for a defined number of generations, with each new generation aiming to produce better solutions than the last.
8.  **Orchestration (`TaskManagerAgent`)**: The maestro of the operation, coordinating all other agents and managing the overall evolutionary loop.

---

## 🚀 Key Features

*   **LLM-Powered Code Generation**: Leverages state-of-the-art Large Language Models (Google Gemini integration included).
*   **Evolutionary Algorithm Core**: Implements iterative improvement through selection, mutation (via prompting), and survival.
*   **Modular Agent Architecture**: Easily extend or replace individual components (e.g., use a different LLM, database, or evaluation strategy).
*   **Automated Program Evaluation**: Basic syntax checking and functional testing against user-provided examples.
*   **Configuration Management**: Easily tweak parameters like population size, number of generations, and LLM settings.
*   **Detailed Logging**: Comprehensive logs provide insights into each step of the evolutionary process.
*   **Open Source & Extensible**: Built with Python, designed for experimentation and community contributions.

---

## 📂 Project Structure

```
OpenAplha_Evolve/
├── agents/                  # Core intelligent agents
│   ├── code_generator/
│   ├── database_agent/
│   ├── evaluator_agent/
│   ├── prompt_designer/
│   ├── selection_controller/
│   └── task_manager/
│   └── ... (rl_finetuner, monitoring_agent - placeholders)
├── config/                  # Configuration files (settings.py)
├── core/                    # Core interfaces, data models (Program, TaskDefinition)
├── utils/                   # Utility functions
├── tests/                   # Unit and integration tests (to be expanded)
├── scripts/                 # Helper scripts
├── main.py                  # Main entry point to run the system
├── requirements.txt         # Project dependencies
├── .env.example             # Example for environment variables (copy to .env)
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
    git clone https://github.com/shyamsaktawat/OpenAplha_Evolve.git # MODIFIED URL
    cd OpenAplha_Evolve # MODIFIED directory name
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

5.  **Set Up Environment Variables**:
    *   Copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit `.env` and add your `GEMINI_API_KEY`:
        ```
        GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        ```
        *Obtain your API key from Google AI Studio.*

6.  **Run OpenAplha_Evolve!**
    The `main.py` file is configured with an example task (Dijkstra's algorithm). To run it:
    ```bash
    python -m main # Or python main.py - check based on your new structure
    ```
    Watch the logs to see the evolutionary process unfold!

---

## 💡 Defining Your Own Algorithmic Quests!

Want to challenge OpenAplha_Evolve with a new problem? It's easy:

1.  **Open `main.py`**.
2.  **Modify the `TaskDefinition`**:
    *   `id`: A unique identifier for your task.
    *   `description`: A clear, detailed natural language description of the problem. This is crucial for the LLM to understand what to do.
    *   `function_name_to_evolve`: The name of the Python function the agent should try to create/evolve.
    *   `input_output_examples`: A list of dictionaries, each containing an `input` (what your function will receive) and the corresponding expected `output`. These are vital for evaluation.
        *   For complex inputs (like graphs), structure them as Python dictionaries or lists.
        *   Use `float('inf')` or `float('-inf')` directly for infinity values if needed by your problem.
    *   `allowed_imports`: Specify a list of Python standard libraries that the generated code is allowed to import (e.g., `["heapq", "math", "sys"]`).
    *   (Optional) `evaluation_criteria`: Define how success is measured (e.g., prioritize correctness, then minimize runtime).
    *   (Optional) `initial_code_prompt`: Provide a more specific starting prompt if the default isn't suitable.

3.  **Run the agent** as before.

The quality of your `description` and `input_output_examples` significantly impacts the agent's success!

---

## 🔮 The Horizon: Future Evolution

OpenAplha_Evolve is a living project. Here are some directions we're excited to explore (and invite contributions for!):

*   **Advanced Evaluation Sandboxing**: Implementing robust, secure sandboxing (e.g., using Docker or other isolation technologies) for code execution to handle potentially unsafe code and complex dependencies.
*   **Sophisticated Fitness Metrics**: Beyond correctness and basic runtime, incorporating checks for code complexity, style, resource usage, and custom domain-specific metrics.
*   **Reinforcement Learning for Prompt Strategy**: Implementing the `RLFineTunerAgent` to dynamically optimize prompt engineering strategies based on performance.
*   **Enhanced Monitoring & Visualization**: Developing tools (via `MonitoringAgent`) to visualize the evolutionary process, track fitness landscapes, and understand agent behavior.
*   **Broader LLM Support**: Adding easy integrations for other powerful LLMs.
*   **Self-Correction & Reflection**: Enabling the agent to analyze its own failures more deeply and refine its problem-solving approach.
*   **Diverse Task Domains**: Applying OpenAplha_Evolve to a wider range of problems in science, engineering, and creative coding.
*   **Community-Driven Task Library**: Building a collection of interesting and challenging tasks contributed by the community.

---

## 🤝 Join the Evolution: Contributing

This is an open invitation to collaborate! Whether you're an AI researcher, a Python developer, or simply an enthusiast, your contributions are welcome.

*   **Report Bugs**: Find an issue? Let us know!
*   **Suggest Features**: Have an idea to make OpenAplha_Evolve better? Share it!
*   **Submit Pull Requests**:
    *   Fork the repository.
    *   Create a new branch for your feature or bugfix.
    *   Write clean, well-documented code.
    *   Add tests for your changes.
    *   Submit a pull request!

Let's evolve this agent together!

---

## 📜 License

This project is licensed under the **MIT License**. See the `LICENSE` file for details. (You'll need to create a `LICENSE` file with the MIT license text).

---

## 🙏 Homage

OpenAplha_Evolve is proudly inspired by the pioneering work of the Google DeepMind team on AlphaEvolve and other related research in LLM-driven code generation and automated discovery. This project aims to make the core concepts more accessible for broader experimentation and learning. We stand on the shoulders of giants.

---

*Disclaimer: This is an experimental project. Generated code may not always be optimal, correct, or secure. Always review and test code thoroughly, especially before using it in production environments.* 
