import os
import logging
import asyncio
from typing import Optional, Dict, Any
from http import HTTPStatus
import aiohttp  # Async HTTP client for calling Ollama
import re
from core.interfaces import CodeGeneratorInterface, BaseAgent, Program
from config import settings

logger = logging.getLogger(__name__)


class CodeGeneratorAgent(CodeGeneratorInterface):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not settings.OLLAMA_HOST:
            raise ValueError("OLLAMA_HOST not found in settings. Please set it in your .env file or config.")
        self.ollama_host = settings.OLLAMA_HOST.rstrip('/')
        self.model_name = settings.OLLAMA_MODEL_NAME  # e.g., 'codellama', 'llama3', etc.
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 512  # Adjust based on expected output size
        }
        logger.info(f"CodeGeneratorAgent initialized with model: {self.model_name}")

    async def generate_code(self, prompt: str, model_name: Optional[str] = None,
                            temperature: Optional[float] = None, output_format: str = "code") -> str:
        effective_model_name = model_name if model_name else self.model_name
        logger.info(f"Attempting to generate code using model: {effective_model_name}, output_format: {output_format}")

        if output_format == "diff":
            prompt += '''Provide your changes as a sequence of diff blocks in the following format:<<<<<<< SEARCH # Original code block to be found and replaced ======= # New code block to replace the original >>>>>>> REPLACE Ensure the SEARCH block is an exact segment from the current program. Describe each change with such a SEARCH/REPLACE block. Make sure that the changes you propose are consistent with each other.'''

        logger.debug(f"Received prompt for code generation (format: {output_format}):--PROMPT START--{prompt}--PROMPT END--")

        # Override temperature if provided
        gen_config = self.generation_config.copy()
        if temperature is not None:
            gen_config["temperature"] = temperature
            logger.debug(f"Using temperature override: {temperature}")

        payload = {
            "model": effective_model_name,
            "prompt": prompt,
            "stream": False,
            **gen_config
        }

        retries = settings.API_MAX_RETRIES
        delay = settings.API_RETRY_DELAY_SECONDS

        async with aiohttp.ClientSession() as session:
            for attempt in range(retries):
                try:
                    logger.debug(f"API Call Attempt {attempt + 1} of {retries} to Ollama at {self.ollama_host}/api/generate")
                    async with session.post(f"{self.ollama_host}/api/generate", json=payload, timeout=60) as response:
                        if response.status != HTTPStatus.OK:
                            error_text = await response.text()
                            logger.warning(f"Ollama returned status {response.status}: {error_text}")
                            if attempt < retries - 1:
                                logger.info(f"Retrying in {delay}s...")
                                await asyncio.sleep(delay)
                                delay *= 2
                            else:
                                raise Exception(f"Ollama request failed after {retries} attempts: {error_text}")
                            continue

                        result = await response.json()
                        generated_text = result.get("response", "").strip()

                        logger.debug(f"Raw response from Ollama:--RESPONSE START--{generated_text}--RESPONSE END--")

                        if output_format == "code":
                            cleaned_code = self._clean_llm_output(generated_text)
                            logger.debug(f"Cleaned code:--CLEANED CODE START--{cleaned_code}--CLEANED CODE END--")
                            return cleaned_code
                        else:
                            return generated_text

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logger.warning(f"Network error during Ollama call: {e}. Retrying in {delay}s...")
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"Failed to reach Ollama after {retries} retries.")
                        raise
                except Exception as e:
                    logger.error(f"Unexpected error during code generation: {e}", exc_info=True)
                    raise

        logger.error("Code generation failed after all retries.")
        return ""

    def _clean_llm_output(self, raw_code: str) -> str:
        """
        Cleans the raw output from the LLM, typically removing markdown code fences.
        Example: ```python code``` -> code
        """
        logger.debug(f"Attempting to clean raw LLM output. Input length: {len(raw_code)}")
        code = raw_code.strip()
        if code.startswith("```python") and code.endswith("```"):
            cleaned = code[len("```python"): -len("```")].strip()
            logger.debug("Cleaned Python markdown fences.")
            return cleaned
        elif code.startswith("```") and code.endswith("```"):
            cleaned = code[len("```"): -len("```")].strip()
            logger.debug("Cleaned generic markdown fences.")
            return cleaned
        logger.debug("No markdown fences found or standard cleaning applied to the stripped code.")
        return code

    def _apply_diff(self, parent_code: str, diff_text: str) -> str:
        """
        Applies a diff in the AlphaEvolve format to the parent code.
        Diff format:
        <<<<<<< SEARCH
        # Original code block
        =======
        # New code block
        >>>>>>> REPLACE
        """
        logger.info("Attempting to apply diff.")
        logger.debug(f"Parent code length: {len(parent_code)}")
        logger.debug(f"Diff text:{diff_text}")
        modified_code = parent_code
        diff_pattern = re.compile(r"<<<<<<< SEARCH\s*?(.*?)=======\s*?(.*?)>>>>>>> REPLACE", re.DOTALL)
        for match in diff_pattern.finditer(diff_text):
            search_block = match.group(1).strip('\n')
            replace_block = match.group(2).strip('\n')
            search_block_normalized = search_block.replace('\r\n', '\n').replace('\r', '\n')
            try:
                if search_block_normalized in modified_code:
                    modified_code = modified_code.replace(search_block_normalized, replace_block, 1)
                    logger.debug(f"Applied one diff block. SEARCH:{search_block_normalized}REPLACE:{replace_block}")
                else:
                    logger.warning(f"Diff application: SEARCH block not found in current code state:{search_block_normalized}")
            except re.error as e:
                logger.error(f"Regex error during diff application: {e}")
                continue
        if modified_code == parent_code and diff_text.strip():
            logger.warning("Diff text was provided, but no changes were applied. Check SEARCH blocks/diff format.")
        elif modified_code != parent_code:
            logger.info("Diff successfully applied, code has been modified.")
        else:
            logger.info("No diff text provided or diff was empty, code unchanged.")
        return modified_code

    async def execute(self, prompt: str, model_name: Optional[str] = None, temperature: Optional[float] = None,
                      output_format: str = "code", parent_code_for_diff: Optional[str] = None) -> str:
        """
        Generic execution method.
        If output_format is 'diff', it generates a diff and applies it to parent_code_for_diff.
        Otherwise, it generates full code.
        """
        logger.debug(f"CodeGeneratorAgent.execute called. Output format: {output_format}")
        generated_output = await self.generate_code(
            prompt=prompt,
            model_name=model_name,
            temperature=temperature,
            output_format=output_format
        )
        if output_format == "diff":
            if not parent_code_for_diff:
                logger.error("Output format is 'diff' but no parent_code_for_diff provided. Returning raw diff.")
                return generated_output
            if not generated_output.strip():
                logger.info("Generated diff is empty. Returning parent code.")
                return parent_code_for_diff
            try:
                logger.info("Applying generated diff to parent code.")
                modified_code = self._apply_diff(parent_code_for_diff, generated_output)
                return modified_code
            except Exception as e:
                logger.error(f"Error applying diff: {e}. Returning raw diff text.", exc_info=True)
                return generated_output
        else:  # "code"
            return generated_output


# Example Usage (for testing this agent directly)
if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.DEBUG)

    async def test_diff_application():
        agent = CodeGeneratorAgent()
        parent = """Line 1
Line 2 to be replaced
Line 3
Another block
To be changed
End of block
Final line"""
        diff = """Some preamble text from LLM...
<<<<<<< SEARCH
Line 2 to be replaced
=======
Line 2 has been successfully replaced
>>>>>>> REPLACE
Some other text...
<<<<<<< SEARCH
Another block
To be changed
End of block
=======
This
Entire
Block
Is New
>>>>>>> REPLACE
Trailing text..."""
        expected_output = """Line 1
Line 2 has been successfully replaced
Line 3
This
Entire
Block
Is New
Final line"""
        print("--- Testing _apply_diff directly ---")
        result = agent._apply_diff(parent, diff)
        print("Result of diff application:")
        print(result)
        assert result.strip() == expected_output.strip(), f"Direct diff application failed.\nExpected:\n{expected_output}\nGot:\n{result}"
        print("_apply_diff test passed.")

    async def main_tests():
        await test_diff_application()
        print("\nAll selected local tests in CodeGeneratorAgent passed.")

    asyncio.run(main_tests())