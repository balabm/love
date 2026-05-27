import asyncio
import re
from pathlib import Path

async def forge_new_tool(tool_name: str, objective: str) -> bool:
    from evolution.sandbox import run_in_sandbox
    from core.llm import get_coding_llm

    llm = get_coding_llm()
    prompt = f"Generate a single standalone Python function for: {objective}. Include if __name__ == '__main__': with an assert test case."
    response = await llm.ainvoke(prompt)

    code_match = re.search(r"```python\s*(.*?)```", response.content, re.DOTALL)
    if not code_match:
        code_match = re.search(r"```\s*(.*?)```", response.content, re.DOTALL)
    code = code_match.group(1).strip() if code_match else response.content

    result = await run_in_sandbox(code, timeout_seconds=10)

    if result.success:
        output_dir = Path("tools/generated")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{tool_name}.py").write_text(code)
        return True
    else:
        print(f"Sandbox failed: {result.stderr}")
        return False
