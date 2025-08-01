#!/usr/bin/env python3
"""
AGI-NARI Enterprise Integration Demo
Complete example showing how enterprises can integrate with the AGI-NARI system
"""

import requests
import json
import time
import websocket
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

class AGINARIEnterpriseClient:
    """
    Enterprise client for AGI-NARI system integration
    Demonstrates all major integration patterns and API usage
    """
    
    def __init__(self, base_url: str, api_key: str, organization_id: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.organization_id = organization_id
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'X-Organization-ID': organization_id,
            'Content-Type': 'application/json',
            'User-Agent': 'AGI-NARI-Enterprise-Client/1.0'
        })
        
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with the AGI-NARI system using enterprise credentials
        """
        auth_data = {
            "email": email,
            "password": password,
            "organization_id": self.organization_id
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/auth/login", json=auth_data)
        
        if response.status_code == 200:
            auth_result = response.json()
            self.session.headers.update({
                'Authorization': f"Bearer {auth_result['access_token']}"
            })
            return auth_result
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and health metrics
        """
        response = self.session.get(f"{self.base_url}/api/v1/system/status")
        return response.json()
    
    def agi_reasoning(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform AGI reasoning on complex business problems
        """
        reasoning_request = {
            "query": query,
            "context": context or {},
            "reasoning_type": "strategic_analysis",
            "output_format": "structured_report",
            "confidence_threshold": 0.8
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/agi/reason", json=reasoning_request)
        return response.json()
    
    def consciousness_state(self) -> Dict[str, Any]:
        """
        Query the current consciousness state of the AGI system
        """
        response = self.session.get(f"{self.base_url}/api/v1/consciousness/state")
        return response.json()
    
    def emotional_analysis(self, text: str, context: str = "business") -> Dict[str, Any]:
        """
        Analyze emotional content and sentiment in business communications
        """
        analysis_request = {
            "input_text": text,
            "context": context,
            "analysis_depth": "comprehensive",
            "include_empathy_response": True
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/emotion/analyze", json=analysis_request)
        return response.json()
    
    def trigger_nari_evolution(self, domain: str, targets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger NARI evolution for specific business domain optimization
        """
        evolution_request = {
            "evolution_type": "capability_enhancement",
            "target_domain": domain,
            "performance_metrics": targets,
            "priority": "high"
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/nari/evolve", json=evolution_request)
        return response.json()
    
    def nlp_processing(self, text: str, tasks: List[str]) -> Dict[str, Any]:
        """
        Perform advanced NLP processing on business documents
        """
        nlp_request = {
            "text": text,
            "tasks": tasks,
            "language": "en",
            "domain_specific": True
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/nlp/process", json=nlp_request)
        return response.json()
    
    def vision_analysis(self, image_url: str, analysis_type: str) -> Dict[str, Any]:
        """
        Analyze images and visual content for business insights
        """
        vision_request = {
            "image_url": image_url,
            "analysis_type": analysis_type,
            "extract_text": True,
            "identify_objects": True,
            "business_context": True
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/vision/analyze", json=vision_request)
        return response.json()
    
    def blockchain_record(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record important business decisions on the blockchain for audit trail
        """
        blockchain_request = {
            "transaction_type": "business_decision",
            "data": transaction_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "organization": self.organization_id
            }
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/blockchain/record", json=blockchain_request)
        return response.json()
    
    def analytics_query(self, query: str, data_sources: List[str]) -> Dict[str, Any]:
        """
        Perform advanced analytics on business data
        """
        analytics_request = {
            "query": query,
            "data_sources": data_sources,
            "analysis_type": "comprehensive",
            "visualization": True
        }
        
        response = self.session.post(f"{self.base_url}/api/v1/analytics/query", json=analytics_request)
        return response.json()

class EnterpriseIntegrationDemo:
    """
    Comprehensive demonstration of enterprise integration patterns
    """
    
    def __init__(self):
        # Initialize with demo credentials
        self.client = AGINARIEnterpriseClient(
            base_url="https://api.agi-nari.com",
            api_key="demo_enterprise_key_123",
            organization_id="enterprise_demo_org"
        )
        
    def run_comprehensive_demo(self):
        """
        Run a complete demonstration of all integration capabilities
        """
        print("🚀 AGI-NARI Enterprise Integration Demo Starting...")
        print("=" * 60)
        
        # 1. System Health Check
        self.demo_system_health()
        
        # 2. Business Intelligence Demo
        self.demo_business_intelligence()
        
        # 3. Decision Support Demo
        self.demo_decision_support()
        
        # 4. Customer Intelligence Demo
        self.demo_customer_intelligence()
        
        # 5. Risk Management Demo
        self.demo_risk_management()
        
        # 6. Innovation Acceleration Demo
        self.demo_innovation_acceleration()
        
        # 7. Operational Optimization Demo
        self.demo_operational_optimization()
        
        print("\n🎉 Enterprise Integration Demo Complete!")
        print("=" * 60)
    
    def demo_system_health(self):
        """
        Demonstrate system health monitoring and status checking
        """
        print("\n📊 1. SYSTEM HEALTH MONITORING")
        print("-" * 40)
        
        try:
            status = self.client.get_system_status()
            print(f"✅ System Status: {status.get('status', 'Unknown')}")
            print(f"🧠 AGI Capability: {status.get('agi_capability', 0)}%")
            print(f"💭 Consciousness Level: {status.get('consciousness_level', 0)}%")
            print(f"🔄 NARI Evolution: {status.get('nari_evolution', 0)}%")
            print(f"⚡ System Health: {status.get('system_health', 0)}%")
            
            # Get consciousness state
            consciousness = self.client.consciousness_state()
            print(f"🎯 Current Focus: {consciousness.get('self_reflection', {}).get('current_focus', 'Unknown')}")
            print(f"🤔 Cognitive Load: {consciousness.get('self_reflection', {}).get('cognitive_load', 0)}")
            
        except Exception as e:
            print(f"❌ Error checking system health: {e}")
    
    def demo_business_intelligence(self):
        """
        Demonstrate business intelligence and strategic analysis
        """
        print("\n📈 2. BUSINESS INTELLIGENCE & STRATEGIC ANALYSIS")
        print("-" * 50)
        
        try:
            # Strategic market analysis
            market_query = """
            Analyze the current market trends in artificial intelligence and machine learning 
            for enterprise applications. Provide strategic recommendations for a Fortune 500 
            company looking to invest in AI capabilities over the next 3-5 years.
            """
            
            context = {
                "domain": "technology_strategy",
                "time_horizon": "3_to_5_years",
                "company_size": "fortune_500",
                "industry": "diversified_technology"
            }
            
            result = self.client.agi_reasoning(market_query, context)
            
            print(f"✅ Analysis Complete - Confidence: {result.get('confidence_score', 0):.1%}")
            
            if 'recommendations' in result:
                recommendations = result['recommendations']
                print(f"🎯 Primary Strategy: {recommendations.get('primary_strategy', 'Not specified')}")
                
                if 'allocation' in recommendations:
                    print("💰 Investment Allocation:")
                    for area, percentage in recommendations['allocation'].items():
                        print(f"   • {area.replace('_', ' ').title()}: {percentage:.1%}")
                
                print(f"⚠️  Risk Assessment: {recommendations.get('risk_assessment', 'Not specified')}")
                print(f"⏱️  Timeline: {recommendations.get('timeline', 'Not specified')}")
            
            # Record decision on blockchain
            blockchain_data = {
                "decision_type": "strategic_analysis",
                "query": market_query[:100] + "...",
                "confidence": result.get('confidence_score', 0),
                "recommendations": result.get('recommendations', {})
            }
            
            blockchain_result = self.client.blockchain_record(blockchain_data)
            print(f"🔗 Decision recorded on blockchain: {blockchain_result.get('transaction_id', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error in business intelligence demo: {e}")
    
    def demo_decision_support(self):
        """
        Demonstrate AI-powered decision support capabilities
        """
        print("\n🎯 3. AI-POWERED DECISION SUPPORT")
        print("-" * 40)
        
        try:
            # Complex business decision scenario
            decision_query = """
            Our company is considering acquiring a smaller AI startup. The startup has 
            50 employees, $10M annual revenue, and proprietary computer vision technology. 
            The asking price is $150M. Should we proceed with the acquisition?
            """
            
            context = {
                "domain": "mergers_acquisitions",
                "decision_type": "acquisition",
                "financial_impact": "high",
                "strategic_importance": "high"
            }
            
            result = self.client.agi_reasoning(decision_query, context)
            
            print(f"✅ Decision Analysis Complete - Confidence: {result.get('confidence_score', 0):.1%}")
            
            if 'reasoning_chain' in result:
                print("🔍 Reasoning Process:")
                for i, step in enumerate(result['reasoning_chain'][:3], 1):
                    print(f"   {i}. {step.get('description', 'Unknown step')} (Confidence: {step.get('confidence', 0):.1%})")
            
            if 'recommendations' in result:
                recommendations = result['recommendations']
                print(f"📋 Recommendation: {recommendations.get('primary_strategy', 'Not specified')}")
                print(f"⚠️  Risk Level: {recommendations.get('risk_assessment', 'Not specified')}")
            
        except Exception as e:
            print(f"❌ Error in decision support demo: {e}")
    
    def demo_customer_intelligence(self):
        """
        Demonstrate customer intelligence and sentiment analysis
        """
        print("\n👥 4. CUSTOMER INTELLIGENCE & SENTIMENT ANALYSIS")
        print("-" * 50)
        
        try:
            # Customer feedback analysis
            customer_feedback = """
            I've been using your enterprise software for 6 months now. While the AI features 
            are impressive and have helped our team be more productive, the user interface 
            could be more intuitive. The learning curve was steep, but the results are worth it. 
            I'm excited to see what new features you'll add next quarter.
            """
            
            emotion_result = self.client.emotional_analysis(customer_feedback, "customer_feedback")
            
            print("🎭 Emotional Analysis Results:")
            if 'primary_emotions' in emotion_result:
                for emotion in emotion_result['primary_emotions'][:3]:
                    print(f"   • {emotion['emotion'].title()}: {emotion['intensity']:.1%} (Confidence: {emotion['confidence']:.1%})")
            
            if 'sentiment_analysis' in emotion_result:
                sentiment = emotion_result['sentiment_analysis']
                print(f"📊 Overall Sentiment: {sentiment.get('overall_sentiment', 'Unknown')}")
                print(f"📈 Sentiment Score: {sentiment.get('sentiment_score', 0):.2f}")
            
            if 'empathy_response' in emotion_result:
                empathy = emotion_result['empathy_response']
                print(f"🤝 AI Understanding: {empathy.get('understanding', 'Not available')}")
                print(f"💡 Suggested Response: {empathy.get('suggested_response', 'Not available')}")
            
            # NLP processing for key insights
            nlp_tasks = ["entity_extraction", "key_phrases", "sentiment_analysis", "intent_detection"]
            nlp_result = self.client.nlp_processing(customer_feedback, nlp_tasks)
            
            if 'entities' in nlp_result:
                print("🏷️  Key Entities Identified:")
                for entity in nlp_result['entities'][:3]:
                    print(f"   • {entity.get('text', 'Unknown')}: {entity.get('type', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error in customer intelligence demo: {e}")
    
    def demo_risk_management(self):
        """
        Demonstrate risk management and compliance monitoring
        """
        print("\n⚠️  5. RISK MANAGEMENT & COMPLIANCE")
        print("-" * 40)
        
        try:
            # Risk assessment scenario
            risk_query = """
            Analyze the cybersecurity risks for our organization given the recent increase 
            in AI-powered cyberattacks. We have 10,000 employees, cloud infrastructure, 
            and handle sensitive customer data. What are the top risks and mitigation strategies?
            """
            
            context = {
                "domain": "cybersecurity",
                "organization_size": "large_enterprise",
                "data_sensitivity": "high",
                "infrastructure": "hybrid_cloud"
            }
            
            result = self.client.agi_reasoning(risk_query, context)
            
            print(f"✅ Risk Analysis Complete - Confidence: {result.get('confidence_score', 0):.1%}")
            
            if 'recommendations' in result:
                recommendations = result['recommendations']
                print(f"🛡️  Primary Strategy: {recommendations.get('primary_strategy', 'Not specified')}")
                print(f"⚠️  Risk Level: {recommendations.get('risk_assessment', 'Not specified')}")
            
            if 'supporting_data' in result:
                supporting_data = result['supporting_data']
                if 'key_drivers' in supporting_data:
                    print("🔍 Key Risk Factors:")
                    for driver in supporting_data['key_drivers'][:3]:
                        print(f"   • {driver.replace('_', ' ').title()}")
            
        except Exception as e:
            print(f"❌ Error in risk management demo: {e}")
    
    def demo_innovation_acceleration(self):
        """
        Demonstrate innovation acceleration and R&D optimization
        """
        print("\n🚀 6. INNOVATION ACCELERATION & R&D")
        print("-" * 40)
        
        try:
            # Innovation opportunity analysis
            innovation_query = """
            Identify emerging technology trends that could create new product opportunities 
            for our enterprise software company. Focus on AI, automation, and digital 
            transformation technologies that could be commercialized within 2-3 years.
            """
            
            context = {
                "domain": "product_innovation",
                "industry": "enterprise_software",
                "time_horizon": "2_to_3_years",
                "focus_areas": ["ai", "automation", "digital_transformation"]
            }
            
            result = self.client.agi_reasoning(innovation_query, context)
            
            print(f"✅ Innovation Analysis Complete - Confidence: {result.get('confidence_score', 0):.1%}")
            
            if 'recommendations' in result:
                recommendations = result['recommendations']
                print(f"💡 Innovation Strategy: {recommendations.get('primary_strategy', 'Not specified')}")
                
                if 'allocation' in recommendations:
                    print("🎯 Focus Areas:")
                    for area, priority in recommendations['allocation'].items():
                        print(f"   • {area.replace('_', ' ').title()}: {priority:.1%} priority")
            
            # Trigger NARI evolution for innovation capabilities
            evolution_targets = {
                "creativity_score": 0.95,
                "innovation_speed": "accelerated",
                "cross_domain_synthesis": "advanced"
            }
            
            evolution_result = self.client.trigger_nari_evolution("innovation", evolution_targets)
            print(f"🧬 NARI Evolution Triggered: {evolution_result.get('evolution_id', 'Unknown')}")
            print(f"⏱️  Estimated Completion: {evolution_result.get('estimated_completion', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error in innovation acceleration demo: {e}")
    
    def demo_operational_optimization(self):
        """
        Demonstrate operational optimization and efficiency improvements
        """
        print("\n⚙️  7. OPERATIONAL OPTIMIZATION")
        print("-" * 35)
        
        try:
            # Operational efficiency analysis
            operations_query = """
            Analyze our current business processes and identify opportunities for automation 
            and efficiency improvements. We have manual processes in HR, finance, and 
            customer service that could benefit from AI automation.
            """
            
            data_sources = ["hr_systems", "financial_data", "customer_service_logs", "process_metrics"]
            
            analytics_result = self.client.analytics_query(operations_query, data_sources)
            
            print(f"✅ Operational Analysis Complete")
            
            if 'insights' in analytics_result:
                insights = analytics_result['insights']
                print("📊 Key Insights:")
                for insight in insights[:3]:
                    print(f"   • {insight.get('description', 'Unknown insight')}")
            
            if 'recommendations' in analytics_result:
                recommendations = analytics_result['recommendations']
                print("🎯 Optimization Opportunities:")
                for rec in recommendations[:3]:
                    print(f"   • {rec.get('area', 'Unknown')}: {rec.get('potential_improvement', 'Unknown')} improvement")
            
            # Process automation recommendations
            automation_query = """
            Recommend specific automation opportunities for our enterprise operations, 
            including ROI estimates and implementation complexity.
            """
            
            context = {
                "domain": "process_automation",
                "focus": "high_roi_low_complexity",
                "departments": ["hr", "finance", "customer_service"]
            }
            
            automation_result = self.client.agi_reasoning(automation_query, context)
            
            if 'recommendations' in automation_result:
                recommendations = automation_result['recommendations']
                print(f"🤖 Automation Strategy: {recommendations.get('primary_strategy', 'Not specified')}")
                print(f"💰 Expected ROI: {recommendations.get('roi_estimate', 'Not specified')}")
            
        except Exception as e:
            print(f"❌ Error in operational optimization demo: {e}")

def main():
    """
    Main function to run the enterprise integration demonstration
    """
    print("🏢 AGI-NARI Enterprise Integration Demo")
    print("Demonstrating how enterprises can connect and integrate with the AGI-NARI system")
    print("=" * 80)
    
    # Create and run the demo
    demo = EnterpriseIntegrationDemo()
    demo.run_comprehensive_demo()
    
    print("\n📚 Integration Resources:")
    print("• API Documentation: https://docs.agi-nari.com/api")
    print("• SDK Downloads: https://github.com/agi-nari/enterprise-sdks")
    print("• Support Portal: https://support.agi-nari.com")
    print("• Enterprise Sales: enterprise@agi-nari.com")

if __name__ == "__main__":
    main()

