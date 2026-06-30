import os
import re
import gradio as gr
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is not set in the environment or .env file.")

client = Groq(api_key=api_key)

INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
    "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry", "All India"
]

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

def generate_policy(role, target_state, sector, problem_statement):
    if not role or not target_state or not sector or not problem_statement.strip():
        error_md = """
        <div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 1rem; border-radius: 8px; color: #fca5a5;">
            <strong>⚠️ Input Required:</strong> Please fill in all fields (Role, State, Sector, and Problem Statement).
        </div>
        """
        return error_md, error_md
    
    # 1. Security Check
    status, cleaned_problem, warnings = security_check(problem_statement)
    if status == "BLOCKED":
        blocked_md = f"""
        <div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 1rem; border-radius: 8px; color: #fca5a5;">
            <strong>❌ Blocked:</strong> {cleaned_problem}
        </div>
        """
        return blocked_md, blocked_md
    
    warning_text = ""
    if warnings:
        warning_text = f"""
        <div style="background-color: rgba(245, 158, 11, 0.2); border: 1px solid #f59e0b; padding: 1rem; border-radius: 8px; color: #fde68a; margin-bottom: 1rem;">
            <strong>⚠️ Security Warning:</strong> {', '.join(warnings)} (Sensitive data redacted for privacy)
        </div>
        """
        
    # 2. Gap Analysis
    gap_prompt = f"""
    You are an expert Indian government policy analyst. The user role is {role}.
    
    Analyze the following and identify policy gaps:
    State/UT: {target_state}
    Sector: {sector}
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
        err_md = f"""
        <div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 1rem; border-radius: 8px; color: #fca5a5;">
            <strong>Error during Gap Analysis:</strong> {str(e)}
        </div>
        """
        return err_md, "N/A"
        
    # 3. Policy Recommendation
    rec_prompt = f"""
    You are an expert Indian government policy designer. The user role is {role}.
    
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
    
    try:
        rec_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": rec_prompt}
            ]
        )
        recommendation = rec_response.choices[0].message.content
    except Exception as e:
        err_md = f"""
        <div style="background-color: rgba(220, 38, 38, 0.2); border: 1px solid #dc2626; padding: 1rem; border-radius: 8px; color: #fca5a5;">
            <strong>Error during Recommendation Generation:</strong> {str(e)}
        </div>
        """
        return gap_analysis, err_md
        
    if warning_text:
        gap_analysis = warning_text + "\n\n" + gap_analysis
        
    return gap_analysis, recommendation

# CSS for a modern, elegant dark theme featuring India's tricolor palette
custom_css = """
body, .gradio-container {
    background-color: #0c0f1d !important;
    color: #e2e8f0 !important;
    font-family: 'Outfit', 'Inter', sans-serif !important;
}

/* Custom Header with Saffron & Green Accent Lines */
.header-container {
    background: linear-gradient(135deg, #13172c 0%, #1e2548 100%);
    border: 1px solid rgba(255, 153, 51, 0.15);
    border-top: 4px solid #FF9933; /* Saffron Top border */
    border-bottom: 4px solid #138808; /* Green Bottom border */
    border-radius: 12px;
    padding: 2rem 1.5rem;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    position: relative;
}
.header-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}
.header-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-top: 0.5rem;
    font-weight: 500;
}

/* Form panels */
.input-panel {
    background-color: #12182c !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}
.output-panel {
    background-color: #12182c !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}

/* Custom styled inputs */
.gr-input, .gr-box, input, textarea, select {
    background-color: #1a203c !important;
    color: #f1f5f9 !important;
    border: 1px solid #313d66 !important;
    border-radius: 8px !important;
}
.gr-input:focus, input:focus, textarea:focus, select:focus {
    border-color: #FF9933 !important;
    box-shadow: 0 0 0 2px rgba(255, 153, 51, 0.2) !important;
}

/* Big Saffron/Navy/Green Glow Button */
.generate-btn {
    background: linear-gradient(135deg, #000080 0%, #1e2a58 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 0.9rem 1.5rem !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255, 153, 51, 0.35) !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 0, 128, 0.4) !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 1rem;
}
.generate-btn:hover {
    background: linear-gradient(135deg, #1e2a58 0%, #314486 100%) !important;
    border-color: #138808 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(30, 42, 88, 0.6) !important;
}
.generate-btn:active {
    transform: translateY(0) !important;
}

/* Output tab styling with custom selected highlights */
.tab-nav button {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    padding: 0.8rem 1.2rem !important;
    border: none !important;
    background: transparent !important;
    transition: all 0.2s ease !important;
}
.tab-nav button.selected {
    color: #ffffff !important;
    border-bottom: 3px solid #FF9933 !important; /* Saffron highlight */
    background-color: rgba(255, 153, 51, 0.08) !important;
}

.output-markdown {
    background-color: #161c36 !important;
    border-left: 4px solid #138808 !important; /* Green highlight on left */
    border-radius: 8px !important;
    padding: 1.5rem !important;
    color: #f1f5f9 !important;
    line-height: 1.7 !important;
}

/* Footer Section */
.footer-container {
    text-align: center;
    margin-top: 3rem;
    padding: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 0.95rem;
    color: #64748b;
}
.footer-text {
    background: linear-gradient(90deg, #FF9933, #ffffff 50%, #138808);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}
"""

# Custom theme overrides for Gradio component styles
theme = gr.themes.Default(
    primary_hue="blue",
    secondary_hue="orange",
    neutral_hue="slate",
).set(
    body_background_fill="#0c0f1d",
    body_background_fill_dark="#0c0f1d",
    block_background_fill="#12182c",
    block_background_fill_dark="#12182c",
    block_border_color="#313d66",
    block_border_color_dark="#313d66",
    button_primary_background_fill="#000080",
    button_primary_background_fill_dark="#000080",
    input_background_fill="#1a203c",
    input_background_fill_dark="#1a203c",
    input_border_color="#313d66",
    input_border_color_dark="#313d66",
    input_placeholder_color="#64748b",
    input_placeholder_color_dark="#64748b"
)

with gr.Blocks() as demo:
    # Header Section
    gr.HTML(
        '''
        <div class="header-container">
            <h1 class="header-title">🏛️ AI Policy & Scheme Recommendation System</h1>
            <p class="header-subtitle">Powered by Google ADK 2.0</p>
        </div>
        '''
    )
    
    with gr.Row():
        # Input Column
        with gr.Column(scale=1, elem_classes=["input-panel"]):
            gr.Markdown("### 📋 Demographics & Problem Profile")
            
            role = gr.Dropdown(
                choices=["Policymaker", "Researcher", "NGO Worker", "Citizen"],
                label="Your Professional Role",
                value="Policymaker",
                info="Identify your target perspective for the proposal"
            )
            
            target_state = gr.Dropdown(
                choices=INDIAN_STATES,
                label="Target State / UT",
                value="All India",
                info="Select the geographical focus area"
            )
            
            sector = gr.Dropdown(
                choices=["Education", "Healthcare", "Agriculture", "Women", "Youth", "Housing"],
                label="Sector / Domain",
                value="Education",
                info="Specify the policy domain sector"
            )
            
            problem_statement = gr.Textbox(
                label="Problem Statement",
                placeholder="Identify the key policy issue, target groups, constraints, and gaps you wish to address...",
                lines=6,
                info="Describe the policy challenge in detail (max 200 words)"
            )
            
            submit_btn = gr.Button(
                "Generate Policy Recommendation", 
                elem_classes=["generate-btn"]
            )
            
        # Output Column
        with gr.Column(scale=2, elem_classes=["output-panel"]):
            gr.Markdown("### 🔍 AI Analysis & Proposal Outputs")
            
            with gr.Tabs():
                with gr.Tab("📊 Gap Analysis"):
                    gap_output = gr.Markdown(
                        value="*Gap analysis results will appear here after you submit the form.*",
                        elem_classes=["output-markdown"]
                    )
                with gr.Tab("📋 Policy Proposal"):
                    rec_output = gr.Markdown(
                        value="*Structured policy proposal will appear here after you submit the form.*",
                        elem_classes=["output-markdown"]
                    )
                    
    # Link Click action with automatic loader/spinner support
    submit_btn.click(
        fn=generate_policy,
        inputs=[role, target_state, sector, problem_statement],
        outputs=[gap_output, rec_output],
        show_progress="full"
    )
    
    # Footer Section
    gr.HTML(
        '''
        <div class="footer-container">
            <p>Built with Google ADK 2.0 | <span class="footer-text">Kaggle Agents for Good</span></p>
        </div>
        '''
    )

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1", 
        server_port=7860,
        theme=theme,
        css=custom_css
    )
