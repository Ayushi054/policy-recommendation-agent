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

import json
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("myscheme-mcp")

# Mock database of schemes
SCHEMES_DB = {
    "ayushman_bharat": {
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "sector": "healthcare",
        "state": "All India",
        "description": "Provides free health cover of Rs. 5 Lakh per family per year for secondary and tertiary care hospitalization to over 12 crore poor and vulnerable families.",
        "eligibility": "Families identified by the Socio-Economic Caste Census (SECC) 2011 data.",
        "budget": "Rs. 7,200 Crores (FY 2024-25)",
        "ministry": "Ministry of Health and Family Welfare",
    },
    "samagra_shiksha": {
        "name": "Samagra Shiksha Abhiyan",
        "sector": "education",
        "state": "All India",
        "description": "An overarching programme for the school education sector extending from pre-school to class 12, aiming to ensure inclusive and equitable quality education.",
        "eligibility": "All government schools and students enrolled in pre-school to class 12.",
        "budget": "Rs. 37,500 Crores (FY 2024-25)",
        "ministry": "Ministry of Education",
    },
    "pm_kisan": {
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "sector": "agriculture",
        "state": "All India",
        "description": "An income support scheme providing Rs. 6,000 per year in three equal installments directly to the bank accounts of all landholding farmers' families.",
        "eligibility": "All landholding farmer families across the country (with certain exclusion criteria).",
        "budget": "Rs. 60,000 Crores (FY 2024-25)",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
    },
    "pmay_u": {
        "name": "Pradhan Mantri Awas Yojana - Urban (PMAY-U)",
        "sector": "housing",
        "state": "All India",
        "description": "A mission to provide all-weather pucca houses to all eligible beneficiaries in urban areas.",
        "eligibility": "Economically Weaker Section (EWS), Low Income Group (LIG), and Middle Income Group (MIG) families.",
        "budget": "Rs. 26,170 Crores (FY 2024-25)",
        "ministry": "Ministry of Housing and Urban Affairs",
    },
    "bihar_student_credit_card": {
        "name": "Bihar Student Credit Card Scheme",
        "sector": "youth",
        "state": "Bihar",
        "description": "Provides education loan up to Rs. 4 Lakh at very low interest rates (1% for women/disabled/transgender, 4% for others) to students of Bihar for pursuing higher education.",
        "eligibility": "12th pass students who are residents of Bihar and aged 15-25 years.",
        "budget": "Rs. 500 Crores",
        "ministry": "Department of Education, Government of Bihar",
    },
}


@mcp.tool()
def search_schemes(query: str = "", sector: str = "", state: str = "") -> str:
    """
    Search for central or state government schemes based on query, sector, or state.

    Args:
        query: General text query to match against name or description.
        sector: Sector filter (e.g., healthcare, education, agriculture, housing, youth).
        state: State filter (e.g., Bihar, All India).
    """
    results = []
    q = query.lower()
    sec = sector.lower()
    st = state.lower()

    for key, scheme in SCHEMES_DB.items():
        # Sector check
        if sec and scheme["sector"].lower() != sec:
            continue
        # State check
        if st and scheme["state"].lower() != st and scheme["state"].lower() != "all india":
            continue
        # Query text match
        if q:
            match_name = q in scheme["name"].lower()
            match_desc = q in scheme["description"].lower()
            if not (match_name or match_desc):
                continue

        results.append(scheme)

    return json.dumps(results, indent=2)


@mcp.tool()
def get_scheme_details(scheme_name: str) -> str:
    """
    Retrieve full details for a specific scheme by name.

    Args:
        scheme_name: The name or partial name of the scheme.
    """
    target = scheme_name.lower()
    for key, scheme in SCHEMES_DB.items():
        if target in scheme["name"].lower() or target in key.lower().replace("_", " "):
            return json.dumps(scheme, indent=2)
    return json.dumps({"error": f"Scheme '{scheme_name}' not found in database."}, indent=2)


@mcp.tool()
def identify_gaps(sector: str, state: str, problem_statement: str) -> str:
    """
    Identify policy and implementation gaps by matching user problem statements
    against standard guidelines and typical government scheme features.

    Args:
        sector: Sector domain being analyzed (e.g. education, healthcare).
        state: Target State or UT (e.g. Bihar, Maharashtra).
        problem_statement: The specific problem described by the user.
    """
    # Fetch schemes in this sector/state
    related_schemes_json = search_schemes(sector=sector, state=state)
    related_schemes = json.loads(related_schemes_json)

    # Perform analysis of gaps based on problem statement keywords
    gaps = []
    prob_lower = problem_statement.lower()

    if not related_schemes:
        gaps.append(f"No active schemes found in the '{sector}' sector for {state}.")
    else:
        gaps.append(f"Analyzing issues against {len(related_schemes)} active scheme(s).")

    # Custom heuristics for common issues
    if "infrastructure" in prob_lower or "building" in prob_lower or "water" in prob_lower:
        gaps.append("Physical infrastructure and basic amenities (like water/sanitation) are underserved in rural areas.")
    if "awareness" in prob_lower or "reach" in prob_lower or "illiteracy" in prob_lower:
        gaps.append("Information asymmetry and low public outreach prevent eligible beneficiaries from enrolling.")
    if "corruption" in prob_lower or "leakage" in prob_lower or "middlemen" in prob_lower:
        gaps.append("Direct benefit transfer (DBT) implementation and digital verification gaps exist.")
    if "fund" in prob_lower or "budget" in prob_lower or "cost" in prob_lower:
        gaps.append("Insufficient local budget utilization and delays in fund disbursement from Central to State agencies.")

    if len(gaps) <= 1:
        gaps.append("General governance, tracking, and capacity building gaps at the district/block level.")

    analysis = {
        "sector": sector,
        "state": state,
        "related_schemes_count": len(related_schemes),
        "potential_gaps": gaps,
        "recommendation_priorities": [
            "Establish unified digital dashboard for tracking.",
            "Formulate specific state-sponsored auxiliary scheme.",
            "Introduce localized community outreach champions."
        ]
    }

    return json.dumps(analysis, indent=2)


if __name__ == "__main__":
    mcp.run()
