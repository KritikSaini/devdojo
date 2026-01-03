import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

# --- Load Agent URLs and API Keys from .env file ---
DIFY_AGENT_1_API_URL = os.getenv("DIFY_AGENT_1_API_URL")
DIFY_AGENT_1_API_KEY = os.getenv("DIFY_AGENT_1_API_KEY")

DIFY_AGENT_2_API_URL = os.getenv("DIFY_AGENT_2_API_URL")
DIFY_AGENT_2_API_KEY = os.getenv("DIFY_AGENT_2_API_KEY")

DIFY_AGENT_3_API_URL = os.getenv("DIFY_AGENT_3_API_URL")
DIFY_AGENT_3_API_KEY = os.getenv("DIFY_AGENT_3_API_KEY")

DIFY_AGENT_4_API_URL = os.getenv("DIFY_AGENT_4_API_URL")
DIFY_AGENT_4_API_KEY = os.getenv("DIFY_AGENT_4_API_KEY")


async def _safe_post(url: str, payload: dict, api_key: str):
    """Safely performs a POST request with the correct authentication for each agent."""
    if not url or not api_key:
        raise ValueError("Dify agent URL or API Key is not configured in .env file.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            print("\n--- Dify Raw Response ---")
            print(f"URL: {url}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            print("-------------------------\n")
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "failed":
                raise RuntimeError(f"Dify agent at {url} failed with error: {data.get('error')}")
            
            return data

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"HTTP error {e.response.status_code} for URL {url}: {e.response.text}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON from Dify for URL {url}. Raw response:\n{repr(response.text)}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while calling Dify agent at {url}: {e}")


# (trigger_agent_1, trigger_agent_2_breakdown, trigger_agent_3_testcases remain the same)
# ...
async def trigger_agent_1(Topic: str, difficulty: str, user_id: str):
    payload = { "inputs": { "Topic": Topic, "difficulty": difficulty }, "response_mode": "blocking", "user": user_id }
    return await _safe_post(DIFY_AGENT_1_API_URL, payload, DIFY_AGENT_1_API_KEY)

async def trigger_agent_2_breakdown(statement: str, user_id: str):
    payload = { "inputs": { "statement": statement }, "response_mode": "blocking", "user": user_id }
    return await _safe_post(DIFY_AGENT_2_API_URL, payload, DIFY_AGENT_2_API_KEY)

async def trigger_agent_3_testcases(prompt: str, user_id: str):
    payload = { "inputs": { "prompt": prompt }, "response_mode": "blocking", "user": user_id }
    return await _safe_post(DIFY_AGENT_3_API_URL, payload, DIFY_AGENT_3_API_KEY)


# --- Agent 4: Evaluate Submission (UPDATED) ---
async def trigger_agent_4_evaluation(user_code: str, test_cases: str, user_id: str):
    """
    This function now accepts the raw user_code as a string.
    """
    payload = {
        "inputs": {
            # The variable names here MUST match the variables in your Dify START block
            "user_code": user_code,
            "test_cases": test_cases
        },
        "response_mode": "blocking",
        "user": user_id
    }
    return await _safe_post(DIFY_AGENT_4_API_URL, payload, DIFY_AGENT_4_API_KEY)