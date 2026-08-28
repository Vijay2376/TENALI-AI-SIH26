"""Google Gemini AI integration service for query understanding and answer synthesis."""

from typing import Any

from app.config import settings


class GeminiService:
    """Service wrapper for Google Gemini API with robust offline fallback."""

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Google GenAI client if API key is provided."""
        if self.api_key and self.api_key.strip():
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception:  # noqa: BLE001
                self._client = None

    def is_available(self) -> bool:
        """Check if Gemini API client is active and configured."""
        return self._client is not None

    def classify_intent_with_llm(
        self, query: str, mode: str, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Use Gemini to understand complex natural-language queries into structured task specs."""
        if not self.is_available():
            return None

        prompt = f"""You are TENALI AI's query intent router for remote sensing imagery.
User Query: "{query}"
Input Mode: "{mode}" (single | bi_temporal | optical_sar)
Metadata: {metadata or {}}

Classify this query into one of the following Task Types:
- single_image_vqa
- grounding
- captioning
- bi_temporal_change
- built_up_change
- optical_sar_analysis
- spatial_analysis

Output valid JSON only with keys: "task_type", "target_entity", "requires_tools" (list of tool names from [vqa_tool, grounding_tool, captioning_tool, change_detection_tool, change_statistics_tool, optical_sar_tool, spatial_analysis_tool, evidence_generation_tool]), "reasoning".
"""
        if self._client is None:
            return None

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            if not response or not response.text:
                return None
            text = response.text.strip()
            # Clean possible markdown json fences
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()

            import json
            data = json.loads(text)
            return data
        except Exception:  # noqa: BLE001
            return None

    def synthesize_grounded_answer(
        self,
        query: str,
        task: str,
        analysis_data: dict[str, Any],
        disclaimer: str,
    ) -> str | None:
        """Synthesize a clear, authoritative, grounded technical answer based strictly on evidence."""
        if not self.is_available() or self._client is None:
            return None

        prompt = f"""You are TENALI AI, an Earth Observation intelligence assistant.
Synthesize a concise, technically grounded answer for the user query.
DO NOT hallucinate facts outside the provided specialist analysis data.

User Query: "{query}"
Task Type: "{task}"
Specialist Analysis Output: {analysis_data}
Disclaimer note: "{disclaimer}"

Rules:
1. Reference quantitative metrics (percentages, classes, counts) from the specialist output.
2. State clearly whether findings are based on domain adaptation, differential analysis, or optical-SAR fusion.
3. Keep the answer under 3-4 professional sentences.
"""
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            if response and response.text:
                return response.text.strip()
            return None
        except Exception:  # noqa: BLE001
            return None


# Global Gemini Service instance
gemini_service = GeminiService()
