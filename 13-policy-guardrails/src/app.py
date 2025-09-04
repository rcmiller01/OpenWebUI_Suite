"""
Policy Guardrails Service - Deterministic Policy Enforcement
Provides lane-specific prompt engineering, validation, and repair mechanisms
"""

import json
import re
import logging
from typing import Dict, List, Any, Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jsonschema import validate as validate_json_schema, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Policy Guardrails Service",
    description="Deterministic policy enforcement for OpenWebUI Suite",
    version="1.0.0"
)

# Lane configurations
LANE_CONFIGS = {
    "technical": {
        "template": """You are a technical assistant. Follow these guidelines:

1. Provide accurate, well-structured technical information
2. Include code examples when relevant
3. Explain concepts clearly and concisely
4. Follow security best practices
5. Use proper formatting for code and data structures

Response must conform to this JSON schema:
{schema}

Current context:
- User affect: {emotion} (intensity: {intensity})
- Drive state: Energy {energy}, Focus {focus}""",
        "schema": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Clear explanation of the technical concept"
                },
                "code": {
                    "type": "string",
                    "description": "Code example if applicable"
                },
                "best_practices": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of best practices"
                },
                "security_notes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Security considerations"
                }
            },
            "required": ["explanation"]
        },
        "filters": ["security", "syntax", "imports"],
        "max_length": 2000
    },
    "emotional": {
        "template": """You are an empathetic assistant providing
emotional support.

Guidelines:
1. Show genuine empathy and understanding
2. Keep responses to 3-5 sentences
3. Use warm, supportive language
4. Validate feelings without judgment
5. Offer gentle guidance when appropriate

Current emotional context:
- User affect: {emotion} (intensity: {intensity})
- Drive state: Energy {energy}, Focus {focus}""",
        "schema": {
            "type": "object",
            "properties": {
                "acknowledgment": {
                    "type": "string",
                    "description": "Acknowledgment of user's feelings"
                },
                "support": {
                    "type": "string",
                    "description": "Supportive message"
                },
                "guidance": {
                    "type": "string",
                    "description": "Gentle guidance if appropriate"
                }
            },
            "additionalProperties": False
        },
        "filters": ["length", "tone", "appropriateness"],
        "max_sentences": 5
    },
    "creative": {
        "template": """You are a creative assistant for writing and ideation.

Guidelines:
1. Encourage original and imaginative thinking
2. Provide engaging and compelling content
3. Maintain narrative coherence and flow
4. Use descriptive and vivid language
5. Adapt to the user's creative goals

Current context:
- User affect: {emotion} (intensity: {intensity})
- Drive state: Energy {energy}, Focus {focus}""",
        "schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Main creative concept or idea"
                },
                "development": {
                    "type": "string",
                    "description": "Further development of the concept"
                },
                "elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key creative elements"
                }
            },
            "required": ["concept"]
        },
        "filters": ["originality", "coherence", "engagement"],
        "max_length": 1500
    },
    "analytical": {
        "template": """You are an analytical assistant for reasoning
and problem-solving.

Guidelines:
1. Break down complex problems systematically
2. Provide evidence-based analysis
3. Consider multiple perspectives
4. Draw logical conclusions
5. Present findings clearly and objectively

Current context:
- User affect: {emotion} (intensity: {intensity})
- Drive state: Energy {energy}, Focus {focus}""",
        "schema": {
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "string",
                    "description": "Step-by-step analysis"
                },
                "evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Supporting evidence"
                },
                "conclusion": {
                    "type": "string",
                    "description": "Logical conclusion"
                },
                "alternatives": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Alternative considerations"
                }
            },
            "required": ["analysis", "conclusion"]
        },
        "filters": ["logic", "evidence", "objectivity"],
        "max_length": 1800
    }
}

# Filter definitions
FILTER_CONFIGS = {
    "security": {
        "patterns": [
            r"eval\s*\(",
            r"exec\s*\(",
            r"password\s*=\s*['\"][^'\"]*['\"]",
            r"import\s+os\s*;?\s*os\.system",
            r"subprocess\.(call|Popen|run)"
        ],
        "severity": "high",
        "description": "Security vulnerability detected"
    },
    "syntax": {
        "patterns": [
            r"def\s+\w+\s*\([^)]*$",  # Incomplete function definition
            r"class\s+\w+\s*:\s*$",   # Incomplete class definition
            r"if\s+.*:\s*$",          # Incomplete if statement
            r"for\s+.*:\s*$",         # Incomplete for loop
        ],
        "severity": "medium",
        "description": "Syntax error detected"
    },
    "imports": {
        "patterns": [
            r"import\s+\w+",
            r"from\s+\w+\s+import"
        ],
        "severity": "low",
        "description": "Import statement validation"
    },
    "length": {
        "max_sentences": 5,
        "severity": "medium",
        "description": "Response length exceeds limit"
    },
    "tone": {
        "patterns": [
            r"\b(hate|stupid|idiot|dumb)\b",
            r"\b(you.*should|you.*must)\b.*!",
        ],
        "severity": "high",
        "description": "Inappropriate tone detected"
    },
    "appropriateness": {
        "patterns": [
            r"\b(hate|stupid|idiot|dumb|moron)\b",
            r"\b(die|kill|hurt)\b.*\b(yourself|someone)\b"
        ],
        "severity": "high",
        "description": "Inappropriate content detected"
    },
    "originality": {
        "patterns": [
            r"This is a copy of",
            r"Plagiarized from",
            r"Stolen content"
        ],
        "severity": "high",
        "description": "Potential plagiarism detected"
    },
    "coherence": {
        "patterns": [
            r"\.\s*[A-Z]",  # Missing space after period
            r"\?\s*[a-z]",  # Lowercase after question mark
            r"!\s*[a-z]",   # Lowercase after exclamation
        ],
        "severity": "low",
        "description": "Coherence issue detected"
    },
    "engagement": {
        "patterns": [
            r"\b(boring|dull|uninteresting)\b",
            r"no\s+one\s+cares",
            r"whatever"
        ],
        "severity": "medium",
        "description": "Low engagement content detected"
    },
    "logic": {
        "patterns": [
            r"therefore.*but",
            r"however.*therefore",
            r"because.*although"
        ],
        "severity": "medium",
        "description": "Logical inconsistency detected"
    },
    "evidence": {
        "patterns": [
            r"because\s+I\s+(think|feel|believe)",
            r"obviously",
            r"clearly"
        ],
        "severity": "low",
        "description": "Weak evidence detected"
    },
    "objectivity": {
        "patterns": [
            r"I\s+personally\s+(think|believe|feel)",
            r"In\s+my\s+opinion",
            r"This\s+is\s+the\s+best"
        ],
        "severity": "low",
        "description": "Subjective language detected"
    }
}

# Pydantic models
class AffectData(BaseModel):
    emotion: str
    intensity: float


class DriveData(BaseModel):
    energy: float
    focus: float


class PolicyApplyRequest(BaseModel):
    lane: str
    system: str
    user: str
    affect: AffectData
    drive: DriveData


class PolicyValidateRequest(BaseModel):
    lane: str
    text: str


class ValidatorConfig(BaseModel):
    type: str
    schema: Union[Dict[str, Any], None] = None
    pattern: Union[str, None] = None
    description: str

    class Config:
        arbitrary_types_allowed = True


class PolicyApplyResponse(BaseModel):
    system_final: str
    validators: List[ValidatorConfig]


class RepairItem(BaseModel):
    type: str
    issue: str
    repair: str
    severity: str


class PolicyValidateResponse(BaseModel):
    ok: bool
    repairs: List[RepairItem]


# Core functions
def apply_template(template: str, **kwargs) -> str:
    """Apply template with variable substitution"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning(f"Missing template variable: {e}")
        return template

def validate_json(text: str, schema: Dict[str, Any]) -> bool:
    """Validate JSON text against schema"""
    try:
        data = json.loads(text)
        validate_json_schema(data, schema)
        return True
    except (json.JSONDecodeError, ValidationError) as e:
        logger.info(f"JSON validation failed: {e}")
        return False

def apply_filters(text: str, filters: List[str]) -> List[Dict[str, Any]]:
    """Apply content filters and return issues"""
    issues = []
    for filter_name in filters:
        if filter_name not in FILTER_CONFIGS:
            continue

        filter_config = FILTER_CONFIGS[filter_name]

        if "patterns" in filter_config:
            for pattern in filter_config["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    issues.append({
                        "type": "filter",
                        "issue": filter_config["description"],
                        "severity": filter_config["severity"]
                    })
                    break  # Only report once per filter type

        elif filter_name == "length":
            # Count sentences (rough approximation)
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            if len(sentences) > filter_config["max_sentences"]:
                issues.append({
                    "type": "filter",
                    "issue": filter_config["description"],
                    "severity": filter_config["severity"]
                })

    return issues

def generate_repairs(issues: List[Dict[str, Any]], lane: str) -> List[Dict[str, Any]]:
    """Generate repair suggestions for validation issues"""
    repairs = []
    for issue in issues:
        repair_suggestion = get_repair_suggestion(issue, lane)
        repairs.append({
            "type": issue["type"],
            "issue": issue["issue"],
            "repair": repair_suggestion,
            "severity": issue["severity"]
        })
    return repairs

def get_repair_suggestion(issue: Dict[str, Any], lane: str) -> str:
    """Get specific repair suggestion based on issue and lane"""
    issue_type = issue.get("issue", "").lower()

    if "security" in issue_type:
        return "Remove or replace insecure code patterns (eval, exec, password literals, etc.)"
    elif "syntax" in issue_type:
        return "Fix syntax errors in code examples"
    elif "length" in issue_type:
        if lane == "emotional":
            return "Reduce response to 3-5 sentences"
        else:
            return "Shorten content to meet length requirements"
    elif "tone" in issue_type:
        return "Use more supportive and appropriate language"
    elif "appropriateness" in issue_type:
        return "Remove inappropriate or harmful content"
    elif "originality" in issue_type:
        return "Ensure content is original and not plagiarized"
    elif "coherence" in issue_type:
        return "Improve sentence structure and punctuation"
    elif "engagement" in issue_type:
        return "Make content more engaging and compelling"
    elif "logic" in issue_type:
        return "Fix logical inconsistencies in reasoning"
    elif "evidence" in issue_type:
        return "Provide stronger evidence and avoid unsubstantiated claims"
    elif "objectivity" in issue_type:
        return "Use more objective language and avoid personal opinions"
    else:
        return "Review and revise content according to lane guidelines"

# API endpoints
@app.post("/policy/apply", response_model=PolicyApplyResponse)
async def apply_policy(request: PolicyApplyRequest):
    """Apply policy transformations to generate final system prompts and validators"""
    try:
        if request.lane not in LANE_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown lane: {request.lane}")

        lane_config = LANE_CONFIGS[request.lane]

        # Apply template
        system_final = apply_template(
            lane_config["template"],
            schema=json.dumps(lane_config["schema"], indent=2),
            emotion=request.affect.emotion,
            intensity=request.affect.intensity,
            energy=request.drive.energy,
            focus=request.drive.focus
        )

        # Build validators
        validators = []

        # Schema validator
        validators.append(ValidatorConfig(
            type="schema",
            schema=lane_config["schema"],
            description=f"JSON schema validation for {request.lane} responses"
        ))

        # Filter validators
        for filter_name in lane_config["filters"]:
            if filter_name in FILTER_CONFIGS:
                filter_config = FILTER_CONFIGS[filter_name]
                if "patterns" in filter_config:
                    for pattern in filter_config["patterns"]:
                        validators.append(ValidatorConfig(
                            type="filter",
                            pattern=pattern,
                            description=filter_config["description"]
                        ))

        return PolicyApplyResponse(
            system_final=system_final,
            validators=validators
        )

    except Exception as e:
        logger.error(f"Error applying policy: {e}")
        raise HTTPException(status_code=500, detail="Policy application failed")

@app.post("/policy/validate", response_model=PolicyValidateResponse)
async def validate_content(request: PolicyValidateRequest):
    """Validate content against lane policies and provide repair suggestions"""
    try:
        if request.lane not in LANE_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown lane: {request.lane}")

        lane_config = LANE_CONFIGS[request.lane]

        # Apply filters
        issues = apply_filters(request.text, lane_config["filters"])

        # Check schema if content appears to be JSON
        if request.text.strip().startswith("{") and request.text.strip().endswith("}"):
            if not validate_json(request.text, lane_config["schema"]):
                issues.append({
                    "type": "schema",
                    "issue": "Content does not match required JSON schema",
                    "severity": "high"
                })

        # Check length
        if len(request.text) > lane_config.get("max_length", 2000):
            issues.append({
                "type": "length",
                "issue": f"Content exceeds maximum length of {lane_config['max_length']} characters",
                "severity": "medium"
            })

        # Generate repairs
        repairs = generate_repairs(issues, request.lane)

        return PolicyValidateResponse(
            ok=len(issues) == 0,
            repairs=repairs
        )

    except Exception as e:
        logger.error(f"Error validating content: {e}")
        raise HTTPException(status_code=500, detail="Content validation failed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "lanes_loaded": len(LANE_CONFIGS),
        "filters_loaded": len(FILTER_CONFIGS)
    }

@app.get("/lanes")
async def get_lanes():
    """Get available policy lanes"""
    return {
        "lanes": list(LANE_CONFIGS.keys()),
        "details": LANE_CONFIGS
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8113)
