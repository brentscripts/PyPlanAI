print("\n--- Testing real GroqPlannerClient ---")
from pyplanai.core.llm import GroqPlannerClient

llm_client = GroqPlannerClient()
test_tasks = [
    {"title": "Finish PyPlanAI core layer", "priority": 1, "notes": ""},
    {"title": "Call dentist to reschedule", "priority": 3, "notes": ""},
]
result = llm_client.generate_blueprint("2026-09-03", test_tasks)
print(type(result))
print(len(result), "blocks returned")
for block in result:
    print(block)