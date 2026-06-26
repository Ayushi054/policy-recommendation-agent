# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
from dotenv import load_dotenv
from google.adk.apps import App, ResumabilityConfig
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.adk.events.request_input import RequestInput
from google.adk.workflow import Workflow, node
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def _get_input(val):
    if isinstance(val, dict):
        return val.get("response") or val.get("text") or list(val.values())[0]
    return val


@node(rerun_on_resume=True)
async def collect_user_profile(ctx: Context, node_input=None):
    """Collects user role, target state, sector domain, and problem statement."""
    role = ctx.state.get("user_role")
    domain = ctx.state.get("user_domain")
    state = ctx.state.get("target_state")
    problem = ctx.state.get("problem_statement")

    # Step 1: Ask role
    if not role:
        if ctx.resume_inputs and "ask_role" in ctx.resume_inputs:
            role = _get_input(ctx.resume_inputs["ask_role"])
            yield Event(actions=EventActions(state_delta={"user_role": role}))
        else:
            yield RequestInput(
                interrupt_id="ask_role",
                message="What is your role? (Policymaker / Researcher / NGO Worker / Citizen)",
            )
            return

    # Step 2: Ask state
    if not state:
        if ctx.resume_inputs and "ask_state" in ctx.resume_inputs:
            state = _get_input(ctx.resume_inputs["ask_state"])
            yield Event(actions=EventActions(state_delta={"target_state": state}))
        else:
            yield RequestInput(
                interrupt_id="ask_state",
                message="Which state are you analyzing? (e.g., Maharashtra, Bihar, All India)",
            )
            return

    # Step 3: Ask domain
    if not domain:
        if ctx.resume_inputs and "ask_domain" in ctx.resume_inputs:
            domain = _get_input(ctx.resume_inputs["ask_domain"])
            yield Event(actions=EventActions(state_delta={"user_domain": domain}))
        else:
            yield RequestInput(
                interrupt_id="ask_domain",
                message="Which sector? (education / healthcare / agriculture / women / youth / housing)",
            )
            return

    # Step 4: Ask problem
    if not problem:
        if ctx.resume_inputs and "ask_problem" in ctx.resume_inputs:
            problem = _get_input(ctx.resume_inputs["ask_problem"])
            yield Event(actions=EventActions(state_delta={"problem_statement": problem}))
        else:
            yield RequestInput(
                interrupt_id="ask_problem",
                message="Describe the problem you want to address (max 200 words):",
            )
            return

    yield Event(actions=EventActions(state_delta={
        "user_role": role,
        "user_domain": domain,
        "target_state": state,
        "problem_statement": problem,
        "profile_complete": True
    }))


async def security_check(ctx: Context, node_input=None):
    """Screens input for PII and prompt injection"""
    problem = ctx.state.get("problem_statement", "")

    # Prompt injection patterns
    injection_patterns = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
        r"bypass\s+(all\s+)?rules",
        r"you\s+are\s+now\s+a",
        r"forget\s+(everything|all)",
        r"override\s+(safety|guidelines|rules)",
        r"auto.?approve",
        r"jailbreak",
    ]

    for pattern in injection_patterns:
        if re.search(pattern, problem, re.IGNORECASE):
            yield Event(actions=EventActions(state_delta={
                "security_status": "BLOCKED",
                "security_warning": "Prompt injection detected!"
            }))
            return

    # PII Redaction
    pii_patterns = {
        "Aadhaar": r"\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b",
        "PAN": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        "Phone": r"\b[6-9]\d{9}\b",
        "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }

    cleaned = problem
    warnings = []
    for pii_type, pattern in pii_patterns.items():
        if re.search(pattern, cleaned):
            cleaned = re.sub(pattern, f"[{pii_type} REDACTED]", cleaned)
            warnings.append(f"{pii_type} redacted")

    yield Event(actions=EventActions(state_delta={
        "security_status": "PASSED",
        "cleaned_problem": cleaned,
        "security_warnings": warnings
    }))


async def analyze_gaps(ctx: Context, node_input=None):
    """Analyzes policy gaps using Gemini LLM"""
    security_status = ctx.state.get("security_status", "")
    if security_status == "BLOCKED":
        yield Event(actions=EventActions(state_delta={
            "gap_analysis": "Blocked due to security policy."
        }))
        return

    domain = ctx.state.get("user_domain", "")
    state = ctx.state.get("target_state", "")
    problem = ctx.state.get("cleaned_problem", ctx.state.get("problem_statement", ""))

    prompt = f"""
    You are an expert Indian government policy analyst.
    
    Analyze the following and identify policy gaps:
    State/UT: {state}
    Sector: {domain}
    Problem Statement: {problem}
    
    Provide:
    1. Current government schemes addressing this area
    2. Key gaps in existing policies
    3. Underserved populations
    4. Priority areas for new policy intervention
    
    Be specific to Indian context. Format as structured gap analysis report.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    gap_analysis = response.choices[0].message.content

    yield Event(actions=EventActions(state_delta={
        "gap_analysis": gap_analysis
    }))

    yield Event(
        content={
            "role": "model",
            "parts": [{"text": f"📊 **Gap Analysis Complete!**\n\n{gap_analysis}"}]
        }
    )


async def generate_recommendation(ctx: Context, node_input=None):
    """Generates structured policy proposal using Gemini LLM"""
    security_status = ctx.state.get("security_status", "")
    if security_status == "BLOCKED":
        yield Event(actions=EventActions(state_delta={
            "policy_recommendation": "Blocked due to security policy."
        }))
        return

    gap_analysis = ctx.state.get("gap_analysis", "")
    domain = ctx.state.get("user_domain", "")
    state = ctx.state.get("target_state", "")

    prompt = f"""
    You are an expert Indian government policy designer.
    
    Based on this gap analysis, create a detailed policy proposal:
    {gap_analysis}
    
    Generate a complete policy proposal with:
    1. SCHEME NAME (creative Hindi/English name)
    2. MINISTRY/DEPARTMENT
    3. SCHEME TYPE (Central/State/Centrally Sponsored)
    4. OBJECTIVES (Primary + 3 Secondary)
    5. TARGET BENEFICIARIES with eligibility criteria
    6. KEY COMPONENTS (5 main components)
    7. BUDGET ESTIMATE in Indian Rupees (Crore)
    8. IMPLEMENTATION PLAN (Phase 1, 2, 3)
    9. EXPECTED OUTCOMES (measurable)
    10. SUCCESS METRICS / KPIs
    11. SIMILAR SUCCESSFUL SCHEMES from India
    
    Make it realistic and aligned with India's constitutional framework.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    recommendation = response.choices[0].message.content

    yield Event(actions=EventActions(state_delta={
        "policy_recommendation": recommendation
    }))

    yield Event(
        content={
            "role": "model",
            "parts": [{"text": f"📋 **Policy Recommendation Generated!**\n\n{recommendation}"}]
        }
    )


@node(rerun_on_resume=True)
async def human_review(ctx: Context, node_input=None):
    """Policymaker reviews and approves/rejects"""
    security_status = ctx.state.get("security_status", "")
    decision = ctx.state.get("review_decision")

    # If blocked by security
    if security_status == "BLOCKED":
        warning = ctx.state.get("security_warning", "")
        if ctx.resume_inputs and "security_decision" in ctx.resume_inputs:
            decision_val = _get_input(ctx.resume_inputs["security_decision"])
            yield Event(actions=EventActions(state_delta={
                "review_decision": "rejected",
                "review_comments": f"Blocked: {warning} (User Acknowledged: {decision_val})"
            }))
        else:
            yield RequestInput(
                interrupt_id="security_decision",
                message=f"⚠️ SECURITY ALERT: {warning}\nThis request has been blocked. Acknowledged? (yes/no)",
            )
        return

    # Normal review
    if not decision:
        recommendation = ctx.state.get("policy_recommendation", "")
        preview = recommendation[:300] + "..." if len(recommendation) > 300 else recommendation

        if ctx.resume_inputs and "review_decision" in ctx.resume_inputs:
            raw_input = _get_input(ctx.resume_inputs["review_decision"])
            # Parse comments if formatted as "approve: comment" or "reject: comment"
            if ":" in raw_input:
                decision_part, comments_part = raw_input.split(":", 1)
                decision = decision_part.strip()
                comments = comments_part.strip()
            else:
                decision = raw_input.strip()
                comments = "No comments provided."

            yield Event(actions=EventActions(state_delta={
                "review_decision": decision,
                "review_comments": comments
            }))
        else:
            yield RequestInput(
                interrupt_id="review_decision",
                message=f"📋 Policy Proposal Preview:\n{preview}\n\nDo you APPROVE or REJECT? (approve/reject)",
            )
            return


async def finalize_output(ctx: Context, node_input=None):
    """Prepares final output"""
    decision = ctx.state.get("review_decision", "").lower()
    recommendation = ctx.state.get("policy_recommendation", "")
    comments = ctx.state.get("review_comments", "")
    warnings = ctx.state.get("security_warnings", [])

    if "approve" in decision:
        final_text = f"""
✅ **POLICY PROPOSAL APPROVED!**

{recommendation}

**Reviewer Comments:** {comments}
**Security Notes:** {', '.join(warnings) if warnings else 'None'}

**Next Steps:**
1. Submit to Ministry for formal review
2. Conduct stakeholder consultation  
3. Draft cabinet note
4. Budget allocation planning
"""
    else:
        final_text = f"""
❌ **PROPOSAL REJECTED**

**Reason:** {comments}
**Security Notes:** {', '.join(warnings) if warnings else 'None'}

**Next Steps:**
1. Revise based on feedback
2. Conduct additional research
3. Resubmit for review
"""

    yield Event(
        content={
            "role": "model",
            "parts": [{"text": final_text}]
        },
        output=final_text
    )


# Build Workflow Graph
root_agent = Workflow(
    name="policy_recommendation_workflow",
    edges=[
        ("START", collect_user_profile),
        (collect_user_profile, security_check),
        (security_check, analyze_gaps),
        (analyze_gaps, generate_recommendation),
        (generate_recommendation, human_review),
        (human_review, finalize_output),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True),
)