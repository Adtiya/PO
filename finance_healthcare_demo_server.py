#!/usr/bin/env python3
"""
Finance and Healthcare AGI-NARI Solutions Demo Server
Demonstrates real-world business problem solving with AGI-NARI integration
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import time
import threading
import uuid
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)
CORS(app)

# Mock AGI-NARI Service for Finance and Healthcare Demonstrations
class FinanceHealthcareAGINARI:
    """
    Mock AGI-NARI service demonstrating finance and healthcare solutions
    """
    
    def __init__(self):
        self.consciousness_level = 0.867
        self.system_health = 0.984
        self.active_sessions = 0
        
        # Finance sector data
        self.market_conditions = {
            "volatility_index": 23.4,
            "market_sentiment": "cautiously_optimistic",
            "economic_indicators": {
                "gdp_growth": 2.1,
                "inflation_rate": 3.2,
                "unemployment_rate": 3.7
            }
        }
        
        # Healthcare sector data
        self.healthcare_metrics = {
            "patient_satisfaction": 87.3,
            "diagnostic_accuracy": 94.2,
            "treatment_efficacy": 89.7,
            "operational_efficiency": 82.1
        }
    
    # Finance Solutions
    async def analyze_credit_risk(self, applicant_data):
        """Comprehensive credit risk assessment"""
        time.sleep(2)  # Simulate processing time
        
        # Simulate AGI reasoning for credit assessment
        base_score = 720
        
        # Adjust based on income
        income_factor = min(applicant_data.get('annual_income', 50000) / 100000, 1.0)
        score_adjustment = income_factor * 80
        
        # Adjust based on employment history
        employment_years = applicant_data.get('employment_years', 2)
        employment_factor = min(employment_years / 10, 1.0) * 40
        
        # Adjust based on debt-to-income ratio
        debt_ratio = applicant_data.get('debt_to_income_ratio', 0.3)
        debt_penalty = debt_ratio * 100
        
        final_score = base_score + score_adjustment + employment_factor - debt_penalty
        final_score = max(300, min(850, final_score))
        
        # Determine approval status
        if final_score >= 700:
            approval_status = "approved"
            risk_level = "low"
        elif final_score >= 600:
            approval_status = "conditional_approval"
            risk_level = "moderate"
        else:
            approval_status = "declined"
            risk_level = "high"
        
        return {
            "analysis_id": f"credit_{uuid.uuid4().hex[:8]}",
            "credit_score": round(final_score),
            "approval_status": approval_status,
            "risk_level": risk_level,
            "confidence_score": 0.92,
            "reasoning_chain": [
                {
                    "factor": "income_analysis",
                    "description": f"Annual income of ${applicant_data.get('annual_income', 50000):,} indicates {income_factor:.1%} income stability",
                    "impact": f"+{score_adjustment:.0f} points",
                    "confidence": 0.94
                },
                {
                    "factor": "employment_history",
                    "description": f"{employment_years} years employment history shows {employment_factor/40:.1%} stability",
                    "impact": f"+{employment_factor:.0f} points",
                    "confidence": 0.89
                },
                {
                    "factor": "debt_analysis",
                    "description": f"Debt-to-income ratio of {debt_ratio:.1%} indicates {debt_ratio:.1%} financial stress",
                    "impact": f"-{debt_penalty:.0f} points",
                    "confidence": 0.96
                }
            ],
            "recommendations": {
                "primary_action": approval_status.replace('_', ' ').title(),
                "loan_amount_recommendation": applicant_data.get('requested_amount', 250000) * (0.8 if approval_status == "conditional_approval" else 1.0),
                "interest_rate_adjustment": 0.5 if risk_level == "moderate" else 0.0,
                "monitoring_requirements": ["monthly_income_verification"] if risk_level != "low" else []
            },
            "consciousness_factors": {
                "uncertainty_level": 0.08,
                "model_confidence": 0.92,
                "human_review_recommended": risk_level == "high",
                "explanation_clarity": "high"
            },
            "regulatory_compliance": {
                "fair_lending_score": 0.97,
                "bias_detection": "no_bias_detected",
                "audit_trail": "complete"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def detect_fraud(self, transaction_data):
        """Advanced fraud detection analysis"""
        time.sleep(1.5)  # Simulate processing time
        
        # Simulate fraud risk calculation
        risk_factors = []
        fraud_score = 0.1  # Base low risk
        
        # Check transaction amount
        amount = transaction_data.get('amount', 100)
        if amount > 10000:
            fraud_score += 0.3
            risk_factors.append("high_transaction_amount")
        
        # Check location
        if transaction_data.get('location_unusual', False):
            fraud_score += 0.4
            risk_factors.append("unusual_location")
        
        # Check time patterns
        if transaction_data.get('unusual_time', False):
            fraud_score += 0.2
            risk_factors.append("unusual_timing")
        
        # Check velocity
        if transaction_data.get('high_velocity', False):
            fraud_score += 0.3
            risk_factors.append("high_transaction_velocity")
        
        fraud_score = min(fraud_score, 0.95)
        
        # Determine risk level
        if fraud_score < 0.3:
            risk_level = "low"
            action = "approve"
        elif fraud_score < 0.7:
            risk_level = "moderate"
            action = "review"
        else:
            risk_level = "high"
            action = "block"
        
        return {
            "analysis_id": f"fraud_{uuid.uuid4().hex[:8]}",
            "fraud_probability": round(fraud_score, 3),
            "risk_level": risk_level,
            "recommended_action": action,
            "confidence_score": 0.94,
            "risk_factors": risk_factors,
            "reasoning_chain": [
                {
                    "factor": factor,
                    "description": f"Detected {factor.replace('_', ' ')} pattern",
                    "risk_contribution": 0.2 + random.random() * 0.3,
                    "confidence": 0.85 + random.random() * 0.1
                } for factor in risk_factors
            ],
            "emotional_intelligence": {
                "customer_stress_indicators": transaction_data.get('customer_communications', '') != '',
                "social_engineering_risk": 0.15 if 'urgent' in transaction_data.get('customer_communications', '').lower() else 0.05,
                "behavioral_anomalies": len(risk_factors) > 2
            },
            "consciousness_awareness": {
                "model_limitations": "Pattern-based detection may miss novel fraud schemes",
                "uncertainty_acknowledgment": f"Confidence level: {94}%",
                "human_oversight_recommended": risk_level == "high"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def optimize_portfolio(self, portfolio_data):
        """Portfolio optimization with risk management"""
        time.sleep(2.5)  # Simulate processing time
        
        # Simulate portfolio optimization
        current_allocation = portfolio_data.get('current_allocation', {
            'stocks': 60,
            'bonds': 30,
            'alternatives': 10
        })
        
        risk_tolerance = portfolio_data.get('risk_tolerance', 'moderate')
        
        # AGI-NARI optimization based on market conditions and consciousness
        if risk_tolerance == 'conservative':
            optimized_allocation = {'stocks': 40, 'bonds': 50, 'alternatives': 10}
            expected_return = 0.067
            risk_level = 0.12
        elif risk_tolerance == 'aggressive':
            optimized_allocation = {'stocks': 80, 'bonds': 15, 'alternatives': 5}
            expected_return = 0.095
            risk_level = 0.18
        else:  # moderate
            optimized_allocation = {'stocks': 65, 'bonds': 25, 'alternatives': 10}
            expected_return = 0.081
            risk_level = 0.15
        
        return {
            "analysis_id": f"portfolio_{uuid.uuid4().hex[:8]}",
            "current_allocation": current_allocation,
            "optimized_allocation": optimized_allocation,
            "expected_annual_return": expected_return,
            "estimated_risk": risk_level,
            "confidence_score": 0.89,
            "optimization_reasoning": [
                {
                    "factor": "market_conditions",
                    "description": f"Current market volatility of {self.market_conditions['volatility_index']} suggests moderate positioning",
                    "impact": "reduced_equity_exposure",
                    "confidence": 0.91
                },
                {
                    "factor": "economic_outlook",
                    "description": f"GDP growth of {self.market_conditions['economic_indicators']['gdp_growth']}% supports equity allocation",
                    "impact": "maintained_growth_exposure",
                    "confidence": 0.87
                },
                {
                    "factor": "risk_tolerance_alignment",
                    "description": f"Portfolio aligned with {risk_tolerance} risk tolerance",
                    "impact": "balanced_allocation",
                    "confidence": 0.95
                }
            ],
            "rebalancing_recommendations": {
                "immediate_actions": [
                    f"Reduce stocks by {current_allocation['stocks'] - optimized_allocation['stocks']}%",
                    f"Increase bonds by {optimized_allocation['bonds'] - current_allocation['bonds']}%"
                ],
                "monitoring_triggers": [
                    "Market volatility exceeds 30",
                    "Portfolio drift exceeds 5%",
                    "Economic indicators change significantly"
                ]
            },
            "consciousness_factors": {
                "model_uncertainty": 0.11,
                "market_unpredictability": "acknowledged",
                "human_oversight_value": "high_for_major_changes"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    # Healthcare Solutions
    async def diagnose_patient(self, patient_data):
        """Intelligent diagnostic support"""
        time.sleep(3)  # Simulate processing time
        
        symptoms = patient_data.get('symptoms', [])
        patient_history = patient_data.get('medical_history', {})
        
        # Simulate diagnostic reasoning
        primary_diagnosis = "Hypertension with metabolic syndrome"
        confidence = 0.87
        
        if 'chest_pain' in symptoms:
            primary_diagnosis = "Possible coronary artery disease"
            confidence = 0.73
        elif 'headache' in symptoms and 'fatigue' in symptoms:
            primary_diagnosis = "Tension headache with possible depression"
            confidence = 0.81
        elif 'joint_pain' in symptoms:
            primary_diagnosis = "Osteoarthritis"
            confidence = 0.79
        
        return {
            "analysis_id": f"diagnosis_{uuid.uuid4().hex[:8]}",
            "primary_diagnosis": primary_diagnosis,
            "confidence_level": confidence,
            "differential_diagnoses": [
                {
                    "condition": "Essential hypertension",
                    "probability": 0.78,
                    "supporting_factors": ["elevated_bp", "family_history"]
                },
                {
                    "condition": "Secondary hypertension",
                    "probability": 0.23,
                    "supporting_factors": ["young_age", "resistant_hypertension"]
                },
                {
                    "condition": "White coat hypertension",
                    "probability": 0.15,
                    "supporting_factors": ["normal_home_readings", "anxiety"]
                }
            ],
            "reasoning_chain": [
                {
                    "step": 1,
                    "analysis": "Symptom pattern analysis",
                    "findings": f"Patient presents with {len(symptoms)} key symptoms",
                    "confidence": 0.92
                },
                {
                    "step": 2,
                    "analysis": "Medical history correlation",
                    "findings": "Family history supports cardiovascular risk",
                    "confidence": 0.85
                },
                {
                    "step": 3,
                    "analysis": "Differential diagnosis ranking",
                    "findings": f"Primary diagnosis: {primary_diagnosis}",
                    "confidence": confidence
                }
            ],
            "recommended_tests": [
                {
                    "test": "Echocardiogram",
                    "priority": "high",
                    "rationale": "Assess cardiac function and structure"
                },
                {
                    "test": "Lipid panel",
                    "priority": "medium",
                    "rationale": "Evaluate cardiovascular risk factors"
                },
                {
                    "test": "HbA1c",
                    "priority": "medium",
                    "rationale": "Screen for diabetes mellitus"
                }
            ],
            "treatment_recommendations": [
                {
                    "intervention": "Lifestyle modifications",
                    "details": "Diet modification, exercise program, weight management",
                    "priority": "immediate"
                },
                {
                    "intervention": "Antihypertensive therapy",
                    "details": "ACE inhibitor or ARB as first-line therapy",
                    "priority": "high"
                }
            ],
            "consciousness_factors": {
                "diagnostic_uncertainty": 1 - confidence,
                "specialist_consultation_recommended": confidence < 0.8,
                "patient_complexity": "moderate",
                "explanation_clarity": "high"
            },
            "emotional_intelligence": {
                "patient_anxiety_level": patient_data.get('anxiety_indicators', 0.3),
                "communication_recommendations": [
                    "Provide clear explanation of diagnosis",
                    "Address patient concerns about prognosis",
                    "Emphasize treatable nature of condition"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def optimize_treatment(self, treatment_data):
        """Personalized treatment optimization"""
        time.sleep(2)  # Simulate processing time
        
        patient_profile = treatment_data.get('patient_profile', {})
        condition = treatment_data.get('condition', 'hypertension')
        
        # Simulate personalized treatment optimization
        genetic_factors = patient_profile.get('genetic_markers', {})
        current_medications = patient_profile.get('current_medications', [])
        
        optimized_treatment = {
            "primary_medication": "Lisinopril 10mg daily",
            "alternative_options": [
                "Amlodipine 5mg daily",
                "Hydrochlorothiazide 25mg daily"
            ],
            "dosing_optimization": "Start low, titrate based on response",
            "monitoring_schedule": "Blood pressure check in 2 weeks, then monthly"
        }
        
        return {
            "analysis_id": f"treatment_{uuid.uuid4().hex[:8]}",
            "condition": condition,
            "optimized_treatment_plan": optimized_treatment,
            "confidence_score": 0.91,
            "personalization_factors": [
                {
                    "factor": "genetic_profile",
                    "impact": "Standard metabolism predicted",
                    "confidence": 0.87
                },
                {
                    "factor": "drug_interactions",
                    "impact": "No significant interactions identified",
                    "confidence": 0.95
                },
                {
                    "factor": "patient_preferences",
                    "impact": "Once-daily dosing preferred",
                    "confidence": 0.92
                }
            ],
            "efficacy_prediction": {
                "expected_response_rate": 0.78,
                "time_to_effect": "2-4 weeks",
                "side_effect_probability": 0.15
            },
            "monitoring_recommendations": [
                {
                    "parameter": "Blood pressure",
                    "frequency": "Weekly for first month",
                    "target": "<130/80 mmHg"
                },
                {
                    "parameter": "Kidney function",
                    "frequency": "Baseline and 3 months",
                    "target": "Stable creatinine"
                }
            ],
            "consciousness_awareness": {
                "treatment_uncertainty": 0.09,
                "individual_variation_acknowledged": True,
                "adjustment_readiness": "high"
            },
            "patient_education": {
                "key_points": [
                    "Medication works by relaxing blood vessels",
                    "May take several weeks to see full effect",
                    "Important to take consistently"
                ],
                "lifestyle_recommendations": [
                    "Reduce sodium intake",
                    "Regular exercise",
                    "Stress management"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def optimize_hospital_operations(self, operations_data):
        """Hospital operations optimization"""
        time.sleep(2)  # Simulate processing time
        
        current_metrics = operations_data.get('current_metrics', {})
        department = operations_data.get('department', 'emergency')
        
        # Simulate operations optimization
        optimization_recommendations = {
            "staff_allocation": {
                "current_staffing": current_metrics.get('staff_count', 12),
                "recommended_staffing": 15,
                "adjustment_rationale": "Peak demand period approaching"
            },
            "patient_flow": {
                "current_wait_time": current_metrics.get('wait_time_minutes', 45),
                "target_wait_time": 25,
                "improvement_strategies": [
                    "Implement fast-track for low-acuity patients",
                    "Optimize triage process",
                    "Improve discharge planning"
                ]
            },
            "resource_utilization": {
                "bed_utilization": "87%",
                "equipment_efficiency": "92%",
                "optimization_opportunities": [
                    "Implement predictive bed management",
                    "Optimize equipment scheduling"
                ]
            }
        }
        
        return {
            "analysis_id": f"operations_{uuid.uuid4().hex[:8]}",
            "department": department,
            "optimization_recommendations": optimization_recommendations,
            "confidence_score": 0.88,
            "expected_improvements": {
                "wait_time_reduction": "44%",
                "patient_satisfaction_increase": "23%",
                "staff_efficiency_improvement": "18%",
                "cost_reduction": "12%"
            },
            "implementation_timeline": {
                "immediate_actions": [
                    "Adjust current shift staffing",
                    "Implement fast-track protocol"
                ],
                "short_term_goals": [
                    "Staff training on new protocols",
                    "Technology system updates"
                ],
                "long_term_objectives": [
                    "Predictive analytics implementation",
                    "Workflow automation"
                ]
            },
            "consciousness_factors": {
                "operational_complexity": "high",
                "human_factor_importance": "critical",
                "continuous_monitoring_required": True
            },
            "staff_wellbeing_considerations": {
                "burnout_risk_assessment": "moderate",
                "workload_balance": "requires_attention",
                "satisfaction_factors": [
                    "Adequate staffing levels",
                    "Clear protocols",
                    "Technology support"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def assess_mental_health(self, patient_data):
        """Mental health assessment and support"""
        time.sleep(2.5)  # Simulate processing time
        
        patient_communications = patient_data.get('communications', '')
        assessment_responses = patient_data.get('assessment_responses', {})
        
        # Simulate mental health assessment
        depression_score = assessment_responses.get('phq9_score', 8)
        anxiety_score = assessment_responses.get('gad7_score', 6)
        
        if depression_score >= 15:
            severity = "severe"
            risk_level = "high"
        elif depression_score >= 10:
            severity = "moderate"
            risk_level = "moderate"
        else:
            severity = "mild"
            risk_level = "low"
        
        return {
            "analysis_id": f"mental_health_{uuid.uuid4().hex[:8]}",
            "assessment_summary": {
                "depression_severity": severity,
                "anxiety_level": "moderate" if anxiety_score >= 10 else "mild",
                "overall_risk_level": risk_level,
                "confidence_score": 0.89
            },
            "emotional_analysis": {
                "primary_emotions": [
                    {
                        "emotion": "sadness",
                        "intensity": 0.7,
                        "confidence": 0.91
                    },
                    {
                        "emotion": "anxiety",
                        "intensity": 0.6,
                        "confidence": 0.87
                    }
                ],
                "mood_patterns": "Persistent low mood with anxiety episodes",
                "emotional_regulation": "impaired",
                "social_connection_quality": "reduced"
            },
            "treatment_recommendations": [
                {
                    "intervention": "Cognitive Behavioral Therapy",
                    "priority": "high",
                    "rationale": "Evidence-based treatment for depression and anxiety",
                    "expected_duration": "12-16 sessions"
                },
                {
                    "intervention": "Medication evaluation",
                    "priority": "moderate",
                    "rationale": "Consider SSRI for moderate-severe symptoms",
                    "specialist_required": True
                },
                {
                    "intervention": "Lifestyle interventions",
                    "priority": "immediate",
                    "rationale": "Exercise, sleep hygiene, stress management",
                    "self_directed": True
                }
            ],
            "crisis_assessment": {
                "suicidal_ideation_risk": "low",
                "immediate_safety_concerns": False,
                "crisis_intervention_needed": False,
                "safety_planning_recommended": True
            },
            "consciousness_awareness": {
                "assessment_limitations": "Self-reported data may have bias",
                "cultural_considerations": "Important for treatment planning",
                "human_clinician_oversight": "essential"
            },
            "monitoring_plan": {
                "frequency": "Weekly initially, then bi-weekly",
                "key_indicators": [
                    "Mood tracking",
                    "Sleep patterns",
                    "Social engagement",
                    "Medication compliance"
                ],
                "escalation_triggers": [
                    "Worsening suicidal ideation",
                    "Significant functional decline",
                    "Treatment non-response"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }

# Initialize mock service
mock_agi_nari = FinanceHealthcareAGINARI()

# HTML Template for the demonstration interface
DEMO_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AGI-NARI Finance & Healthcare Solutions Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        
        .sector-tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 20px;
        }
        
        .tab-button {
            padding: 15px 30px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: all 0.3s;
        }
        
        .tab-button.active {
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .tab-button:hover {
            background: #2980b9;
        }
        
        .sector-content {
            display: none;
        }
        
        .sector-content.active {
            display: block;
        }
        
        .demo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .demo-section {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            border-left: 5px solid #3498db;
        }
        
        .finance-section {
            border-left-color: #27ae60;
        }
        
        .healthcare-section {
            border-left-color: #e74c3c;
        }
        
        .demo-section h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.4em;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            color: #34495e;
            font-weight: 600;
        }
        
        .input-group input, .input-group textarea, .input-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus, .input-group textarea:focus, .input-group select:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .btn {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
        }
        
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .btn.finance {
            background: linear-gradient(135deg, #27ae60, #229954);
        }
        
        .btn.healthcare {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
        }
        
        .result-area {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            border-left: 4px solid #27ae60;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .result-area pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
            color: #2c3e50;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #27ae60;
            margin-bottom: 5px;
        }
        
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏦🏥 AGI-NARI Finance & Healthcare Solutions</h1>
            <p>Real-world business problem solving with AGI-NARI integration</p>
        </div>
        
        <!-- Sector Tabs -->
        <div class="sector-tabs">
            <button class="tab-button active" onclick="showSector('finance')">💰 Finance Solutions</button>
            <button class="tab-button" onclick="showSector('healthcare')">🏥 Healthcare Solutions</button>
        </div>
        
        <!-- Finance Sector Content -->
        <div id="finance-content" class="sector-content active">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">98.4%</div>
                    <div class="metric-label">System Health</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">23.4</div>
                    <div class="metric-label">Market Volatility</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">92%</div>
                    <div class="metric-label">Risk Model Accuracy</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">$2.3B</div>
                    <div class="metric-label">Losses Prevented</div>
                </div>
            </div>
            
            <div class="demo-grid">
                <!-- Credit Risk Assessment -->
                <div class="demo-section finance-section">
                    <h3>💳 Credit Risk Assessment</h3>
                    <div class="input-group">
                        <label for="creditIncome">Annual Income ($):</label>
                        <input type="number" id="creditIncome" value="75000" min="0">
                    </div>
                    <div class="input-group">
                        <label for="creditEmployment">Employment Years:</label>
                        <input type="number" id="creditEmployment" value="5" min="0">
                    </div>
                    <div class="input-group">
                        <label for="creditDebtRatio">Debt-to-Income Ratio:</label>
                        <input type="number" id="creditDebtRatio" value="0.25" step="0.01" min="0" max="1">
                    </div>
                    <div class="input-group">
                        <label for="creditAmount">Requested Amount ($):</label>
                        <input type="number" id="creditAmount" value="250000" min="0">
                    </div>
                    <button class="btn finance" onclick="assessCreditRisk()">
                        <span id="creditLoader" style="display: none;" class="loading"></span>
                        Assess Credit Risk
                    </button>
                    <div class="result-area" id="creditResult" style="display: none;">
                        <pre id="creditOutput"></pre>
                    </div>
                </div>
                
                <!-- Fraud Detection -->
                <div class="demo-section finance-section">
                    <h3>🔍 Fraud Detection</h3>
                    <div class="input-group">
                        <label for="fraudAmount">Transaction Amount ($):</label>
                        <input type="number" id="fraudAmount" value="5000" min="0">
                    </div>
                    <div class="input-group">
                        <label for="fraudLocation">Unusual Location:</label>
                        <select id="fraudLocation">
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="fraudTime">Unusual Time:</label>
                        <select id="fraudTime">
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="fraudVelocity">High Velocity:</label>
                        <select id="fraudVelocity">
                            <option value="false">No</option>
                            <option value="true">Yes</option>
                        </select>
                    </div>
                    <button class="btn finance" onclick="detectFraud()">
                        <span id="fraudLoader" style="display: none;" class="loading"></span>
                        Analyze Fraud Risk
                    </button>
                    <div class="result-area" id="fraudResult" style="display: none;">
                        <pre id="fraudOutput"></pre>
                    </div>
                </div>
                
                <!-- Portfolio Optimization -->
                <div class="demo-section finance-section">
                    <h3>📊 Portfolio Optimization</h3>
                    <div class="input-group">
                        <label for="portfolioRisk">Risk Tolerance:</label>
                        <select id="portfolioRisk">
                            <option value="conservative">Conservative</option>
                            <option value="moderate" selected>Moderate</option>
                            <option value="aggressive">Aggressive</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="portfolioStocks">Current Stocks (%):</label>
                        <input type="number" id="portfolioStocks" value="60" min="0" max="100">
                    </div>
                    <div class="input-group">
                        <label for="portfolioBonds">Current Bonds (%):</label>
                        <input type="number" id="portfolioBonds" value="30" min="0" max="100">
                    </div>
                    <div class="input-group">
                        <label for="portfolioAlts">Current Alternatives (%):</label>
                        <input type="number" id="portfolioAlts" value="10" min="0" max="100">
                    </div>
                    <button class="btn finance" onclick="optimizePortfolio()">
                        <span id="portfolioLoader" style="display: none;" class="loading"></span>
                        Optimize Portfolio
                    </button>
                    <div class="result-area" id="portfolioResult" style="display: none;">
                        <pre id="portfolioOutput"></pre>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Healthcare Sector Content -->
        <div id="healthcare-content" class="sector-content">
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">94.2%</div>
                    <div class="metric-label">Diagnostic Accuracy</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">87.3%</div>
                    <div class="metric-label">Patient Satisfaction</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">89.7%</div>
                    <div class="metric-label">Treatment Efficacy</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">82.1%</div>
                    <div class="metric-label">Operational Efficiency</div>
                </div>
            </div>
            
            <div class="demo-grid">
                <!-- Diagnostic Support -->
                <div class="demo-section healthcare-section">
                    <h3>🩺 Diagnostic Support</h3>
                    <div class="input-group">
                        <label for="diagnosticSymptoms">Symptoms (comma-separated):</label>
                        <textarea id="diagnosticSymptoms" rows="3">headache, fatigue, elevated blood pressure</textarea>
                    </div>
                    <div class="input-group">
                        <label for="diagnosticHistory">Medical History:</label>
                        <textarea id="diagnosticHistory" rows="2">Family history of hypertension, diabetes</textarea>
                    </div>
                    <div class="input-group">
                        <label for="diagnosticAge">Patient Age:</label>
                        <input type="number" id="diagnosticAge" value="45" min="0" max="120">
                    </div>
                    <button class="btn healthcare" onclick="diagnosePatient()">
                        <span id="diagnosticLoader" style="display: none;" class="loading"></span>
                        Analyze Diagnosis
                    </button>
                    <div class="result-area" id="diagnosticResult" style="display: none;">
                        <pre id="diagnosticOutput"></pre>
                    </div>
                </div>
                
                <!-- Treatment Optimization -->
                <div class="demo-section healthcare-section">
                    <h3>💊 Treatment Optimization</h3>
                    <div class="input-group">
                        <label for="treatmentCondition">Condition:</label>
                        <select id="treatmentCondition">
                            <option value="hypertension">Hypertension</option>
                            <option value="diabetes">Diabetes</option>
                            <option value="depression">Depression</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="treatmentAge">Patient Age:</label>
                        <input type="number" id="treatmentAge" value="55" min="0" max="120">
                    </div>
                    <div class="input-group">
                        <label for="treatmentAllergies">Known Allergies:</label>
                        <input type="text" id="treatmentAllergies" placeholder="e.g., penicillin, sulfa">
                    </div>
                    <div class="input-group">
                        <label for="treatmentMedications">Current Medications:</label>
                        <textarea id="treatmentMedications" rows="2" placeholder="List current medications"></textarea>
                    </div>
                    <button class="btn healthcare" onclick="optimizeTreatment()">
                        <span id="treatmentLoader" style="display: none;" class="loading"></span>
                        Optimize Treatment
                    </button>
                    <div class="result-area" id="treatmentResult" style="display: none;">
                        <pre id="treatmentOutput"></pre>
                    </div>
                </div>
                
                <!-- Hospital Operations -->
                <div class="demo-section healthcare-section">
                    <h3>🏥 Hospital Operations</h3>
                    <div class="input-group">
                        <label for="operationsDept">Department:</label>
                        <select id="operationsDept">
                            <option value="emergency">Emergency Department</option>
                            <option value="surgery">Surgery</option>
                            <option value="icu">ICU</option>
                            <option value="general">General Medicine</option>
                        </select>
                    </div>
                    <div class="input-group">
                        <label for="operationsStaff">Current Staff Count:</label>
                        <input type="number" id="operationsStaff" value="12" min="1">
                    </div>
                    <div class="input-group">
                        <label for="operationsWait">Average Wait Time (minutes):</label>
                        <input type="number" id="operationsWait" value="45" min="0">
                    </div>
                    <div class="input-group">
                        <label for="operationsOccupancy">Bed Occupancy (%):</label>
                        <input type="number" id="operationsOccupancy" value="87" min="0" max="100">
                    </div>
                    <button class="btn healthcare" onclick="optimizeOperations()">
                        <span id="operationsLoader" style="display: none;" class="loading"></span>
                        Optimize Operations
                    </button>
                    <div class="result-area" id="operationsResult" style="display: none;">
                        <pre id="operationsOutput"></pre>
                    </div>
                </div>
                
                <!-- Mental Health Assessment -->
                <div class="demo-section healthcare-section">
                    <h3>🧠 Mental Health Assessment</h3>
                    <div class="input-group">
                        <label for="mentalPHQ9">PHQ-9 Depression Score (0-27):</label>
                        <input type="number" id="mentalPHQ9" value="8" min="0" max="27">
                    </div>
                    <div class="input-group">
                        <label for="mentalGAD7">GAD-7 Anxiety Score (0-21):</label>
                        <input type="number" id="mentalGAD7" value="6" min="0" max="21">
                    </div>
                    <div class="input-group">
                        <label for="mentalCommunications">Patient Communications:</label>
                        <textarea id="mentalCommunications" rows="3" placeholder="Patient's description of feelings and concerns">I've been feeling down lately and having trouble sleeping. Work stress is overwhelming.</textarea>
                    </div>
                    <button class="btn healthcare" onclick="assessMentalHealth()">
                        <span id="mentalLoader" style="display: none;" class="loading"></span>
                        Assess Mental Health
                    </button>
                    <div class="result-area" id="mentalResult" style="display: none;">
                        <pre id="mentalOutput"></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function showSector(sector) {
            // Hide all content
            document.querySelectorAll('.sector-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab-button').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected content and activate tab
            document.getElementById(sector + '-content').classList.add('active');
            event.target.classList.add('active');
        }
        
        // Finance Functions
        async function assessCreditRisk() {
            const loader = document.getElementById('creditLoader');
            const button = event.target;
            const resultArea = document.getElementById('creditResult');
            const output = document.getElementById('creditOutput');
            
            const data = {
                annual_income: parseInt(document.getElementById('creditIncome').value),
                employment_years: parseInt(document.getElementById('creditEmployment').value),
                debt_to_income_ratio: parseFloat(document.getElementById('creditDebtRatio').value),
                requested_amount: parseInt(document.getElementById('creditAmount').value)
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/finance/credit-risk', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
        
        async function detectFraud() {
            const loader = document.getElementById('fraudLoader');
            const button = event.target;
            const resultArea = document.getElementById('fraudResult');
            const output = document.getElementById('fraudOutput');
            
            const data = {
                amount: parseInt(document.getElementById('fraudAmount').value),
                location_unusual: document.getElementById('fraudLocation').value === 'true',
                unusual_time: document.getElementById('fraudTime').value === 'true',
                high_velocity: document.getElementById('fraudVelocity').value === 'true'
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/finance/fraud-detection', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
        
        async function optimizePortfolio() {
            const loader = document.getElementById('portfolioLoader');
            const button = event.target;
            const resultArea = document.getElementById('portfolioResult');
            const output = document.getElementById('portfolioOutput');
            
            const data = {
                risk_tolerance: document.getElementById('portfolioRisk').value,
                current_allocation: {
                    stocks: parseInt(document.getElementById('portfolioStocks').value),
                    bonds: parseInt(document.getElementById('portfolioBonds').value),
                    alternatives: parseInt(document.getElementById('portfolioAlts').value)
                }
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/finance/portfolio-optimization', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
        
        // Healthcare Functions
        async function diagnosePatient() {
            const loader = document.getElementById('diagnosticLoader');
            const button = event.target;
            const resultArea = document.getElementById('diagnosticResult');
            const output = document.getElementById('diagnosticOutput');
            
            const symptoms = document.getElementById('diagnosticSymptoms').value.split(',').map(s => s.trim());
            const data = {
                symptoms: symptoms,
                medical_history: {
                    history: document.getElementById('diagnosticHistory').value,
                    age: parseInt(document.getElementById('diagnosticAge').value)
                }
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/healthcare/diagnosis', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
        
        async function optimizeTreatment() {
            const loader = document.getElementById('treatmentLoader');
            const button = event.target;
            const resultArea = document.getElementById('treatmentResult');
            const output = document.getElementById('treatmentOutput');
            
            const data = {
                condition: document.getElementById('treatmentCondition').value,
                patient_profile: {
                    age: parseInt(document.getElementById('treatmentAge').value),
                    allergies: document.getElementById('treatmentAllergies').value.split(',').map(s => s.trim()),
                    current_medications: document.getElementById('treatmentMedications').value.split(',').map(s => s.trim())
                }
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/healthcare/treatment-optimization', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
        
        async function optimizeOperations() {
            const loader = document.getElementById('operationsLoader');
            const button = event.target;
            const resultArea = document.getElementById('operationsResult');
            const output = document.getElementById('operationsOutput');
            
            const data = {
                department: document.getElementById('operationsDept').value,
                current_metrics: {
                    staff_count: parseInt(document.getElementById('operationsStaff').value),
                    wait_time_minutes: parseInt(document.getElementById('operationsWait').value),
                    bed_occupancy: parseInt(document.getElementById('operationsOccupancy').value)
                }
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/healthcare/operations-optimization', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
        
        async function assessMentalHealth() {
            const loader = document.getElementById('mentalLoader');
            const button = event.target;
            const resultArea = document.getElementById('mentalResult');
            const output = document.getElementById('mentalOutput');
            
            const data = {
                assessment_responses: {
                    phq9_score: parseInt(document.getElementById('mentalPHQ9').value),
                    gad7_score: parseInt(document.getElementById('mentalGAD7').value)
                },
                communications: document.getElementById('mentalCommunications').value
            };
            
            loader.style.display = 'inline-block';
            button.disabled = true;
            resultArea.style.display = 'none';
            
            try {
                const response = await fetch('/api/healthcare/mental-health-assessment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                output.textContent = JSON.stringify(result, null, 2);
                resultArea.style.display = 'block';
            } catch (error) {
                output.textContent = 'Error: ' + error.message;
                resultArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
                button.disabled = false;
            }
        }
    </script>
</body>
</html>
"""

# API Routes
@app.route('/')
def index():
    """Main demonstration interface"""
    mock_agi_nari.active_sessions += 1
    return render_template_string(DEMO_TEMPLATE)

# Finance API Routes
@app.route('/api/finance/credit-risk', methods=['POST'])
async def api_credit_risk():
    """Credit risk assessment"""
    data = request.get_json()
    result = await mock_agi_nari.analyze_credit_risk(data)
    return jsonify(result)

@app.route('/api/finance/fraud-detection', methods=['POST'])
async def api_fraud_detection():
    """Fraud detection analysis"""
    data = request.get_json()
    result = await mock_agi_nari.detect_fraud(data)
    return jsonify(result)

@app.route('/api/finance/portfolio-optimization', methods=['POST'])
async def api_portfolio_optimization():
    """Portfolio optimization"""
    data = request.get_json()
    result = await mock_agi_nari.optimize_portfolio(data)
    return jsonify(result)

# Healthcare API Routes
@app.route('/api/healthcare/diagnosis', methods=['POST'])
async def api_diagnosis():
    """Diagnostic support"""
    data = request.get_json()
    result = await mock_agi_nari.diagnose_patient(data)
    return jsonify(result)

@app.route('/api/healthcare/treatment-optimization', methods=['POST'])
async def api_treatment_optimization():
    """Treatment optimization"""
    data = request.get_json()
    result = await mock_agi_nari.optimize_treatment(data)
    return jsonify(result)

@app.route('/api/healthcare/operations-optimization', methods=['POST'])
async def api_operations_optimization():
    """Hospital operations optimization"""
    data = request.get_json()
    result = await mock_agi_nari.optimize_hospital_operations(data)
    return jsonify(result)

@app.route('/api/healthcare/mental-health-assessment', methods=['POST'])
async def api_mental_health():
    """Mental health assessment"""
    data = request.get_json()
    result = await mock_agi_nari.assess_mental_health(data)
    return jsonify(result)

if __name__ == '__main__':
    print("🚀 Starting Finance & Healthcare AGI-NARI Solutions Demo Server...")
    print("💰 Finance Solutions:")
    print("   • Credit Risk Assessment with Consciousness-Aware Analysis")
    print("   • Advanced Fraud Detection with Emotional Intelligence")
    print("   • Portfolio Optimization with Market Sentiment Analysis")
    print("🏥 Healthcare Solutions:")
    print("   • Intelligent Diagnostic Support with Uncertainty Estimation")
    print("   • Personalized Treatment Optimization")
    print("   • Hospital Operations Optimization")
    print("   • Mental Health Assessment with Emotional Intelligence")
    print("\n🌐 Access the demo at: http://localhost:5001")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

