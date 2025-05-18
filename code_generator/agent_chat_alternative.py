import aiohttp
from aiohttp import ClientSession, ClientTimeout
from typing import Optional, Dict, Any
import logging
import asyncio
import re
from core.interfaces import CodeGeneratorInterface, Program
from config import settings

logger = logging.getLogger(__name__)

# THIS IS A ALTERNATIVE VERSION USING THE /CHAT/ ENDPOINT in the OLLAMA API but its less adviseable since it keeps a history of the previous chat messages

class CodeGeneratorAgent(CodeGeneratorInterface):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_url = settings.OLLAMA_HOST
        timeout = ClientTimeout(total=120)  # 60 seconds max
        self.session = aiohttp.ClientSession(base_url=self.api_url, timeout=timeout)
        self.model_name = settings.PRO_MODEL_NAME
        logger.info(f"CodeGeneratorAgent initialized with model: {self.model_name}")

    async def generate_code(self, prompt: str, model_name: Optional[str] = None, temperature: Optional[float] = None, output_format: str = "code") -> str:
        effective_model_name = model_name if model_name else self.model_name
        logger.info(f"Generating code with model: {effective_model_name}, output format: {output_format}")

        # Define system prompt
        system_prompt = """
You are an expert Python programmer. Your task is to write a Python function based on the following specifications.
"""

        # Add diff instructions if requested
        if output_format == "diff":
            prompt += '''
Provide your changes as a sequence of diff blocks in the following format:
<<<<<<< SEARCH
# Original code block to be found and replaced
=======
# New code block to replace the original
>>>>>>> REPLACE
Ensure the SEARCH block is an exact segment from the current program.
Describe each change with such a SEARCH/REPLACE block.
Make sure that the changes you propose are consistent with each other.
'''

        #print(f"Received prompt for code generation (format: {output_format}):\n--PROMPT START--\n{prompt}\n--PROMPT END--")
        logger.debug(f"Received prompt for code generation (format: {output_format}):\n--PROMPT START--\n{prompt}\n--PROMPT END--")

        # Build messages list
        messages = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": prompt.strip()}
        ]

        payload = {
            "model": effective_model_name,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.1,
            "stream": False
        }

        try:
            print(f"Sending request to {self.api_url}/v1/chat/completions")
            logger.debug(f"Sending request to {self.api_url}/v1/chat/completions")
            async with self.session.post("/v1/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API call failed with status {response.status}: {error_text}")
                    raise Exception(f"API call failed: {error_text}")

                data = await response.json()
                generated_text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

                if not generated_text:
                    logger.warning("Model returned empty content")
                    raise Exception("Empty response from LLM")

                if output_format == "code":
                    cleaned_code = self._clean_llm_output(generated_text)
                    print(f"GOT ANSWER {cleaned_code}")
                    return cleaned_code
                else:
                    return generated_text

        except Exception as e:
            logger.error(f"Error during API call: {e}", exc_info=True)
            raise

    def _clean_llm_output(self, raw_code: str) -> str:
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
        logger.info("Attempting to apply diff.")
        logger.debug(f"Parent code length: {len(parent_code)}")
        logger.debug(f"Diff text:\n{diff_text}")
        modified_code = parent_code
        diff_pattern = re.compile(r"<<<<<<< SEARCH\s*?\n(.*?)\n=======\s*?\n(.*?)\n>>>>>>> REPLACE", re.DOTALL)

        for match in diff_pattern.finditer(diff_text):
            search_block = match.group(1).strip('\r\n')
            replace_block = match.group(2).strip('\r\n')

            if search_block in modified_code:
                modified_code = modified_code.replace(search_block, replace_block, 1)
                logger.debug(f"Applied one diff block. SEARCH:\n{search_block}\nREPLACE:\n{replace_block}")
            else:
                logger.warning(f"SEARCH block not found in current code state:\n{search_block}")

        return modified_code

    async def execute(self, prompt: str, model_name: Optional[str] = None, temperature: Optional[float] = None, output_format: str = "code", parent_code_for_diff: Optional[str] = None) -> str:
        logger.debug(f"CodeGeneratorAgent.execute called. Output format: {output_format}")
        generated_output = await self.generate_code(prompt=prompt, model_name=model_name, temperature=temperature, output_format=output_format)

        if output_format == "diff":
            if not parent_code_for_diff:
                logger.error("Output format is 'diff' but no parent_code_for_diff provided. Returning raw diff.")
                return generated_output

            if not generated_output.strip():
                logger.info("Generated diff is empty. Returning parent code.")
                return parent_code_for_diff

            try:
                logger.info("Applying generated diff to parent code.")
                return self._apply_diff(parent_code_for_diff, generated_output)
            except Exception as e:
                logger.error(f"Error applying diff: {e}. Returning raw diff text.", exc_info=True)
                return generated_output
        else:
            return generated_output