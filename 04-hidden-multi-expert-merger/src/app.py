"""
Hidden Multi-Expert Merger Service
Combines draft text with helper critiques into final persona output
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uvicorn

from merge_templates import get_merge_template


class ComposeRequest(BaseModel):
    """Request model for compose endpoint"""
    prompt: str = Field(..., description="Original prompt/draft text")
    persona: str = Field(..., description="Target persona for final output")
    tone_policy: List[str] = Field(default_factory=list,
                                   description="Tone policy filters")
    budgets: Dict[str, Any] = Field(default_factory=dict,
                                    description="Budget constraints")


class ComposeResponse(BaseModel):
    """Response model for compose endpoint"""
    final_text: str = Field(..., description="Merged final text")
    processing_time_ms: float = Field(..., description="Processing time in ms")
    helpers_used: int = Field(..., description="Number of helpers used")
    tokens_used: int = Field(..., description="Total tokens used")


class HelperCritique:
    """Simulated helper critique with budget constraints"""

    def __init__(self, name: str, max_tokens: int = 120):
        self.name = name
        self.max_tokens = max_tokens
        self.template = "persona_preserving"

    async def generate_critique(self, draft: str, persona: str,
                               time_budget_ms: int = 1500) -> str:
        """Generate critique with budget constraints"""
        start_time = time.time()

        # Simulate processing time (random between 100-500ms for local sub-10B)
        processing_time = min(time_budget_ms / 1000,
                             0.1 + (hash(self.name + draft) % 400) / 1000)
        await asyncio.sleep(processing_time)

        # Generate critique based on helper type
        if "concise" in self.name.lower():
            critique = self._generate_concise_critique(draft, persona)
        elif "creative" in self.name.lower():
            critique = self._generate_creative_critique(draft, persona)
        else:
            critique = self._generate_general_critique(draft, persona)

        # Enforce token limit (rough approximation: 4 chars per token)
        token_count = len(critique) // 4
        if token_count > self.max_tokens:
            critique = critique[:self.max_tokens * 4] + "..."

        elapsed_time = (time.time() - start_time) * 1000
        if elapsed_time > time_budget_ms:
            raise TimeoutError(f"Helper {self.name} exceeded time budget")

        return critique

    def _generate_concise_critique(self, draft: str, persona: str) -> str:
        """Generate concise, executive-style critique"""
        return f"""Remove unnecessary words. Focus on key points.
Make language more direct and professional.
Ensure consistency with {persona} persona.
Shorten sentences for better impact."""

    def _generate_creative_critique(self, draft: str, persona: str) -> str:
        """Generate creative enhancement critique"""
        return f"""Add vivid imagery and sensory details.
Use more dynamic language and varied sentence structure.
Incorporate metaphors that align with {persona} characteristics.
Enhance emotional resonance while maintaining clarity."""

    def _generate_general_critique(self, draft: str, persona: str) -> str:
        """Generate general improvement critique"""
        return f"""Strengthen the core message.
Improve flow and transitions between ideas.
Ensure alignment with {persona} voice and tone.
Add specific examples where appropriate."""


class MultiExpertMerger:
    """Main merger class coordinating helpers and templates"""

    def __init__(self):
        self.helpers = [
            HelperCritique("ConciseEditor", max_tokens=120),
            HelperCritique("CreativeEnhancer", max_tokens=120),
            HelperCritique("GeneralReviewer", max_tokens=120),
        ]
        self.default_time_budget_ms = 1500
        self.default_template = "persona_preserving"

    async def compose(self, prompt: str, persona: str,
                     tone_policy: Optional[List[str]] = None,
                     budgets: Optional[Dict[str, Any]] = None
                     ) -> Dict[str, Any]:
        """Main composition method"""
        start_time = time.time()

        # Parse budgets
        time_budget = budgets.get("time_ms", self.default_time_budget_ms) if budgets else self.default_time_budget_ms
        helper_limit = budgets.get("max_helpers", len(self.helpers)) if budgets else len(self.helpers)
        template_name = budgets.get("template", self.default_template) if budgets else self.default_template

        # Generate critiques from helpers
        critiques = []
        helpers_used = 0
        total_tokens = 0

        for helper in self.helpers[:helper_limit]:
            try:
                critique = await helper.generate_critique(
                    prompt, persona, time_budget // helper_limit)
                critiques.append(critique)
                helpers_used += 1
                total_tokens += len(critique) // 4  # Rough token approximation

            except TimeoutError:
                continue  # Skip helpers that exceed time budget
            except Exception as e:
                continue  # Skip failed helpers

        # Get merge template
        template = get_merge_template(template_name)

        # Merge with template
        final_text = template.merge(prompt, critiques, persona,
                                   tone_policy or [])

        processing_time = (time.time() - start_time) * 1000

        return {
            "final_text": final_text,
            "processing_time_ms": processing_time,
            "helpers_used": helpers_used,
            "tokens_used": total_tokens
        }


# Global merger instance
merger = MultiExpertMerger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Hidden Multi-Expert Merger Service starting...")
    yield
    # Shutdown
    print("Hidden Multi-Expert Merger Service shutting down...")


app = FastAPI(
    title="Hidden Multi-Expert Merger",
    description="Service for composing text with helper critiques",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "hidden-multi-expert-merger"}


@app.post("/compose", response_model=ComposeResponse)
async def compose_text(request: ComposeRequest, background_tasks: BackgroundTasks):
    """Compose final text from draft with helper critiques"""
    try:
        result = await merger.compose(
            request.prompt,
            request.persona,
            request.tone_policy,
            request.budgets
        )

        return ComposeResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Composition failed: {str(e)}")


@app.get("/templates")
async def list_templates():
    """List available merge templates"""
    return {
        "templates": ["persona_preserving", "concise_executive", "creative_enhancement"],
        "default": "persona_preserving"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8104)
