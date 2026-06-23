import asyncio
import logging
from app.services.agents.agent_builder import FabricAgent

logger = logging.getLogger(__name__)

async def run_development_workflow(requirement: str):
    """
    Basic workflow:
    1. Architect Agent: Create architecture plan
    2. Coder Agent: Write code based on architecture
    3. Reviewer Agent: Check code and security
    """
    logger.info("1. Starting Architect Agent...")
    architect = FabricAgent(pattern_name="create_design_document", temperature=0.4)
    architecture_plan = await architect.ainvoke(requirement)
    
    logger.info("2. Starting Coder Agent...")
    # Use create_coding_feature instead of write_code
    coder = FabricAgent(pattern_name="create_coding_feature", temperature=0.1)
    # Send both requirement and architecture plan to the coder
    coder_input = f"REQUIREMENT:\n{requirement}\n\nARCHITECTURE PLAN:\n{architecture_plan}"
    source_code = await coder.ainvoke(coder_input)
    
    logger.info("3. Starting Reviewer Agent...")
    reviewer = FabricAgent(pattern_name="review_code", temperature=0.1)
    review_report = await reviewer.ainvoke(source_code)
    
    return {
        "architecture_plan": architecture_plan,
        "source_code": source_code,
        "review_report": review_report
    }

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    # Configure logging for direct execution
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    sample_req = "Create a GET /health API endpoint in FastAPI that returns status 'ok', version '1.0' and current server time."
    print(f"--- RUNNING ORCHESTRATOR TEST ---\nRequirement: {sample_req}\n")
    
    try:
        result = asyncio.run(run_development_workflow(sample_req))
        print("\n================ ARCHITECTURE PLAN ================\n")
        print(result["architecture_plan"])
        print("\n================ SOURCE CODE ================\n")
        print(result["source_code"])
        print("\n================ REVIEW REPORT ================\n")
        print(result["review_report"])
    except Exception as e:
        logger.error(f"Error: {e}")

