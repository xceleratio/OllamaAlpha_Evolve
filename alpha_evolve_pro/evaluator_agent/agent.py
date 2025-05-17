# Evaluator Agent 
import time
import logging
import traceback
import subprocess
import tempfile
import os
import ast
import json
import asyncio
import sys
from typing import Optional, Dict, Any, Tuple, Union

from alpha_evolve_pro.core.interfaces import EvaluatorAgentInterface, Program, TaskDefinition, BaseAgent
from alpha_evolve_pro.config import settings

logger = logging.getLogger(__name__)

class EvaluatorAgent(EvaluatorAgentInterface, BaseAgent):
    def __init__(self, task_definition: TaskDefinition):
        super().__init__()
        self.task_definition = task_definition
        self.timeout_seconds = settings.EVALUATION_TIMEOUT_SECONDS
        logger.info(f"EvaluatorAgent initialized for task: {self.task_definition.id} with timeout: {self.timeout_seconds}s")

    def _check_syntax(self, code: str) -> Union[str, None]:
        logger.debug("Performing syntax check.")
        try:
            ast.parse(code)
            logger.debug("Syntax check successful.")
            return None
        except SyntaxError as e:
            logger.warning(f"Syntax check failed: {e}")
            return f"SyntaxError: {e.msg} on line {e.lineno}"
        except Exception as e:
            logger.warning(f"Unexpected error during syntax check: {e}")
            return f"Unexpected SyntaxCheckError: {str(e)}"

    async def _execute_code_safely(
        self, 
        code_to_run: str, 
        inputs: Dict[str, Any],
        function_name: str,
        timeout_seconds: int
    ) -> Dict[str, Any]:
        logger.debug(f"Preparing to execute code for function '{function_name}' with inputs: {inputs}. Timeout: {timeout_seconds}s")
        tmp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as fp:
                fp.write(code_to_run)
                if self.task_definition.input_output_examples:
                    fp.write("\nimport sys\nimport json\nimport math\n")
                    try:
                        parsed_code = ast.parse(code_to_run)
                        for node in ast.walk(parsed_code):
                            if isinstance(node, ast.FunctionDef):
                                function_name = node.name
                                break
                    except Exception:
                        pass

                    # Serialize test cases to JSON string first
                    test_cases_json_str = json.dumps(self.task_definition.input_output_examples)
                    # Replace JSON representations of infinity/NaN with Python's float versions
                    test_cases_py_str = test_cases_json_str.replace(": Infinity", ": float('inf')")
                    test_cases_py_str = test_cases_py_str.replace(": -Infinity", ": float('-inf')")
                    test_cases_py_str = test_cases_py_str.replace(": NaN", ": float('nan')")

                    fp.write(f"test_cases = {test_cases_py_str}\n") # Use the Python-compatible string
                    fp.write(f"results = []\n")
                    fp.write(f"for case in test_cases:\n")
                    fp.write(f"    input_val_str = case.get('input')\n")
                    fp.write(f"    try:\n")
                    fp.write(f"        input_val = eval(str(input_val_str))\n") 
                    fp.write(f"        result = {function_name}(input_val)\n")
                    fp.write(f"        results.append(result)\n")
                    fp.write(f"    except Exception as e:\n")
                    fp.write(f"        results.append(f'ERROR: {{str(e)}}')\n") 
                    fp.write(f"print(json.dumps(results))\n")
                tmp_file_path = fp.name
            
            start_time = time.perf_counter()
            process = await asyncio.create_subprocess_exec(
                sys.executable, tmp_file_path,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout_seconds)
            end_time = time.perf_counter()
            execution_time_ms = (end_time - start_time) * 1000

            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            if process.returncode != 0:
                error_msg = f"Execution failed with return code {process.returncode}. Stderr: {stderr_str}"
                if stdout_str: error_msg += f" Stdout: {stdout_str}"
                logger.warning(error_msg)
                return {"error": error_msg, "execution_time_ms": execution_time_ms}
            
            if self.task_definition.input_output_examples:
                try:
                    output_results = json.loads(stdout_str)
                    return {"output_results": output_results, "execution_time_ms": execution_time_ms}
                except json.JSONDecodeError:
                    return {"warning": f"Warning: Output was not valid JSON despite test harness. Output: {stdout_str}", "execution_time_ms": execution_time_ms}
            else:
                return {"output_str": stdout_str, "execution_time_ms": execution_time_ms}

        except asyncio.TimeoutError:
            logger.warning(f"Code execution timed out after {self.timeout_seconds} seconds.")
            return {"error": f"TimeoutError: Execution exceeded {self.timeout_seconds} seconds.", "execution_time_ms": self.timeout_seconds * 1000}
        except Exception as e:
            logger.error(f"Error during code execution: {e}\n{traceback.format_exc()}")
            return {"error": f"ExecutionError: {e}", "execution_time_ms": 0.0}
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                try:
                    os.remove(tmp_file_path)
                except Exception as e_rm:
                    logger.error(f"Error deleting temporary file {tmp_file_path}: {e_rm}")

    async def evaluate_program(self, program: Program) -> Dict[str, Any]:
        logger.info(f"Evaluating program: {program.program_id} for task: {self.task_definition.id}")
        program.status = "evaluating"
        program.errors = []
        program.fitness_scores = {"correctness": 0.0, "runtime_ms": float('inf')}

        syntax_error = self._check_syntax(program.code)
        if syntax_error:
            program.errors.append(syntax_error)
            program.fitness_scores["correctness"] = 0.0
            program.status = "failed_evaluation"
            logger.warning(f"Program {program.program_id} failed syntax check: {syntax_error}")
            return program

        result = await self._execute_code_safely(program.code, self.task_definition.input_output_examples, "solve", self.timeout_seconds)
        program.fitness_scores["runtime_ms"] = result["execution_time_ms"]

        if "error" in result:
            program.errors.append(result["error"])
            program.fitness_scores["correctness"] = 0.0 # Penalize errors heavily
            program.status = "failed_evaluation"
            logger.warning(f"Program {program.program_id} failed execution: {result['error']}")
            return program

        # Basic correctness check if input/output examples are provided
        correct_count = 0
        total_tests = 0
        if self.task_definition.input_output_examples and isinstance(result["output_results"], list) and len(result["output_results"]) == len(self.task_definition.input_output_examples):
            total_tests = len(self.task_definition.input_output_examples)
            for i, example_run_result in enumerate(result["output_results"]):
                expected_output_str = str(self.task_definition.input_output_examples[i]['output'])
                actual_output_str = str(example_run_result) # example_run_result could be an error string from harness
                
                # This comparison is very basic (string comparison)
                # A more sophisticated system would parse expected/actual outputs properly
                if actual_output_str == expected_output_str:
                    correct_count += 1
                else:
                    err_msg = f"Test case {i+1} failed: Expected '{expected_output_str}', Got '{actual_output_str}'"
                    program.errors.append(err_msg)
                    logger.debug(f"Program {program.program_id}: {err_msg}")
            
            program.fitness_scores["correctness"] = (correct_count / total_tests) if total_tests > 0 else 0.0
        elif not self.task_definition.input_output_examples:
            # No examples, assume correct if no execution errors, but this is weak.
            program.fitness_scores["correctness"] = 1.0 
            logger.info(f"Program {program.program_id} executed without errors, but no specific test cases provided.")
        else:
            # Output format mismatch or other issue with test harness results
            err_msg = f"Output format from execution harness did not match expected for test cases. Output: {str(result['output_results'])[:200]}..."
            program.errors.append(err_msg)
            program.fitness_scores["correctness"] = 0.0
            logger.warning(f"Program {program.program_id}: {err_msg}")

        if not program.errors:
            logger.info(f"Program {program.program_id} evaluated successfully. Correctness: {program.fitness_scores['correctness']:.2f}, Runtime: {result['execution_time_ms']:.2f}ms")
        
        program.status = "evaluated"
        return program

    async def execute(self, program: Program) -> Dict[str, Any]:
        return await self.evaluate_program(program)

    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        logger.debug(f"Comparing outputs. Actual: {actual}, Expected: {expected}")
        # ... (rest of the _compare_outputs logic from your version)
        return actual == expected

# Removed the old __main__ block from this file, 
# as TaskManagerAgent should be the entry point for full runs.
# The more detailed __main__ from your version of EvaluatorAgent was good for unit testing it.
# For now, I am removing it to keep the agent file clean.
# If you need to unit test EvaluatorAgent specifically, 
# we can re-add a similar main block or create separate test files. 