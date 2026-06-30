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
import json
import pytest
from ui.server import app, UI_DIR

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_approve_proposal(client):
    # Ensure file is clean/removed first
    approved_file = os.path.join(UI_DIR, "approved_proposals.json")
    if os.path.exists(approved_file):
        try:
            os.remove(approved_file)
        except OSError:
            pass

    proposal_text = "This is a sample policy proposal for testing."
    response = client.post("/api/approve", json={"policy_proposal": proposal_text})
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "approved"
    assert "proposal_id" in data
    assert data["message"] == "Proposal approved and saved for ministry submission"
    assert len(data["next_steps"]) == 4

    # Verify file was written
    assert os.path.exists(approved_file)
    with open(approved_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
        assert isinstance(saved_data, list)
        assert saved_data[-1]["policy_proposal"] == proposal_text
        assert saved_data[-1]["proposal_id"] == data["proposal_id"]

    # Clean up
    if os.path.exists(approved_file):
        try:
            os.remove(approved_file)
        except OSError:
            pass

def test_reject_proposal(client):
    # Ensure file is clean/removed first
    rejected_file = os.path.join(UI_DIR, "rejected_proposals.json")
    if os.path.exists(rejected_file):
        try:
            os.remove(rejected_file)
        except OSError:
            pass

    proposal_text = "This is a sample policy proposal for rejection testing."
    reason = "Insufficient budget details."
    response = client.post("/api/reject", json={
        "policy_proposal": proposal_text,
        "rejection_reason": reason
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "rejected"
    assert data["reason"] == reason
    assert len(data["next_steps"]) == 3

    # Verify file was written
    assert os.path.exists(rejected_file)
    with open(rejected_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
        assert isinstance(saved_data, list)
        assert saved_data[-1]["policy_proposal"] == proposal_text
        assert saved_data[-1]["rejection_reason"] == reason
        assert "proposal_id" in saved_data[-1]

    # Clean up
    if os.path.exists(rejected_file):
        try:
            os.remove(rejected_file)
        except OSError:
            pass
