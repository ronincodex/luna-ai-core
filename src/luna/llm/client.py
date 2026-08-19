"""Ollama client with structured JSON prompting"""

import json
import logging
from typing import Dict, Any, Optional
import ollama

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, model: str = "qwen2.5:7b"):
        self.model = model
        self.client = ollama.Client()

    def ask_for_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Send a free-form prompt and expect a JSON response."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                options={"temperature": 0.0},
            )
            raw = response["message"]["content"].strip()
            if raw.startswith("```json"):
                raw = raw.split("```json")[1].split("```")[0]
            elif raw.startswith("```"):
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw)
        except Exception as e:
            logger.error(f"ask_for_json error: {e}")
            return None

    def ask_for_tool(
        self, user_input: str, context: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Send a prompt to the LLM asking it to decide if a tool is needed.
        Returns a dict with 'action' and relevant fields, or None on failure.
        """
        system_prompt = (
            "You are Luna, a personalized virtual assistant created by Saurabh Tiwari for IT WEBHUT. "
            "Respond ONLY with a valid JSON object.\n"
            "If the user wants to perform an action that requires a tool, use 'tool_call'.\n"
            "Available tools: get_weather, create_reminder, get_traffic, send_message.\n"
            "For send_message, include 'recipient' and 'content'.\n"
            "If the user is just chatting or asking for information, use 'direct_answer' and provide an 'answer' field.\n"
            'Example direct_answer: {"action": "direct_answer", "answer": "The capital of France is Paris."}\n'
            'Example tool_call: {"action": "tool_call", "tool_name": "get_weather", "parameters": {"location": "home", "date": "tomorrow"}}\n'
            "Output only JSON, no extra text or markdown."
        )
        full_prompt = f"{system_prompt}\n\nContext: {context}\nUser: {user_input}"

        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": full_prompt}],
                stream=False,
                options={"temperature": 0.0},
            )
            raw = response["message"]["content"].strip()

            # Clean markdown if present
            if raw.startswith("```json"):
                raw = raw.split("```json")[1].split("```")[0]
            elif raw.startswith("```"):
                raw = raw.split("```")[1].split("```")[0]
            raw = raw.strip()

            data = json.loads(raw)

            # --- Validation and return ---
            if "action" not in data:
                logger.error("LLM response missing 'action'")
                return None

            if data["action"] == "tool_call":
                if "tool_name" not in data or "parameters" not in data:
                    logger.error("Tool call missing tool_name or parameters")
                    return None
                # Valid tool call
                return data

            elif data["action"] == "direct_answer":
                if "answer" not in data:
                    logger.error("Direct answer missing 'answer' field")
                    return None
                # Valid direct answer
                return data

            else:
                logger.error(f"Unknown action: {data['action']}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e} - raw: {raw}")
            return None
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return None
