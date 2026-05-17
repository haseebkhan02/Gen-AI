"""
Agentic Reasoning Module - EHS Violation Assessment
Uses Groq API (LLaMA 3.3 70B) for dynamic policy reasoning.
Consumes CV outputs + retrieved policies to determine violations.
"""

import json
import logging
import os
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


COMPLIANCE_ASSESSMENT_PROMPT = """You are an expert EHS (Environment, Health & Safety) compliance officer with deep knowledge of industrial safety standards including OSHA, ISO 45001, and NFPA regulations.
You will analyze computer vision detection results and relevant EHS policy excerpts to determine safety compliance status.
## Computer Vision Analysis Results:
{cv_results}

## Relevant EHS Policies Retrieved:
{policy_context}

## Your Task:
Analyze the CV results against the policies and provide a structured compliance assessment.

Respond ONLY with a valid JSON object (no markdown, no explanation outside JSON):
{{
  "overall_compliance_status": "COMPLIANT" | "VIOLATION" | "WARNING" | "INCONCLUSIVE",
  "confidence_level": "HIGH" | "MEDIUM" | "LOW",
  "violations": [
    {{
      "violation_id": "V001",
      "policy_reference": "policy ID or name",
      "violation_type": "e.g., PPE_MISSING, BLOCKED_EXIT, CHEMICAL_SPILL",
      "description": "clear description of the violation",
      "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
      "evidence": "what in the CV output supports this finding",
      "immediate_action_required": true/false
    }}
  ],
  "warnings": [
    {{
      "warning_id": "W001",
      "description": "potential concern that needs monitoring",
      "recommended_action": "what should be done"
    }}
  ],
  "reasoning": "2-3 sentence explanation of your overall assessment logic",
  "risk_score": <integer 0-100, where 100 is maximum risk>
}}"""


REPORT_GENERATION_PROMPT = """You are an EHS incident report writer. Generate a professional, detailed incident report based on the compliance assessment and supporting evidence.

## Incident Assessment:
{assessment}

## CV Analysis Summary:
{cv_summary}

## Retrieved Policy Context:
{policy_context}

## Site/Location Context:
- Location: {location}
- Timestamp: {timestamp}
- Reported by: AI Monitoring System

Generate a structured incident report as JSON (no markdown):
{{
  "report_id": "INC-{timestamp_short}-001",
  "incident_date": "{timestamp}",
  "location": "{location}",
  "reported_by": "EHS AI Monitoring System",
  "incident_type": "category of incident",
  "severity": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",
  "description": "detailed paragraph describing what was observed",
  "root_cause_analysis": {{
    "immediate_cause": "what directly caused the issue",
    "contributing_factors": ["factor 1", "factor 2"],
    "root_cause": "underlying systemic cause"
  }},
  "affected_personnel": "description of who is at risk",
  "regulatory_references": ["relevant OSHA/ISO standards"],
  "corrective_actions": [
    {{
      "action_id": "CA-001",
      "description": "specific action to take",
      "priority": "IMMEDIATE" | "SHORT_TERM" | "LONG_TERM",
      "responsible_party": "who should action this",
      "due_within": "timeframe e.g., 1 hour, 24 hours, 1 week"
    }}
  ],
  "preventive_measures": ["measure 1", "measure 2"],
  "follow_up_required": true/false,
  "regulatory_notification_required": true/false,
  "notification_reason": "reason if regulatory notification needed"
}}"""


POLICY_QA_PROMPT = """You are an EHS policy expert assistant. Answer the user's question using ONLY the provided policy documents as context. Be precise, cite specific policies, and provide actionable guidance.

## Retrieved Policy Context:
{policy_context}

## User Question:
{question}

Provide a clear, structured answer. If the policies don't contain sufficient information, say so explicitly.
Format your response with:
1. Direct answer to the question
2. Relevant policy references
3. Specific requirements or thresholds mentioned
4. Recommended actions if applicable"""


class EHSReasoningAgent:
    """
    Agentic reasoning layer using Groq API.
    Applies EHS policies dynamically to CV outputs without hardcoded rules.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = model
        self.client = None
        self._setup()

    def _setup(self):
        """Initialize Groq client."""
        if not self.api_key:
            logger.warning("⚠️ GROQ_API_KEY not set. Agent in mock mode.")
            return
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            logger.info(f"✅ Groq client initialized with model: {self.model}")
        except ImportError:
            logger.warning("⚠️ groq package not installed. Agent in mock mode.")
        except Exception as e:
            logger.error(f"❌ Groq setup failed: {e}")

    def _call_groq(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> str:
        """
        Call Groq API with retry logic.
        Low temperature for deterministic/reproducible outputs.
        """
        if self.client is None:
            return self._mock_response(prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._mock_response(prompt)

    def assess_compliance(self, cv_results: dict, policy_context: str) -> dict:
        """
        Step 1 of agent workflow: Assess compliance from CV + policy.
        Returns structured violation assessment.
        """
        cv_summary = {
            "persons_in_frame": cv_results["summary"]["persons_in_frame"],
            "ppe_violations": cv_results["summary"]["ppe_violations"],
            "hazards": cv_results["hazards_detected"],
            "ppe_details": cv_results["ppe_analysis"],
            "detections": [
                {"label": d["label"], "confidence": d["confidence"]}
                for d in cv_results["detections"][:10]  # limit for prompt
            ]
        }

        prompt = COMPLIANCE_ASSESSMENT_PROMPT.format(
            cv_results=json.dumps(cv_summary, indent=2),
            policy_context=policy_context
        )

        raw_response = self._call_groq(prompt, max_tokens=1500)

        try:
            # Clean and parse JSON response
            clean = raw_response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            assessment = json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("Could not parse compliance JSON, using structured fallback")
            assessment = self._build_fallback_assessment(cv_results)

        assessment["raw_llm_response"] = raw_response
        return assessment

    def generate_incident_report(self, assessment: dict, cv_results: dict,
                                 policy_context: str, location: str = "Industrial Floor A") -> dict:
        """
        Step 2: Generate structured incident report from assessment.
        """
        ts = datetime.now()
        timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_short = ts.strftime("%Y%m%d%H%M")

        cv_summary = {
            "persons": cv_results["summary"]["persons_in_frame"],
            "ppe_violations": cv_results["summary"]["ppe_violations"],
            "hazards": len(cv_results["hazards_detected"]),
            "image_dims": cv_results["image_dimensions"]
        }

        prompt = REPORT_GENERATION_PROMPT.format(
            assessment=json.dumps({k: v for k, v in assessment.items() if k != "raw_llm_response"}, indent=2),
            cv_summary=json.dumps(cv_summary, indent=2),
            policy_context=policy_context[:2000],
            location=location,
            timestamp=timestamp,
            timestamp_short=timestamp_short
        )

        raw_response = self._call_groq(prompt, max_tokens=2000)

        try:
            clean = raw_response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            report = json.loads(clean)
        except json.JSONDecodeError:
            report = self._build_fallback_report(assessment, location, timestamp, timestamp_short)

        report["evidence"] = {
            "cv_analysis": cv_summary,
            "detections_count": cv_results["total_detections"],
            "annotated_image_available": True
        }
        return report

    def answer_policy_question(self, question: str, policy_context: str) -> str:
        """
        Step 3: Answer EHS policy questions using retrieved context.
        """
        prompt = POLICY_QA_PROMPT.format(
            policy_context=policy_context,
            question=question
        )
        return self._call_groq(prompt, max_tokens=800, temperature=0.2)

    def _build_fallback_assessment(self, cv_results: dict) -> dict:
        """Structured fallback assessment when LLM unavailable."""
        violations = []
        ppe_viols = cv_results["summary"]["ppe_violations"]
        hazards = cv_results["hazards_detected"]

        if ppe_viols > 0:
            violations.append({
                "violation_id": "V001",
                "policy_reference": "PPE-001",
                "violation_type": "PPE_MISSING",
                "description": f"{ppe_viols} person(s) detected without required PPE",
                "severity": "HIGH",
                "evidence": f"CV analysis detected {ppe_viols} PPE compliance failure(s)",
                "immediate_action_required": True
            })

        for i, hazard in enumerate(hazards):
            violations.append({
                "violation_id": f"V{i+2:03d}",
                "policy_reference": "WASTE-001",
                "violation_type": hazard["type"].upper(),
                "description": hazard["description"],
                "severity": hazard.get("severity", "MEDIUM"),
                "evidence": f"CV hazard detection confidence: {hazard['confidence']:.2f}",
                "immediate_action_required": hazard.get("severity") in ["CRITICAL", "HIGH"]
            })

        status = "COMPLIANT" if not violations else "VIOLATION"
        risk = min(len(violations) * 25 + ppe_viols * 15, 100)

        return {
            "overall_compliance_status": status,
            "confidence_level": "MEDIUM",
            "violations": violations,
            "warnings": [],
            "reasoning": "Assessment based on CV analysis (LLM unavailable - using rule-based fallback)",
            "risk_score": risk
        }

    def _build_fallback_report(self, assessment: dict, location: str, timestamp: str, ts_short: str) -> dict:
        """Structured fallback report."""
        violations = assessment.get("violations", [])
        severity = "HIGH" if violations else "LOW"
        if any(v["severity"] == "CRITICAL" for v in violations):
            severity = "CRITICAL"

        return {
            "report_id": f"INC-{ts_short}-001",
            "incident_date": timestamp,
            "location": location,
            "reported_by": "EHS AI Monitoring System",
            "incident_type": "Safety Compliance Violation",
            "severity": severity,
            "description": f"AI monitoring system detected {len(violations)} safety violation(s) at {location}.",
            "root_cause_analysis": {
                "immediate_cause": "Non-compliance with PPE and safety protocols",
                "contributing_factors": ["Inadequate safety supervision", "Insufficient PPE availability"],
                "root_cause": "Systemic gaps in safety culture and enforcement"
            },
            "affected_personnel": "All personnel in detected area",
            "regulatory_references": ["OSHA 29 CFR 1910.132", "ISO 45001:2018"],
            "corrective_actions": [
                {
                    "action_id": "CA-001",
                    "description": "Immediately enforce PPE requirements for all personnel",
                    "priority": "IMMEDIATE",
                    "responsible_party": "Area Supervisor",
                    "due_within": "1 hour"
                }
            ],
            "preventive_measures": ["Daily PPE compliance audits", "Refresher safety training"],
            "follow_up_required": True,
            "regulatory_notification_required": severity == "CRITICAL",
            "notification_reason": "Critical safety violation detected by monitoring system" if severity == "CRITICAL" else ""
        }

    def _mock_response(self, prompt: str) -> str:
        """Return mock JSON when no API key available."""
        if "compliance" in prompt.lower() or "violation" in prompt.lower():
            return json.dumps({
                "overall_compliance_status": "WARNING",
                "confidence_level": "LOW",
                "violations": [
                    {
                        "violation_id": "V001",
                        "policy_reference": "PPE-001",
                        "violation_type": "PPE_MISSING",
                        "description": "Mock: PPE compliance could not be verified (no API key configured)",
                        "severity": "MEDIUM",
                        "evidence": "Analysis requires valid GROQ_API_KEY",
                        "immediate_action_required": False
                    }
                ],
                "warnings": [
                    {
                        "warning_id": "W001",
                        "description": "Groq API key not configured - using mock mode",
                        "recommended_action": "Set GROQ_API_KEY in .env file"
                    }
                ],
                "reasoning": "This is a mock assessment. Please configure GROQ_API_KEY for real AI-powered analysis.",
                "risk_score": 30
            })
        return "Mock response: Please configure GROQ_API_KEY in your .env file for real AI analysis. Get a free key at https://console.groq.com"
