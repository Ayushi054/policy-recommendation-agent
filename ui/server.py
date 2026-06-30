import os
import re
import json
import uuid
import datetime
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from parent or current dir
load_dotenv()

# Determine directory paths relative to server.py
UI_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=UI_DIR, static_url_path="")

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def security_check(problem):
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
            return "BLOCKED", "Prompt injection detected!", []

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

    return "PASSED", cleaned, warnings

@app.route("/")
def serve_index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/api/generate", methods=["POST"])
def generate():
    if not client:
        return jsonify({"error": "GROQ_API_KEY is not set on the server. Please check your .env file."}), 500
        
    data = request.json or {}
    role = data.get("role")
    state = data.get("state")
    sector = data.get("sector")
    focus = data.get("focus")
    problem = data.get("problem", "")
    
    if not all([role, state, sector, focus, problem.strip()]):
        return jsonify({"error": "Missing required fields."}), 400
        
    # Run security check
    status, cleaned_problem, warnings = security_check(problem)
    if status == "BLOCKED":
        return jsonify({
            "security_status": "BLOCKED",
            "security_message": cleaned_problem,
            "gap_analysis": "Blocked due to security policy check.",
            "policy_recommendation": "Blocked due to security policy check."
        })
        
    # 1. Generate Gap Analysis
    gap_prompt = f"""
    You are an expert Indian government policy analyst. The user role is {role}.
    
    Analyze the following and identify policy gaps:
    State/UT: {state}
    Sector: {sector}
    Priority Focus Group: {focus}
    Problem Statement: {cleaned_problem}
    
    Provide:
    1. Current government schemes addressing this area
    2. Key gaps in existing policies
    3. Underserved populations
    4. Priority areas for new policy intervention
    
    Be specific to Indian context. Format as structured gap analysis report.
    """
    
    try:
        gap_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": gap_prompt}
            ]
        )
        gap_analysis = gap_response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": f"Gap analysis generation failed: {str(e)}"}), 500
        
    # 2. Generate Policy Proposal
    rec_prompt = f"""
    You are an expert Indian government policy designer. The user role is {role}.
    
    Based on this gap analysis, create a detailed policy proposal focusing on {focus} in {state}:
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
    
    try:
        rec_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": rec_prompt}
            ]
        )
        recommendation = rec_response.choices[0].message.content
    except Exception as e:
        return jsonify({
            "security_status": "PASSED",
            "warnings": warnings,
            "gap_analysis": gap_analysis,
            "policy_recommendation": f"Recommendation generation failed: {str(e)}"
        })
        
    return jsonify({
        "security_status": "PASSED",
        "warnings": warnings,
        "gap_analysis": gap_analysis,
        "policy_recommendation": recommendation
    })

def save_proposal(filename, data):
    filepath = os.path.join(UI_DIR, filename)
    proposals = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    proposals = json.loads(content)
                    if not isinstance(proposals, list):
                        proposals = [proposals]
        except Exception as e:
            app.logger.error(f"Error reading {filename}: {e}")
    proposals.append(data)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposals, f, indent=2, ensure_ascii=False)
    except Exception as e:
        app.logger.error(f"Error writing {filename}: {e}")

@app.route("/api/approve", methods=["POST"])
def approve():
    data = request.json or {}
    proposal_text = data.get("policy_proposal", "")
    
    if not proposal_text.strip():
        return jsonify({"error": "Missing required field: policy_proposal."}), 400
        
    proposal_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.datetime.now().isoformat()
    
    # Log the approval with timestamp
    app.logger.info(f"[{timestamp}] Proposal APPROVED: ID={proposal_id}")
    print(f"[{timestamp}] Proposal APPROVED: ID={proposal_id}")
    
    # Save approved proposal to approved_proposals.json
    record = {
        "proposal_id": proposal_id,
        "policy_proposal": proposal_text,
        "timestamp": timestamp
    }
    save_proposal("approved_proposals.json", record)
    
    return jsonify({
        "status": "approved",
        "message": "Proposal approved and saved for ministry submission",
        "proposal_id": proposal_id,
        "timestamp": timestamp,
        "next_steps": [
            "Submit to Ministry for formal review",
            "Conduct stakeholder consultation",
            "Draft cabinet note",
            "Budget allocation planning"
        ]
    })

@app.route("/api/reject", methods=["POST"])
def reject():
    data = request.json or {}
    proposal_text = data.get("policy_proposal", "")
    rejection_reason = data.get("rejection_reason", "")
    
    if not proposal_text.strip():
        return jsonify({"error": "Missing required field: policy_proposal."}), 400
    if not rejection_reason.strip():
        return jsonify({"error": "Missing required field: rejection_reason."}), 400
        
    proposal_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.datetime.now().isoformat()
    
    # Log the rejection with timestamp and reason
    app.logger.info(f"[{timestamp}] Proposal REJECTED: ID={proposal_id}, Reason={rejection_reason}")
    print(f"[{timestamp}] Proposal REJECTED: ID={proposal_id}, Reason={rejection_reason}")
    
    # Save to rejected_proposals.json
    record = {
        "proposal_id": proposal_id,
        "policy_proposal": proposal_text,
        "rejection_reason": rejection_reason,
        "timestamp": timestamp
    }
    save_proposal("rejected_proposals.json", record)
    
    return jsonify({
        "status": "rejected",
        "message": "Proposal rejected and logged for revision",
        "reason": rejection_reason,
        "timestamp": timestamp,
        "next_steps": [
            "Revise based on feedback",
            "Conduct additional research",
            "Resubmit for review"
        ]
    })

if __name__ == "__main__":
    # Start on port 8000
    app.run(host="127.0.0.1", port=8000, debug=True)
