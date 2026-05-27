import subprocess, tempfile, os, asyncio

async def run_in_sandbox(code_string: str, timeout_seconds: int = 5) -> dict:
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            temp_file = f.name
            f.write(code_string.encode())
        python = "venv/Scripts/python.exe" if os.path.exists("venv/Scripts/python.exe") else "python"
        result = subprocess.run([python, temp_file], capture_output=True, text=True, timeout=timeout_seconds)
        return {"success": result.returncode == 0, "output": result.stdout, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Timeout"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
