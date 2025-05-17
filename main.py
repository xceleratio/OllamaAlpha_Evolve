"""
Main entry point for the AlphaEvolve Pro application.
Orchestrates the different agents and manages the evolutionary loop.
"""
import asyncio
import logging
import sys # Required for sys.maxsize in task definition

from alpha_evolve_pro.task_manager.agent import TaskManagerAgent
from alpha_evolve_pro.core.interfaces import TaskDefinition
# from alpha_evolve_pro.config import settings # Not strictly needed here if TaskManagerAgent handles it

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

async def run_alpha_evolve_pro():
    """
    Initializes and runs the AlphaEvolve Pro task manager with a specific task.
    """
    logger.info("Starting AlphaEvolve Pro...")

    # 1. Define the algorithmic task
    # Task: Implement Dijkstra's algorithm for shortest paths in a weighted graph using adjacency list.
    dijkstra_task = TaskDefinition(
        id="dijkstra_shortest_path", # Using the adjacency list version ID
        description="Implement Dijkstra\\'s algorithm to find the shortest paths from a source node to all other nodes in a weighted graph. The graph is represented as an adjacency list where keys are node IDs and values are dictionaries of neighbor_node: weight. The function should take the graph and the source node as input and return a dictionary of node: shortest_distance_from_source. Use float('inf') for unreachable nodes.",
        function_name_to_evolve="dijkstra",
        input_output_examples=[
            {
                "input": {"graph": {
                    0: {1: 4, 7: 8},
                    1: {0: 4, 2: 8, 7: 11},
                    2: {1: 8, 3: 7, 8: 2, 5: 4},
                    3: {2: 7, 4: 9, 5: 14},
                    4: {3: 9, 5: 10},
                    5: {2: 4, 3: 14, 4: 10, 6: 2},
                    6: {5: 2, 7: 1, 8: 6},
                    7: {0: 8, 1: 11, 6: 1},
                    8: {2: 2, 6: 6, 7: 7}
                }, "source_node": 0},
                "output": {0: 0, 1: 4, 2: 12, 3: 19, 4: 21, 5: 11, 6: 9, 7: 8, 8: 14}
            },
            # Test case 2: Disconnected graph
            {
                "input": {"graph": {
                    0: {1: 10},
                    1: {0: 10},
                    2: {3: 5},
                    3: {2: 5}
                }, "source_node": 0},
                "output": {0: 0, 1: 10, 2: float('inf'), 3: float('inf')}
            },
            # Test case 3: Single node graph
            {
                "input": {"graph": {0: {}}, "source_node": 0},
                "output": {0: 0}
            },
            # Test case 4: Linear graph
            {
                "input": {"graph": {
                    0: {1: 1},
                    1: {2: 2},
                    2: {3: 3}
                }, "source_node": 0},
                "output": {0: 0, 1: 1, 2: 3, 3: 6} # 0->1 (1), 0->1->2 (1+2=3), 0->1->2->3 (1+2+3=6)
            },
            # Test case 5: Graph with a cycle, but path to target exists
            {
                "input": {"graph": {
                    0: {1: 2, 2: 5},
                    1: {2: 1, 3: 6},
                    2: {0: 5, 1: 1, 3: 2}, # Cycle 0-2-1-0
                    3: {}
                }, "source_node": 0},
                "output": {0: 0, 1: 2, 2: 3, 3: 5} # 0->1 (2), 0->1->2 (2+1=3), 0->1->2->3 (3+2=5)
            }
        ],
        evaluation_criteria=(
            "Correctness: Must pass all test cases. Output for unreachable nodes should be float('inf'). "
            "Efficiency: Minimize execution time. Standard library imports like 'heapq' and 'sys' are allowed. Do not use external libraries not available in a standard Python environment."
        ),
        allowed_imports=["heapq", "sys", "math"],
        # initial_code_prompt is optional as per interfaces.py
    )

    # 2. Initialize the Task Manager Agent
    # It will use settings from config/settings.py for model names, API keys, etc.
    task_manager = TaskManagerAgent(task_definition=dijkstra_task)

    # 3. Run the evolutionary process
    try:
        best_program = await task_manager.execute()
        if best_program:
            logger.info(f"AlphaEvolve Pro finished. Overall best program found for task '{dijkstra_task.id}':")
            logger.info(f"Program ID: {best_program.program_id}")
            logger.info(f"Fitness: Correctness={best_program.fitness.get('correctness_score', 'N/A')*100:.2f}%, Runtime={best_program.fitness.get('runtime_ms', 'N/A')}ms")
            logger.info(f"Generation: {best_program.generation}")
            logger.info("Code:\n" + best_program.code)
        else:
            logger.info(f"AlphaEvolve Pro finished. No successful program was evolved for task '{dijkstra_task.id}'.")
    except Exception as e:
        logger.error(f"An error occurred during the evolutionary process: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_alpha_evolve_pro())
