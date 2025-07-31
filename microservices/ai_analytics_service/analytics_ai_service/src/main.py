import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import openai

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from src.models.user import db

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'ai-analytics-service-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Initialize OpenAI client (using environment variables)
openai.api_key = os.getenv('OPENAI_API_KEY')
openai.api_base = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')

with app.app_context():
    db.create_all()

class AIAnalyticsProcessor:
    """Advanced AI-powered analytics and predictive capabilities"""
    
    @staticmethod
    def generate_sample_data(data_type: str, size: int = 100) -> List[Dict]:
        """Generate realistic sample data for testing"""
        np.random.seed(42)  # For reproducible results
        
        if data_type == "sales":
            dates = pd.date_range(start='2024-01-01', periods=size, freq='D')
            base_sales = 1000
            trend = np.linspace(0, 200, size)
            seasonal = 100 * np.sin(2 * np.pi * np.arange(size) / 30)
            noise = np.random.normal(0, 50, size)
            sales = base_sales + trend + seasonal + noise
            
            return [
                {
                    "date": dates[i].strftime('%Y-%m-%d'),
                    "sales": max(0, int(sales[i])),
                    "region": np.random.choice(["North", "South", "East", "West"]),
                    "product": np.random.choice(["Product A", "Product B", "Product C"])
                }
                for i in range(size)
            ]
        
        elif data_type == "users":
            dates = pd.date_range(start='2024-01-01', periods=size, freq='D')
            base_users = 500
            growth = np.linspace(0, 300, size)
            weekly_pattern = 50 * np.sin(2 * np.pi * np.arange(size) / 7)
            noise = np.random.normal(0, 20, size)
            active_users = base_users + growth + weekly_pattern + noise
            
            return [
                {
                    "date": dates[i].strftime('%Y-%m-%d'),
                    "active_users": max(0, int(active_users[i])),
                    "new_users": max(0, int(np.random.normal(50, 15))),
                    "platform": np.random.choice(["web", "mobile", "desktop"])
                }
                for i in range(size)
            ]
        
        else:
            return []
    
    @staticmethod
    def analyze_trends(data: List[Dict], metric: str) -> Dict:
        """Analyze trends in time series data"""
        try:
            if not data or metric not in data[0]:
                return {"error": "Invalid data or metric"}
            
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
            
            values = df[metric].values
            
            # Calculate trend statistics
            if len(values) > 1:
                trend_slope = np.polyfit(range(len(values)), values, 1)[0]
                trend_direction = "increasing" if trend_slope > 0 else "decreasing" if trend_slope < 0 else "stable"
            else:
                trend_slope = 0
                trend_direction = "stable"
            
            # Calculate statistics
            stats = {
                "mean": float(np.mean(values)),
                "median": float(np.median(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "trend_slope": float(trend_slope),
                "trend_direction": trend_direction,
                "data_points": len(values)
            }
            
            # Calculate percentage change
            if len(values) >= 2:
                first_value = values[0]
                last_value = values[-1]
                if first_value != 0:
                    percent_change = ((last_value - first_value) / first_value) * 100
                else:
                    percent_change = 0
                stats["percent_change"] = float(percent_change)
            
            return stats
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def predict_future_values(data: List[Dict], metric: str, periods: int = 30) -> Dict:
        """Predict future values using AI and statistical methods"""
        try:
            if not data or metric not in data[0]:
                return {"error": "Invalid data or metric"}
            
            df = pd.DataFrame(data)
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date')
            
            values = df[metric].values
            
            # Simple linear trend prediction
            if len(values) > 1:
                x = np.arange(len(values))
                coeffs = np.polyfit(x, values, 1)
                
                # Predict future values
                future_x = np.arange(len(values), len(values) + periods)
                predictions = np.polyval(coeffs, future_x)
                
                # Generate future dates
                if 'date' in df.columns:
                    last_date = df['date'].iloc[-1]
                    future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=periods, freq='D')
                    
                    predictions_list = [
                        {
                            "date": future_dates[i].strftime('%Y-%m-%d'),
                            "predicted_value": max(0, float(predictions[i])),
                            "confidence": max(0.1, 1.0 - (i / periods) * 0.5)  # Decreasing confidence
                        }
                        for i in range(periods)
                    ]
                else:
                    predictions_list = [
                        {
                            "period": i + 1,
                            "predicted_value": max(0, float(predictions[i])),
                            "confidence": max(0.1, 1.0 - (i / periods) * 0.5)
                        }
                        for i in range(periods)
                    ]
                
                return {
                    "predictions": predictions_list,
                    "model_type": "linear_trend",
                    "r_squared": float(np.corrcoef(x, values)[0, 1] ** 2) if len(values) > 1 else 0
                }
            else:
                return {"error": "Insufficient data for prediction"}
                
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def detect_anomalies(data: List[Dict], metric: str, threshold: float = 2.0) -> Dict:
        """Detect anomalies in data using statistical methods"""
        try:
            if not data or metric not in data[0]:
                return {"error": "Invalid data or metric"}
            
            df = pd.DataFrame(data)
            values = df[metric].values
            
            # Calculate z-scores
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                return {"anomalies": [], "total_anomalies": 0}
            
            z_scores = np.abs((values - mean_val) / std_val)
            anomaly_indices = np.where(z_scores > threshold)[0]
            
            anomalies = []
            for idx in anomaly_indices:
                anomaly = {
                    "index": int(idx),
                    "value": float(values[idx]),
                    "z_score": float(z_scores[idx]),
                    "severity": "high" if z_scores[idx] > 3 else "medium"
                }
                
                if 'date' in df.columns:
                    anomaly["date"] = df.iloc[idx]['date'].strftime('%Y-%m-%d') if pd.notnull(df.iloc[idx]['date']) else None
                
                anomalies.append(anomaly)
            
            return {
                "anomalies": anomalies,
                "total_anomalies": len(anomalies),
                "threshold_used": threshold,
                "mean": float(mean_val),
                "std": float(std_val)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def ai_insights(data: List[Dict], context: str = "") -> Dict:
        """Generate AI-powered insights from data"""
        try:
            # Prepare data summary for AI analysis
            df = pd.DataFrame(data)
            summary = {
                "total_records": len(df),
                "columns": list(df.columns),
                "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
                "sample_data": df.head(5).to_dict('records') if len(df) > 0 else []
            }
            
            # Add basic statistics for numeric columns
            for col in summary["numeric_columns"]:
                summary[f"{col}_stats"] = {
                    "mean": float(df[col].mean()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "std": float(df[col].std())
                }
            
            prompt = f"""
            Analyze this dataset and provide business insights:
            
            Context: {context}
            Data Summary: {json.dumps(summary, indent=2)}
            
            Please provide insights in JSON format with:
            - key_findings: array of important discoveries
            - recommendations: array of actionable recommendations
            - trends: description of trends observed
            - risks: potential risks or concerns
            - opportunities: business opportunities identified
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data analyst expert. Provide business insights in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.4
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except:
                return {
                    "key_findings": ["AI analysis completed"],
                    "recommendations": ["Review the data patterns"],
                    "trends": "Analysis in progress",
                    "risks": "None identified",
                    "opportunities": "Further analysis recommended",
                    "raw_response": result
                }
                
        except Exception as e:
            return {
                "key_findings": ["Error in AI analysis"],
                "recommendations": ["Check data format"],
                "trends": "Unable to analyze",
                "risks": "Data quality issues",
                "opportunities": "Fix data issues first",
                "error": str(e)
            }

# AI Analytics API Routes
@app.route('/api/analytics/trends', methods=['POST'])
def analyze_trends():
    """Analyze trends in time series data"""
    try:
        data = request.get_json()
        if not data or 'data' not in data or 'metric' not in data:
            return jsonify({"error": "Data and metric are required"}), 400
        
        dataset = data['data']
        metric = data['metric']
        
        if not isinstance(dataset, list) or len(dataset) == 0:
            return jsonify({"error": "Data must be a non-empty list"}), 400
        
        result = AIAnalyticsProcessor.analyze_trends(dataset, metric)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Analytics Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/predict', methods=['POST'])
def predict_values():
    """Predict future values"""
    try:
        data = request.get_json()
        if not data or 'data' not in data or 'metric' not in data:
            return jsonify({"error": "Data and metric are required"}), 400
        
        dataset = data['data']
        metric = data['metric']
        periods = data.get('periods', 30)
        
        if not isinstance(dataset, list) or len(dataset) == 0:
            return jsonify({"error": "Data must be a non-empty list"}), 400
        
        result = AIAnalyticsProcessor.predict_future_values(dataset, metric, periods)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Analytics Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/anomalies', methods=['POST'])
def detect_anomalies():
    """Detect anomalies in data"""
    try:
        data = request.get_json()
        if not data or 'data' not in data or 'metric' not in data:
            return jsonify({"error": "Data and metric are required"}), 400
        
        dataset = data['data']
        metric = data['metric']
        threshold = data.get('threshold', 2.0)
        
        if not isinstance(dataset, list) or len(dataset) == 0:
            return jsonify({"error": "Data must be a non-empty list"}), 400
        
        result = AIAnalyticsProcessor.detect_anomalies(dataset, metric, threshold)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Analytics Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/insights', methods=['POST'])
def generate_insights():
    """Generate AI-powered insights"""
    try:
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "Data is required"}), 400
        
        dataset = data['data']
        context = data.get('context', '')
        
        if not isinstance(dataset, list) or len(dataset) == 0:
            return jsonify({"error": "Data must be a non-empty list"}), 400
        
        result = AIAnalyticsProcessor.ai_insights(dataset, context)
        result['timestamp'] = datetime.utcnow().isoformat()
        result['service'] = 'AI Analytics Service'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/sample-data', methods=['GET'])
def get_sample_data():
    """Generate sample data for testing"""
    try:
        data_type = request.args.get('type', 'sales')
        size = int(request.args.get('size', 100))
        
        if size > 1000:
            size = 1000  # Limit size
        
        sample_data = AIAnalyticsProcessor.generate_sample_data(data_type, size)
        
        return jsonify({
            "data": sample_data,
            "type": data_type,
            "size": len(sample_data),
            "timestamp": datetime.utcnow().isoformat(),
            "service": "AI Analytics Service"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "service": "AI Analytics Service",
        "status": "healthy",
        "version": "2.0.0",
        "capabilities": [
            "trend_analysis",
            "predictive_modeling",
            "anomaly_detection",
            "ai_insights_generation",
            "sample_data_generation"
        ],
        "ai_model": "GPT-3.5-turbo",
        "timestamp": datetime.utcnow().isoformat()
    })

# Service info endpoint
@app.route('/api/info')
def service_info():
    return jsonify({
        "service_name": "AI Analytics and Predictive Service",
        "description": "Advanced AI-powered analytics, predictions, and business insights",
        "version": "2.0.0",
        "ai_features": [
            "Time Series Trend Analysis",
            "Predictive Modeling and Forecasting",
            "Statistical Anomaly Detection",
            "AI-Powered Business Insights",
            "Sample Data Generation for Testing"
        ],
        "endpoints": [
            "/api/analytics/trends",
            "/api/analytics/predict",
            "/api/analytics/anomalies",
            "/api/analytics/insights",
            "/api/analytics/sample-data"
        ],
        "models_used": ["GPT-3.5-turbo", "Linear Regression", "Statistical Analysis"],
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)

