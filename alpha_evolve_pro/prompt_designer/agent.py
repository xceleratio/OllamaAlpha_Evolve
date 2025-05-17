# Prompt Designer Agent 
from typing import Optional, Dict, Any
import logging

from alpha_evolve_pro.core.interfaces import PromptDesignerInterface, Program, TaskDefinition, BaseAgent

logger = logging.getLogger(__name__)

class PromptDesignerAgent(PromptDesignerInterface, BaseAgent):
    def __init__(self, task_definition: TaskDefinition):
        super().__init__()
        self.task_definition = task_definition
        logger.info(f"PromptDesignerAgent initialized for task: {self.task_definition.id}")

    def design_initial_prompt(self) -> str:
        logger.info(f"Designing initial prompt for task: {self.task_definition.id}")
        prompt = (
            f"Task: {self.task_definition.description}\n\n"
            f"Function Signature: Create a Python function named `{self.task_definition.function_name_to_evolve}` "
            f"that accepts arguments as described or implied by the input examples. "
            f"Input examples: {self.task_definition.input_output_examples}\n\n"
            f"Evaluation Criteria: {self.task_definition.evaluation_criteria}\n\n"
            f"Allowed standard library imports for your solution: {self.task_definition.allowed_imports}. Do not use other external libraries.\n\n"
            f"Please provide only the complete Python code for the function `{self.task_definition.function_name_to_evolve}`. "
            f"Do not include any surrounding text, explanations, or markdown code fences (like ```python). "
            f"Ensure the function is self-contained or uses only the allowed imports."
        )
        logger.debug(f"Designed initial prompt:\n--PROMPT START--\n{prompt}\n--PROMPT END--")
        return prompt

    def design_mutation_prompt(self, program: Program, evaluation_feedback: dict | None = None) -> str:
        logger.info(f"Designing mutation prompt for program: {program.program_id} (Generation: {program.generation})")
        logger.debug(f"Parent program code:\n{program.code}")
        if evaluation_feedback:
            logger.debug(f"Evaluation feedback received for parent:\n{evaluation_feedback}")

        feedback_prompt_segment = ""
        if evaluation_feedback:
            correctness = evaluation_feedback.get("correctness_score", 0) * 100
            runtime = evaluation_feedback.get("runtime_ms", "N/A")
            errors = evaluation_feedback.get("errors", None)
            # stdout = evaluation_feedback.get("stdout", None) # Not including stdout in prompt for brevity
            stderr = evaluation_feedback.get("stderr", None)

            feedback_prompt_segment = f"The previous version of this code had a correctness score of {correctness:.2f}% and a runtime of {runtime} ms.\n"
            if errors:
                feedback_prompt_segment += f"It produced the following errors during evaluation: {errors}\n"
            if stderr:
                 feedback_prompt_segment += f"Standard Error output during execution: {stderr}\n"
            if correctness < 100 and not errors and not stderr:
                 feedback_prompt_segment += "It did not achieve 100% correctness but did not produce explicit errors. Review logic for test case failures.\n"
        else:
            feedback_prompt_segment = "The previous version of this code was evaluated, but detailed feedback is not available. Attempt a general improvement.\n"

        prompt = (
            f"Task: {self.task_definition.description}\n\n"
            f"Function Signature: The Python function to improve is `{self.task_definition.function_name_to_evolve}`.\n"
            f"Allowed standard library imports: {self.task_definition.allowed_imports}. Do not use other external libraries.\n\n"
            f"Current Code:\n```python\n{program.code}\n```\n\n"
            f"Evaluation Feedback on Current Code:\n{feedback_prompt_segment}\n"
            f"Instruction: Based on the task, the current code, and the evaluation feedback, provide an improved version of the function `{self.task_definition.function_name_to_evolve}`. "
            f"Focus on improving correctness and then efficiency. "
            f"If the code was incorrect, prioritize fixing the bugs. If it was correct but slow, optimize it. "
            f"If it had errors, resolve them. If no specific errors, try a logical mutation or refinement.\n\n"
            f"Please provide only the complete Python code for the improved function `{self.task_definition.function_name_to_evolve}`. "
            f"Do not include any surrounding text, explanations, or markdown code fences (like ```python). "
            f"Ensure the function is self-contained or uses only the allowed imports."
        )
        logger.debug(f"Designed mutation prompt:\n--PROMPT START--\n{prompt}\n--PROMPT END--")
        return prompt

    def design_bug_fix_prompt(self, program: Program, error_message: str, execution_output: str | None = None) -> str:
        logger.info(f"Designing bug-fix prompt for program: {program.program_id} (Generation: {program.generation})")
        logger.debug(f"Buggy program code:\n{program.code}")
        logger.debug(f"Error message: {error_message}")
        if execution_output:
            logger.debug(f"Execution output (stdout/stderr): {execution_output}")

        output_segment = f"Execution Output (stdout/stderr):\n{execution_output}\n" if execution_output else "No detailed execution output was captured beyond the error.\n"

        prompt = (
            f"Task: {self.task_definition.description}\n\n"
            f"Function Signature: The Python function to fix is `{self.task_definition.function_name_to_evolve}`.\n"
            f"Allowed standard library imports: {self.task_definition.allowed_imports}. Do not use other external libraries.\n\n"
            f"Buggy Code:\n```python\n{program.code}\n```\n\n"
            f"Error Encountered: {error_message}\n"
            f"{output_segment}\n"
            f"Instruction: The above code produced an error. Please analyze the code, the error, and any execution output to identify and fix the bug. "
            f"Provide a corrected version of the function `{self.task_definition.function_name_to_evolve}`.\n\n"
            f"Please provide only the complete Python code for the fixed function `{self.task_definition.function_name_to_evolve}`. "
            f"Do not include any surrounding text, explanations, or markdown code fences (like ```python). "
            f"Ensure the function is self-contained or uses only the allowed imports."
        )
        logger.debug(f"Designed bug-fix prompt:\n--PROMPT START--\n{prompt}\n--PROMPT END--")
        return prompt

    async def execute(self, *args, **kwargs) -> Any:
        # This agent primarily has specific design methods, not a generic execute
        # Or, you could define execute to choose a prompt type based on inputs
        raise NotImplementedError("PromptDesignerAgent.execute() is not the primary way to use this agent. Call specific design methods.")

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # Define sample_task_def first
    sample_task_def = TaskDefinition(
        id="task_001_designer_test",
        description="Create a Python function `sum_list(numbers)` that returns the sum of a list of integers. Handle empty lists by returning 0.",
        function_name_to_evolve="sum_list",
        input_output_examples=[
            {"input": [1, 2, 3], "output": 6}, # Using actual types rather than strings for demo
            {"input": [], "output": 0}
        ],
        # evaluation_criteria can be added if needed for the test
        # initial_code_prompt can be added if needed for the test
        # allowed_imports can be added if needed for the test
    )
    # Pass sample_task_def to the constructor
    designer = PromptDesignerAgent(task_definition=sample_task_def)

    initial_prompt = designer.design_initial_prompt()
    print("--- Initial Prompt ---")
    print(initial_prompt)

    sample_program = Program(
        id="prog_001",
        code="def sum_list(numbers):\n  # Buggy implementation\n  return sum(numbers) if numbers else 'Error'",
        fitness_scores={"correctness": 0.0, "runtime_ms": 10.0},
        generation=1,
        errors=["TypeError: unsupported operand type(s) for +: 'int' and 'str' on empty list with 'Error' return"]
    )
    mutation_prompt = designer.design_mutation_prompt(sample_program, evaluation_feedback={"notes": "Failed on empty list case."})
    print("\n--- Mutation Prompt ---")
    print(mutation_prompt)

    bug_fix_prompt = designer.design_bug_fix_prompt(sample_program, error_message="TypeError", execution_output="Fails when list is empty")
    print("\n--- Bug-Fix Prompt ---")
    print(bug_fix_prompt) 