# Code Generator Agent 
import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
import asyncio # Added for retry sleep
from google.api_core.exceptions import InternalServerError, GoogleAPIError, DeadlineExceeded # For specific error handling
import time

from alpha_evolve_pro.core.interfaces import CodeGeneratorInterface, BaseAgent, Program
from alpha_evolve_pro.config import settings

logger = logging.getLogger(__name__)

class CodeGeneratorAgent(CodeGeneratorInterface):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in settings. Please set it in your .env file or config.")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_PRO_MODEL_NAME # Default to pro, can be overridden by task
        self.generation_config = genai.types.GenerationConfig(
            # candidate_count=1, # Only one candidate is needed for now
            # stop_sequences=['x'],
            # max_output_tokens=2048,
            temperature=0.7, # Adjust for creativity vs. determinism
            top_p=0.9,
            top_k=40
        )
        # Consider making temperature, top_p, top_k configurable via settings.py
        logger.info(f"CodeGeneratorAgent initialized with model: {self.model_name}")
        self.max_retries = 3
        self.retry_delay_seconds = 5

    async def generate_code(self, prompt: str, model_name: Optional[str] = None, temperature: Optional[float] = None) -> str:
        effective_model_name = model_name if model_name else self.model_name
        logger.info(f"Attempting to generate code using model: {effective_model_name}")
        logger.debug(f"Received prompt for code generation:\n--PROMPT START--\n{prompt}\n--PROMPT END--")
        
        # Create a generation config, using instance default or override if temperature is provided
        current_generation_config = genai.types.GenerationConfig(
            temperature=temperature if temperature is not None else self.generation_config.temperature,
            top_p=self.generation_config.top_p,
            top_k=self.generation_config.top_k
        )
        if temperature is not None:
            logger.debug(f"Using temperature override: {temperature}")
        
        model_to_use = genai.GenerativeModel(
            effective_model_name,
            generation_config=current_generation_config
            # safety_settings=... # Add safety settings if needed
        )

        retries = settings.API_MAX_RETRIES
        delay = settings.API_RETRY_DELAY_SECONDS
        
        for attempt in range(retries):
            try:
                logger.debug(f"API Call Attempt {attempt + 1} of {retries} to {effective_model_name}.")
                response = await model_to_use.generate_content_async(prompt)
                
                if not response.candidates:
                    logger.warning("Gemini API returned no candidates.")
                    # Check for prompt feedback if available
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        logger.error(f"Prompt blocked. Reason: {response.prompt_feedback.block_reason}")
                        logger.error(f"Prompt feedback details: {response.prompt_feedback.safety_ratings}")
                        # Depending on the block reason, we might not want to retry.
                        # For now, we will let it retry up to max_retries or raise the error.
                        # If a specific error for blocked prompts is needed, it should be raised here.
                        raise GoogleAPIError(f"Prompt blocked by API. Reason: {response.prompt_feedback.block_reason}")
                    return "" # Or raise an error

                generated_text = response.candidates[0].content.parts[0].text
                logger.debug(f"Raw response from Gemini API:\n--RESPONSE START--\n{generated_text}\n--RESPONSE END--")
                cleaned_code = self._clean_llm_output(generated_text)
                logger.debug(f"Cleaned code:\n--CLEANED CODE START--\n{cleaned_code}\n--CLEANED CODE END--")
                return cleaned_code
            except (InternalServerError, DeadlineExceeded, GoogleAPIError) as e:
                logger.warning(f"Gemini API error on attempt {attempt + 1}: {type(e).__name__} - {e}. Retrying in {delay}s...")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Gemini API call failed after {retries} retries for model {effective_model_name}.")
                    # Re-raise the last exception if all retries fail
                    raise
            except Exception as e:
                logger.error(f"An unexpected error occurred during code generation with {effective_model_name}: {e}", exc_info=True)
                # Decide if this should retry or just raise. For now, re-raise non-API errors immediately.
                raise
        
        logger.error(f"Code generation failed for model {effective_model_name} after all retries.")
        return "" # Should ideally not be reached if exceptions are re-raised

    def _clean_llm_output(self, raw_code: str) -> str:
        """
        Cleans the raw output from the LLM, typically removing markdown code fences.
        Example: ```python\ncode\n``` -> code
        """
        logger.debug(f"Attempting to clean raw LLM output. Input length: {len(raw_code)}")
        if raw_code.strip().startswith("```python"):
            cleaned = raw_code.strip()[len("```python"):].strip()
            if cleaned.endswith("```"):
                cleaned = cleaned[:-len("```")].strip()
            logger.debug("Cleaned Python markdown fences.")
            return cleaned
        elif raw_code.strip().startswith("```") and raw_code.strip().endswith("```"):
            cleaned = raw_code.strip()[len("```"): -len("```")].strip()
            logger.debug("Cleaned generic markdown fences.")
            return cleaned
        logger.debug("No markdown fences found or standard cleaning applied.")
        return raw_code.strip()

    # MODIFIED: Re-added execute method to fulfill BaseAgent contract
    async def execute(self, prompt: str, model_name: Optional[str] = None, temperature: Optional[float] = None) -> str:
        """Generic execution method, calls generate_code."""
        logger.debug(f"CodeGeneratorAgent.execute called. Relaying to generate_code.")
        return await self.generate_code(prompt=prompt, model_name=model_name, temperature=temperature)

# Example Usage (for testing this agent directly)
if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.DEBUG)
    async def test_generation():
        agent = CodeGeneratorAgent()
        # Ensure you have a .env file with GEMINI_API_KEY set
        # or that the key is available as an environment variable.
        test_prompt = "Write a Python function that takes two numbers and returns their sum."
        # MODIFIED: Call generate_code directly, pass temperature if desired for test
        generated_code = await agent.generate_code(test_prompt, temperature=0.6)
        print("--- Generated Code ---")
        print(generated_code)
        print("----------------------")

        test_prompt_diff = ("""
Given the function below:
```python
def add(a, b):
    return a + b
```
Suggest a modification to handle an optional third argument `c` which defaults to 0 and is added to the sum. Provide only the complete modified function code.
""")
        generated_diff_code = await agent.generate_code(test_prompt_diff, temperature=0.5)
        print("--- Generated Diff Code ---")
        print(generated_diff_code)
        print("----------------------")

    asyncio.run(test_generation()) 