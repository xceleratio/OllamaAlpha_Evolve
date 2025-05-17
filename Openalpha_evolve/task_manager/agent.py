# Task Manager Agent 
import logging
import asyncio
import uuid
from typing import List, Dict, Any, Optional

from alpha_evolve_pro.core.interfaces import (
    TaskManagerInterface, TaskDefinition, Program, BaseAgent,
    PromptDesignerInterface, CodeGeneratorInterface, EvaluatorAgentInterface,
    DatabaseAgentInterface, SelectionControllerInterface
)
from alpha_evolve_pro.config import settings

# Import concrete agent implementations
from alpha_evolve_pro.prompt_designer.agent import PromptDesignerAgent
from alpha_evolve_pro.code_generator.agent import CodeGeneratorAgent
from alpha_evolve_pro.evaluator_agent.agent import EvaluatorAgent
from alpha_evolve_pro.database_agent.agent import InMemoryDatabaseAgent # Using InMemory for now
from alpha_evolve_pro.selection_controller.agent import SelectionControllerAgent

logger = logging.getLogger(__name__)

class TaskManagerAgent(TaskManagerInterface):
    def __init__(self, task_definition: TaskDefinition, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.task_definition = task_definition # Store the task definition
        self.prompt_designer: PromptDesignerInterface = PromptDesignerAgent(task_definition=self.task_definition)
        self.code_generator: CodeGeneratorInterface = CodeGeneratorAgent()
        # Pass task_definition to EvaluatorAgent
        self.evaluator: EvaluatorAgentInterface = EvaluatorAgent(task_definition=self.task_definition)
        self.database: DatabaseAgentInterface = InMemoryDatabaseAgent() # Can be swapped with other DB agents
        self.selection_controller: SelectionControllerInterface = SelectionControllerAgent()

        self.population_size = settings.POPULATION_SIZE
        self.num_generations = settings.GENERATIONS
        self.num_parents_to_select = self.population_size // 2 # Example: select half the population size as parents

    async def initialize_population(self) -> List[Program]:
        logger.info(f"Initializing population for task: {self.task_definition.id}")
        initial_population = []
        for i in range(self.population_size):
            program_id = f"{self.task_definition.id}_gen0_prog{i}"
            logger.debug(f"Generating initial program {i+1}/{self.population_size} with id {program_id}")
            initial_prompt = self.prompt_designer.design_initial_prompt()
            generated_code = await self.code_generator.generate_code(initial_prompt, temperature=0.8) # Higher temp for diversity
            
            program = Program(
                id=program_id,
                code=generated_code,
                generation=0,
                status="unevaluated"
            )
            initial_population.append(program)
            await self.database.save_program(program) # Save to DB
        logger.info(f"Initialized population with {len(initial_population)} programs.")
        return initial_population

    async def evaluate_population(self, population: List[Program]) -> List[Program]:
        logger.info(f"Evaluating population of {len(population)} programs.")
        evaluated_programs = []
        evaluation_tasks = [self.evaluator.evaluate_program(prog, self.task_definition) for prog in population if prog.status != "evaluated"]
        
        results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            original_program = population[i] # Assumes order is maintained
            if isinstance(result, Exception):
                logger.error(f"Error evaluating program {original_program.id}: {result}", exc_info=result)
                original_program.status = "failed_evaluation"
                original_program.errors.append(str(result))
                evaluated_programs.append(original_program)
            else:
                evaluated_programs.append(result) # result is the evaluated Program object
            await self.database.save_program(evaluated_programs[-1]) # Update DB with evaluation results
            
        logger.info(f"Finished evaluating population. {len(evaluated_programs)} programs processed.")
        return evaluated_programs

    async def manage_evolutionary_cycle(self):
        logger.info(f"Starting evolutionary cycle for task: {self.task_definition.description[:50]}...")
        current_population = await self.initialize_population()
        current_population = await self.evaluate_population(current_population)

        for gen in range(1, self.num_generations + 1):
            logger.info(f"--- Generation {gen}/{self.num_generations} ---")

            # 1. Selection
            parents = self.selection_controller.select_parents(current_population, self.num_parents_to_select)
            if not parents:
                logger.warning(f"Generation {gen}: No parents selected. Ending evolution early.")
                break
            logger.info(f"Generation {gen}: Selected {len(parents)} parents.")

            # 2. Crossover (simplified: not implemented, LLM mutation is primary)
            # 3. Mutation (generating offspring)
            offspring_population = []
            num_offspring_per_parent = (self.population_size + len(parents) -1) // len(parents) # Ensure population size is met
            
            generation_tasks = []
            for i, parent in enumerate(parents):
                for j in range(num_offspring_per_parent):
                    if len(offspring_population) + len(parents) >= self.population_size and j > 0 : # Rough check to avoid overshooting by too much
                        pass # break # Avoid too many offspring if only a few parents
                    
                    child_id = f"{self.task_definition.id}_gen{gen}_child{len(offspring_population)}"
                    generation_tasks.append(self.generate_offspring(parent, gen, child_id))
            
            generated_offspring_results = await asyncio.gather(*generation_tasks, return_exceptions=True)

            for result in generated_offspring_results:
                if isinstance(result, Exception):
                    logger.error(f"Error generating offspring: {result}", exc_info=result)
                elif result:
                    offspring_population.append(result)
                    await self.database.save_program(result) # Save to DB

            logger.info(f"Generation {gen}: Generated {len(offspring_population)} offspring.")
            if not offspring_population:
                logger.warning(f"Generation {gen}: No offspring generated. May indicate issues with LLM or prompting.")
                # Potentially re-use parents or end early if no new offspring
                if not parents: break # no parents, no offspring, definitely stop
                # offspring_population = parents # if no new ones, try to continue with parents as offspring

            # 4. Evaluation of Offspring
            offspring_population = await self.evaluate_population(offspring_population)

            # 5. Survivor Selection
            current_population = self.selection_controller.select_survivors(current_population, offspring_population, self.population_size)
            logger.info(f"Generation {gen}: New population size: {len(current_population)}.")

            best_program_this_gen = sorted(current_population, key=lambda p: (p.fitness_scores.get("correctness", -1), -p.fitness_scores.get("runtime_ms", float('inf'))), reverse=True) 
            if best_program_this_gen:
                 logger.info(f"Generation {gen}: Best program: ID={best_program_this_gen[0].id}, Fitness={best_program_this_gen[0].fitness_scores}")
            else:
                logger.warning(f"Generation {gen}: No programs in current population after survival selection.")
                break

            # Optional: RL/Fine-tuning step (not implemented here)
            # Optional: Monitoring step (not implemented here)

        logger.info("Evolutionary cycle completed.")
        final_best = await self.database.get_best_programs(task_id=self.task_definition.id, limit=1, objective="correctness_score")
        if final_best:
            logger.info(f"Overall Best Program: {final_best[0].id}, Code:\n{final_best[0].code}\nFitness: {final_best[0].fitness_scores}")
        else:
            logger.info("No best program found at the end of evolution.")
        return final_best
    
    async def generate_offspring(self, parent: Program, generation_num: int, child_id:str) -> Optional[Program]:
        logger.debug(f"Generating offspring from parent {parent.id} for generation {generation_num}")
        # Try to fix bugs if parent has errors and high failure rate (e.g. correctness 0)
        if parent.errors and parent.fitness_scores.get("correctness", 1.0) == 0.0:
            # Simplified: take the first error
            error_info = {"message": parent.errors[0], "details": "From previous evaluation"}
            mutation_prompt = self.prompt_designer.design_bug_fix_prompt(program=parent, error_message=error_info["message"], execution_output=error_info["details"])
            logger.info(f"Attempting bug fix for parent {parent.id}")
        else:
            # Pass recent eval feedback if available
            feedback = {"errors": parent.errors, "fitness": parent.fitness_scores}
            mutation_prompt = self.prompt_designer.design_mutation_prompt(program=parent, evaluation_feedback=feedback)
            logger.info(f"Attempting mutation for parent {parent.id}")
        
        # Use a slightly higher temperature for mutation to encourage exploration but not too wild
        generated_code = await self.code_generator.generate_code(mutation_prompt, temperature=0.75)

        if "# Error:" in generated_code or not generated_code.strip():
            logger.warning(f"Failed to generate valid code for offspring of {parent.id}. LLM Output: {generated_code}")
            return None

        offspring = Program(
            id=child_id,
            code=generated_code,
            generation=generation_num,
            parent_id=parent.id,
            status="unevaluated"
        )
        return offspring

    async def execute(self) -> Any:
        return await self.manage_evolutionary_cycle()

# Example Usage (for testing this agent directly):
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # To see DEBUG logs from specific modules, you can do:
    # logging.getLogger("alpha_evolve_pro.code_generator.agent").setLevel(logging.DEBUG)
    # logging.getLogger("alpha_evolve_pro.prompt_designer.agent").setLevel(logging.DEBUG)

    task_manager = TaskManagerAgent(task_definition=sample_task) # Pass sample_task here

    # Define a simple task
    sample_task = TaskDefinition(
        id="sum_list_task_001",
        description="Write a Python function called `solve(numbers)` that takes a list of integers `numbers` and returns their sum. The function should handle empty lists correctly by returning 0.",
        input_output_examples=[
            {"input": [1, 2, 3], "output": 6},
            {"input": [], "output": 0},
            {"input": [-1, 0, 1], "output": 0},
            {"input": [10, 20, 30, 40, 50], "output": 150}
        ],
        evaluation_criteria={"target_metric": "correctness", "goal": "maximize"},
        initial_code_prompt = "Please provide a Python function `solve(numbers)` that sums a list of integers. Handle empty lists by returning 0."
    )
    
    # Reduce generations/population for quicker test
    task_manager.num_generations = 3 # settings.GENERATIONS = 3
    task_manager.population_size = 5 # settings.POPULATION_SIZE = 5
    task_manager.num_parents_to_select = 2 # settings.POPULATION_SIZE // 2 

    async def run_task():
        # Ensure GEMINI_API_KEY is in your .env file or environment
        try:
            best_programs = await task_manager.manage_evolutionary_cycle() # Removed sample_task argument
            if best_programs:
                print(f"\n*** Evolution Complete! Best program found: ***")
                print(f"ID: {best_programs[0].id}")
                print(f"Generation: {best_programs[0].generation}")
                print(f"Fitness: {best_programs[0].fitness_scores}")
                print(f"Code:\n{best_programs[0].code}")
            else:
                print("\n*** Evolution Complete! No suitable program was found. ***")
        except Exception as e:
            logger.error("An error occurred during the task management cycle.", exc_info=True)

    asyncio.run(run_task()) 