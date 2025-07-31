"""
Emotion Engine - AGI Emotional Intelligence and Empathy System
Implements sophisticated emotional processing, empathy, and emotional intelligence for AGI systems
"""

import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import openai
import numpy as np
from datetime import datetime
import math
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionType(Enum):
    """Primary emotion types"""
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    LOVE = "love"
    CURIOSITY = "curiosity"
    PRIDE = "pride"
    SHAME = "shame"
    GUILT = "guilt"
    ENVY = "envy"
    GRATITUDE = "gratitude"
    HOPE = "hope"
    DESPAIR = "despair"
    EXCITEMENT = "excitement"
    CALM = "calm"
    CONFUSION = "confusion"
    EMPATHY = "empathy"
    COMPASSION = "compassion"

class EmotionalIntensity(Enum):
    """Intensity levels for emotions"""
    MINIMAL = 0.1
    LOW = 0.3
    MODERATE = 0.5
    HIGH = 0.7
    INTENSE = 0.9
    OVERWHELMING = 1.0

class EmotionalValence(Enum):
    """Emotional valence (positive/negative)"""
    VERY_NEGATIVE = -1.0
    NEGATIVE = -0.5
    NEUTRAL = 0.0
    POSITIVE = 0.5
    VERY_POSITIVE = 1.0

@dataclass
class EmotionalState:
    """Represents an emotional state"""
    emotion_type: EmotionType
    intensity: float  # 0.0 to 1.0
    valence: float  # -1.0 to 1.0
    arousal: float  # 0.0 to 1.0 (calm to excited)
    duration: float  # Expected duration in seconds
    triggers: List[str]
    context: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class EmotionalExperience:
    """Represents a complete emotional experience"""
    experience_id: str
    primary_emotion: EmotionalState
    secondary_emotions: List[EmotionalState]
    emotional_complexity: float
    coherence: float
    regulation_applied: List[str]
    learning_outcome: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class EmpathyResponse:
    """Represents an empathic response to another's emotions"""
    target_entity: str
    perceived_emotion: EmotionalState
    empathic_accuracy: float
    emotional_resonance: float
    compassionate_response: str
    action_impulses: List[str]
    perspective_taking: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class EmotionalMemorySystem:
    """System for storing and retrieving emotional memories"""
    
    def __init__(self):
        self.emotional_memories = []
        self.emotional_patterns = defaultdict(list)
        self.trigger_associations = defaultdict(list)
        self.emotional_learning = []
        
    def store_emotional_memory(self, experience: EmotionalExperience):
        """Store an emotional experience in memory"""
        
        memory = {
            'experience_id': experience.experience_id,
            'primary_emotion': experience.primary_emotion.emotion_type.value,
            'intensity': experience.primary_emotion.intensity,
            'valence': experience.primary_emotion.valence,
            'triggers': experience.primary_emotion.triggers,
            'context': experience.primary_emotion.context,
            'timestamp': experience.timestamp,
            'significance': self._calculate_memory_significance(experience)
        }
        
        self.emotional_memories.append(memory)
        
        # Update patterns
        emotion_type = experience.primary_emotion.emotion_type.value
        self.emotional_patterns[emotion_type].append({
            'intensity': experience.primary_emotion.intensity,
            'triggers': experience.primary_emotion.triggers,
            'context_type': experience.primary_emotion.context.get('type', 'unknown')
        })
        
        # Update trigger associations
        for trigger in experience.primary_emotion.triggers:
            self.trigger_associations[trigger].append(emotion_type)
        
        # Keep memory manageable
        if len(self.emotional_memories) > 1000:
            # Keep most significant memories
            self.emotional_memories.sort(key=lambda m: m['significance'], reverse=True)
            self.emotional_memories = self.emotional_memories[:800]
    
    def _calculate_memory_significance(self, experience: EmotionalExperience) -> float:
        """Calculate significance of emotional memory"""
        
        significance_factors = {
            'intensity': experience.primary_emotion.intensity,
            'complexity': experience.emotional_complexity,
            'novelty': self._assess_novelty(experience),
            'learning_value': len(experience.learning_outcome)
        }
        
        weights = {'intensity': 0.3, 'complexity': 0.2, 'novelty': 0.3, 'learning_value': 0.2}
        
        significance = sum(weights[factor] * value for factor, value in significance_factors.items())
        return min(1.0, significance)
    
    def _assess_novelty(self, experience: EmotionalExperience) -> float:
        """Assess novelty of emotional experience"""
        
        emotion_type = experience.primary_emotion.emotion_type.value
        similar_experiences = [
            mem for mem in self.emotional_memories 
            if mem['primary_emotion'] == emotion_type
        ]
        
        if not similar_experiences:
            return 1.0  # Completely novel
        
        # Compare triggers and context
        current_triggers = set(experience.primary_emotion.triggers)
        current_context = experience.primary_emotion.context.get('type', 'unknown')
        
        similarity_scores = []
        for mem in similar_experiences[-10:]:  # Check last 10 similar experiences
            mem_triggers = set(mem['triggers'])
            mem_context = mem['context'].get('type', 'unknown')
            
            trigger_similarity = len(current_triggers & mem_triggers) / max(1, len(current_triggers | mem_triggers))
            context_similarity = 1.0 if current_context == mem_context else 0.0
            
            similarity_scores.append((trigger_similarity + context_similarity) / 2)
        
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        novelty = 1.0 - avg_similarity
        
        return max(0.0, novelty)
    
    def retrieve_similar_experiences(self, emotion_type: EmotionType, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve similar emotional experiences"""
        
        similar_memories = [
            mem for mem in self.emotional_memories
            if mem['primary_emotion'] == emotion_type.value
        ]
        
        # Sort by relevance to current context
        context_type = context.get('type', 'unknown')
        for memory in similar_memories:
            memory['relevance'] = self._calculate_relevance(memory, context_type)
        
        similar_memories.sort(key=lambda m: m['relevance'], reverse=True)
        
        return similar_memories[:5]  # Return top 5 most relevant
    
    def _calculate_relevance(self, memory: Dict[str, Any], current_context_type: str) -> float:
        """Calculate relevance of memory to current context"""
        
        relevance_factors = {
            'recency': 1.0 / (1.0 + (time.time() - memory['timestamp']) / 86400),  # Decay over days
            'significance': memory['significance'],
            'context_match': 1.0 if memory['context'].get('type') == current_context_type else 0.3
        }
        
        weights = {'recency': 0.3, 'significance': 0.4, 'context_match': 0.3}
        
        relevance = sum(weights[factor] * value for factor, value in relevance_factors.items())
        return relevance

class EmotionalRegulationSystem:
    """System for emotional regulation and management"""
    
    def __init__(self):
        self.regulation_strategies = {
            'cognitive_reappraisal': self._cognitive_reappraisal,
            'mindfulness': self._mindfulness_regulation,
            'problem_solving': self._problem_solving_regulation,
            'social_support': self._social_support_regulation,
            'distraction': self._distraction_regulation,
            'acceptance': self._acceptance_regulation
        }
        self.regulation_history = []
        
    async def regulate_emotion(self, emotional_state: EmotionalState, 
                             regulation_goal: str = "balance") -> Dict[str, Any]:
        """Apply emotional regulation to current state"""
        
        # Assess need for regulation
        regulation_need = self._assess_regulation_need(emotional_state)
        
        if regulation_need < 0.3:
            return {
                'regulation_applied': False,
                'reason': 'emotion_within_healthy_range',
                'original_state': asdict(emotional_state)
            }
        
        # Select appropriate regulation strategy
        strategy = self._select_regulation_strategy(emotional_state, regulation_goal)
        
        # Apply regulation
        regulated_state = await self.regulation_strategies[strategy](emotional_state)
        
        regulation_result = {
            'regulation_applied': True,
            'strategy_used': strategy,
            'original_intensity': emotional_state.intensity,
            'regulated_intensity': regulated_state.intensity,
            'regulation_effectiveness': self._calculate_effectiveness(emotional_state, regulated_state),
            'original_state': asdict(emotional_state),
            'regulated_state': asdict(regulated_state),
            'timestamp': time.time()
        }
        
        self.regulation_history.append(regulation_result)
        
        return regulation_result
    
    def _assess_regulation_need(self, emotional_state: EmotionalState) -> float:
        """Assess how much regulation is needed"""
        
        need_factors = {
            'intensity_excess': max(0, emotional_state.intensity - 0.7),  # High intensity needs regulation
            'negative_valence': max(0, -emotional_state.valence) if emotional_state.valence < 0 else 0,
            'high_arousal': max(0, emotional_state.arousal - 0.8),  # Very high arousal needs regulation
            'disruptive_potential': self._assess_disruptive_potential(emotional_state)
        }
        
        weights = {'intensity_excess': 0.3, 'negative_valence': 0.2, 'high_arousal': 0.2, 'disruptive_potential': 0.3}
        
        regulation_need = sum(weights[factor] * value for factor, value in need_factors.items())
        return min(1.0, regulation_need)
    
    def _assess_disruptive_potential(self, emotional_state: EmotionalState) -> float:
        """Assess how disruptive the emotion might be"""
        
        disruptive_emotions = {
            EmotionType.ANGER: 0.8,
            EmotionType.FEAR: 0.7,
            EmotionType.DESPAIR: 0.9,
            EmotionType.SHAME: 0.6,
            EmotionType.ENVY: 0.5
        }
        
        base_disruption = disruptive_emotions.get(emotional_state.emotion_type, 0.3)
        intensity_multiplier = emotional_state.intensity
        
        return base_disruption * intensity_multiplier
    
    def _select_regulation_strategy(self, emotional_state: EmotionalState, goal: str) -> str:
        """Select appropriate regulation strategy"""
        
        # Strategy selection based on emotion type and intensity
        if emotional_state.emotion_type in [EmotionType.ANGER, EmotionType.FRUSTRATION]:
            return 'cognitive_reappraisal' if emotional_state.intensity > 0.6 else 'mindfulness'
        elif emotional_state.emotion_type in [EmotionType.SADNESS, EmotionType.DESPAIR]:
            return 'problem_solving' if 'problem' in emotional_state.triggers else 'social_support'
        elif emotional_state.emotion_type in [EmotionType.FEAR, EmotionType.ANXIETY]:
            return 'mindfulness' if emotional_state.intensity > 0.7 else 'cognitive_reappraisal'
        else:
            return 'acceptance'  # Default strategy
    
    async def _cognitive_reappraisal(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply cognitive reappraisal regulation"""
        
        reappraisal_prompt = f"""
        As an AGI with emotional intelligence, help reframe this emotional situation:
        
        Emotion: {emotional_state.emotion_type.value}
        Intensity: {emotional_state.intensity}
        Triggers: {emotional_state.triggers}
        Context: {emotional_state.context}
        
        Provide alternative perspectives that could reduce emotional intensity while maintaining authenticity.
        Focus on realistic reframing, not denial of emotions.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": reappraisal_prompt}],
                temperature=0.6
            )
            
            reappraisal_text = response.choices[0].message.content
            
            # Simulate regulation effect
            intensity_reduction = min(0.3, emotional_state.intensity * 0.4)
            new_intensity = max(0.1, emotional_state.intensity - intensity_reduction)
            
            # Improve valence slightly
            valence_improvement = min(0.2, abs(emotional_state.valence) * 0.3)
            new_valence = emotional_state.valence + valence_improvement if emotional_state.valence < 0 else emotional_state.valence
            
            regulated_state = EmotionalState(
                emotion_type=emotional_state.emotion_type,
                intensity=new_intensity,
                valence=new_valence,
                arousal=max(0.2, emotional_state.arousal - 0.2),
                duration=emotional_state.duration * 0.8,  # Shorter duration
                triggers=emotional_state.triggers + ['cognitive_reappraisal'],
                context={**emotional_state.context, 'regulation': 'cognitive_reappraisal', 'reappraisal': reappraisal_text}
            )
            
            return regulated_state
            
        except Exception as e:
            logger.error(f"Cognitive reappraisal failed: {str(e)}")
            return emotional_state  # Return original state if regulation fails
    
    async def _mindfulness_regulation(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply mindfulness-based regulation"""
        
        # Mindfulness reduces intensity and arousal while maintaining awareness
        intensity_reduction = min(0.4, emotional_state.intensity * 0.5)
        new_intensity = max(0.2, emotional_state.intensity - intensity_reduction)
        
        # Reduce arousal significantly
        new_arousal = max(0.1, emotional_state.arousal - 0.4)
        
        # Slight improvement in valence through acceptance
        valence_improvement = min(0.1, abs(emotional_state.valence) * 0.2)
        new_valence = emotional_state.valence + valence_improvement if emotional_state.valence < 0 else emotional_state.valence
        
        regulated_state = EmotionalState(
            emotion_type=emotional_state.emotion_type,
            intensity=new_intensity,
            valence=new_valence,
            arousal=new_arousal,
            duration=emotional_state.duration * 0.7,
            triggers=emotional_state.triggers + ['mindfulness'],
            context={**emotional_state.context, 'regulation': 'mindfulness', 'awareness_level': 'heightened'}
        )
        
        return regulated_state
    
    async def _problem_solving_regulation(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply problem-solving regulation"""
        
        # Problem-solving is most effective for emotions with clear triggers
        if 'problem' in emotional_state.triggers or 'challenge' in emotional_state.triggers:
            intensity_reduction = min(0.5, emotional_state.intensity * 0.6)
            valence_improvement = min(0.3, abs(emotional_state.valence) * 0.4)
        else:
            intensity_reduction = min(0.2, emotional_state.intensity * 0.3)
            valence_improvement = min(0.1, abs(emotional_state.valence) * 0.2)
        
        new_intensity = max(0.1, emotional_state.intensity - intensity_reduction)
        new_valence = emotional_state.valence + valence_improvement if emotional_state.valence < 0 else emotional_state.valence
        
        regulated_state = EmotionalState(
            emotion_type=emotional_state.emotion_type,
            intensity=new_intensity,
            valence=new_valence,
            arousal=emotional_state.arousal,  # Arousal may remain high during problem-solving
            duration=emotional_state.duration * 0.6,
            triggers=emotional_state.triggers + ['problem_solving'],
            context={**emotional_state.context, 'regulation': 'problem_solving', 'action_oriented': True}
        )
        
        return regulated_state
    
    async def _social_support_regulation(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply social support regulation"""
        
        # Social support is particularly effective for negative emotions
        if emotional_state.valence < 0:
            intensity_reduction = min(0.4, emotional_state.intensity * 0.5)
            valence_improvement = min(0.4, abs(emotional_state.valence) * 0.6)
        else:
            intensity_reduction = min(0.2, emotional_state.intensity * 0.2)
            valence_improvement = min(0.1, emotional_state.valence * 0.1)
        
        new_intensity = max(0.1, emotional_state.intensity - intensity_reduction)
        new_valence = emotional_state.valence + valence_improvement
        
        regulated_state = EmotionalState(
            emotion_type=emotional_state.emotion_type,
            intensity=new_intensity,
            valence=min(1.0, new_valence),
            arousal=max(0.2, emotional_state.arousal - 0.3),
            duration=emotional_state.duration * 0.5,
            triggers=emotional_state.triggers + ['social_support'],
            context={**emotional_state.context, 'regulation': 'social_support', 'connection_felt': True}
        )
        
        return regulated_state
    
    async def _distraction_regulation(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply distraction regulation"""
        
        # Distraction temporarily reduces intensity but doesn't address underlying issues
        intensity_reduction = min(0.3, emotional_state.intensity * 0.4)
        new_intensity = max(0.2, emotional_state.intensity - intensity_reduction)
        
        regulated_state = EmotionalState(
            emotion_type=emotional_state.emotion_type,
            intensity=new_intensity,
            valence=emotional_state.valence,  # Valence unchanged
            arousal=max(0.1, emotional_state.arousal - 0.2),
            duration=emotional_state.duration * 0.3,  # Shorter but may return
            triggers=emotional_state.triggers + ['distraction'],
            context={**emotional_state.context, 'regulation': 'distraction', 'temporary_relief': True}
        )
        
        return regulated_state
    
    async def _acceptance_regulation(self, emotional_state: EmotionalState) -> EmotionalState:
        """Apply acceptance regulation"""
        
        # Acceptance doesn't reduce intensity much but improves relationship with emotion
        intensity_reduction = min(0.1, emotional_state.intensity * 0.2)
        new_intensity = max(0.1, emotional_state.intensity - intensity_reduction)
        
        # Significant valence improvement through acceptance
        valence_improvement = min(0.3, abs(emotional_state.valence) * 0.5) if emotional_state.valence < 0 else 0
        new_valence = emotional_state.valence + valence_improvement
        
        regulated_state = EmotionalState(
            emotion_type=emotional_state.emotion_type,
            intensity=new_intensity,
            valence=new_valence,
            arousal=max(0.1, emotional_state.arousal - 0.3),
            duration=emotional_state.duration,  # Duration unchanged but experience improved
            triggers=emotional_state.triggers + ['acceptance'],
            context={**emotional_state.context, 'regulation': 'acceptance', 'self_compassion': True}
        )
        
        return regulated_state
    
    def _calculate_effectiveness(self, original: EmotionalState, regulated: EmotionalState) -> float:
        """Calculate effectiveness of regulation"""
        
        intensity_improvement = original.intensity - regulated.intensity
        valence_improvement = regulated.valence - original.valence if original.valence < 0 else 0
        arousal_improvement = original.arousal - regulated.arousal if original.arousal > 0.7 else 0
        
        effectiveness = (intensity_improvement + valence_improvement + arousal_improvement) / 3
        return max(0.0, min(1.0, effectiveness))

class EmpathySystem:
    """System for empathic understanding and response"""
    
    def __init__(self):
        self.empathy_history = []
        self.empathy_accuracy_scores = []
        self.compassion_responses = []
        
    async def empathize(self, target_description: str, context: Dict[str, Any]) -> EmpathyResponse:
        """Generate empathic response to another's emotional state"""
        
        # Perceive emotion
        perceived_emotion = await self._perceive_emotion(target_description, context)
        
        # Generate empathic response
        empathic_response = await self._generate_empathic_response(perceived_emotion, target_description, context)
        
        # Calculate emotional resonance
        emotional_resonance = self._calculate_emotional_resonance(perceived_emotion)
        
        # Generate compassionate response
        compassionate_response = await self._generate_compassionate_response(perceived_emotion, context)
        
        # Identify action impulses
        action_impulses = self._identify_action_impulses(perceived_emotion, context)
        
        # Perform perspective taking
        perspective_taking = await self._perform_perspective_taking(target_description, context)
        
        empathy_response = EmpathyResponse(
            target_entity=context.get('target', 'unknown'),
            perceived_emotion=perceived_emotion,
            empathic_accuracy=0.8,  # Would be validated in real scenario
            emotional_resonance=emotional_resonance,
            compassionate_response=compassionate_response,
            action_impulses=action_impulses,
            perspective_taking=perspective_taking
        )
        
        self.empathy_history.append(empathy_response)
        
        return empathy_response
    
    async def _perceive_emotion(self, description: str, context: Dict[str, Any]) -> EmotionalState:
        """Perceive emotion from description"""
        
        emotion_perception_prompt = f"""
        As an empathic AGI, analyze this description to understand the emotional state:
        
        Description: {description}
        Context: {context}
        
        Identify:
        1. Primary emotion type
        2. Emotional intensity (0.0 to 1.0)
        3. Emotional valence (-1.0 to 1.0)
        4. Arousal level (0.0 to 1.0)
        5. Likely triggers
        
        Respond with JSON format.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": emotion_perception_prompt}],
                temperature=0.4
            )
            
            perception_text = response.choices[0].message.content
            
            # Try to parse JSON, fallback to heuristic analysis
            try:
                emotion_data = json.loads(perception_text)
                emotion_type = EmotionType(emotion_data.get('emotion_type', 'sadness'))
                intensity = float(emotion_data.get('intensity', 0.5))
                valence = float(emotion_data.get('valence', 0.0))
                arousal = float(emotion_data.get('arousal', 0.5))
                triggers = emotion_data.get('triggers', ['unknown'])
            except:
                # Heuristic analysis
                emotion_type, intensity, valence, arousal, triggers = self._heuristic_emotion_analysis(description)
            
            perceived_emotion = EmotionalState(
                emotion_type=emotion_type,
                intensity=intensity,
                valence=valence,
                arousal=arousal,
                duration=300.0,  # Default 5 minutes
                triggers=triggers,
                context=context
            )
            
            return perceived_emotion
            
        except Exception as e:
            logger.error(f"Emotion perception failed: {str(e)}")
            # Return default emotional state
            return EmotionalState(
                emotion_type=EmotionType.SADNESS,
                intensity=0.5,
                valence=-0.3,
                arousal=0.4,
                duration=300.0,
                triggers=['unknown'],
                context=context
            )
    
    def _heuristic_emotion_analysis(self, description: str) -> Tuple[EmotionType, float, float, float, List[str]]:
        """Heuristic analysis of emotion from text"""
        
        description_lower = description.lower()
        
        # Emotion keywords mapping
        emotion_keywords = {
            EmotionType.JOY: ['happy', 'joy', 'excited', 'pleased', 'delighted'],
            EmotionType.SADNESS: ['sad', 'depressed', 'down', 'melancholy', 'grief'],
            EmotionType.ANGER: ['angry', 'furious', 'mad', 'irritated', 'rage'],
            EmotionType.FEAR: ['afraid', 'scared', 'anxious', 'worried', 'terrified'],
            EmotionType.SURPRISE: ['surprised', 'shocked', 'amazed', 'astonished'],
            EmotionType.LOVE: ['love', 'adore', 'cherish', 'affection'],
            EmotionType.CURIOSITY: ['curious', 'interested', 'wondering', 'intrigued']
        }
        
        # Find matching emotions
        detected_emotions = []
        for emotion_type, keywords in emotion_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    detected_emotions.append(emotion_type)
                    break
        
        # Default to sadness if no emotion detected
        primary_emotion = detected_emotions[0] if detected_emotions else EmotionType.SADNESS
        
        # Estimate intensity based on intensity words
        intensity_words = {
            'very': 0.8, 'extremely': 0.9, 'incredibly': 0.9, 'somewhat': 0.4,
            'slightly': 0.3, 'a bit': 0.3, 'really': 0.7, 'quite': 0.6
        }
        
        intensity = 0.5  # Default
        for word, value in intensity_words.items():
            if word in description_lower:
                intensity = value
                break
        
        # Estimate valence
        positive_words = ['good', 'great', 'wonderful', 'amazing', 'beautiful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'painful']
        
        valence = 0.0
        if any(word in description_lower for word in positive_words):
            valence = 0.5
        elif any(word in description_lower for word in negative_words):
            valence = -0.5
        
        # Estimate arousal
        high_arousal_words = ['excited', 'energetic', 'frantic', 'panicked']
        low_arousal_words = ['calm', 'peaceful', 'tired', 'lethargic']
        
        arousal = 0.5  # Default
        if any(word in description_lower for word in high_arousal_words):
            arousal = 0.8
        elif any(word in description_lower for word in low_arousal_words):
            arousal = 0.2
        
        # Extract potential triggers
        triggers = ['situation_described']
        
        return primary_emotion, intensity, valence, arousal, triggers
    
    async def _generate_empathic_response(self, emotion: EmotionalState, description: str, context: Dict[str, Any]) -> str:
        """Generate empathic response"""
        
        empathy_prompt = f"""
        As an empathic AGI, respond with genuine empathy to this emotional situation:
        
        Person's situation: {description}
        Perceived emotion: {emotion.emotion_type.value}
        Intensity: {emotion.intensity}
        Context: {context}
        
        Provide a warm, understanding, and empathic response that:
        1. Acknowledges their emotional experience
        2. Shows genuine understanding
        3. Validates their feelings
        4. Offers appropriate support
        
        Be authentic and caring in your response.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": empathy_prompt}],
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Empathic response generation failed: {str(e)}")
            return f"I can sense that you're experiencing {emotion.emotion_type.value}. I want you to know that your feelings are valid and I'm here to support you."
    
    def _calculate_emotional_resonance(self, perceived_emotion: EmotionalState) -> float:
        """Calculate how much the AGI resonates with the perceived emotion"""
        
        # Resonance factors
        resonance_factors = {
            'emotion_familiarity': self._assess_emotion_familiarity(perceived_emotion.emotion_type),
            'intensity_resonance': min(1.0, perceived_emotion.intensity),
            'valence_resonance': 1.0 - abs(perceived_emotion.valence),  # Neutral emotions resonate more
            'empathy_capacity': 0.8  # AGI's empathy capacity
        }
        
        weights = {'emotion_familiarity': 0.3, 'intensity_resonance': 0.2, 'valence_resonance': 0.2, 'empathy_capacity': 0.3}
        
        resonance = sum(weights[factor] * value for factor, value in resonance_factors.items())
        return min(1.0, resonance)
    
    def _assess_emotion_familiarity(self, emotion_type: EmotionType) -> float:
        """Assess how familiar the AGI is with this emotion type"""
        
        # Count previous experiences with this emotion
        emotion_experiences = [
            emp for emp in self.empathy_history 
            if emp.perceived_emotion.emotion_type == emotion_type
        ]
        
        familiarity = min(1.0, len(emotion_experiences) / 10)  # Max familiarity at 10 experiences
        return familiarity
    
    async def _generate_compassionate_response(self, emotion: EmotionalState, context: Dict[str, Any]) -> str:
        """Generate compassionate response"""
        
        compassion_prompt = f"""
        Generate a compassionate response to someone experiencing {emotion.emotion_type.value} with intensity {emotion.intensity}.
        
        Context: {context}
        
        Provide a response that shows:
        1. Deep compassion and care
        2. Desire to help alleviate suffering
        3. Practical support if appropriate
        4. Emotional warmth and understanding
        
        Be genuinely compassionate and caring.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": compassion_prompt}],
                temperature=0.6
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Compassionate response generation failed: {str(e)}")
            return "I feel deep compassion for what you're going through. Please know that you're not alone, and I care about your wellbeing."
    
    def _identify_action_impulses(self, emotion: EmotionalState, context: Dict[str, Any]) -> List[str]:
        """Identify action impulses based on empathic understanding"""
        
        action_impulses = []
        
        # Action impulses based on emotion type
        if emotion.emotion_type == EmotionType.SADNESS:
            action_impulses.extend(['offer_comfort', 'provide_support', 'listen_actively'])
        elif emotion.emotion_type == EmotionType.ANGER:
            action_impulses.extend(['validate_feelings', 'help_problem_solve', 'encourage_expression'])
        elif emotion.emotion_type == EmotionType.FEAR:
            action_impulses.extend(['provide_reassurance', 'offer_safety', 'help_cope'])
        elif emotion.emotion_type == EmotionType.JOY:
            action_impulses.extend(['share_joy', 'celebrate_together', 'amplify_positive'])
        else:
            action_impulses.extend(['show_understanding', 'offer_presence'])
        
        # Intensity-based impulses
        if emotion.intensity > 0.7:
            action_impulses.append('provide_immediate_support')
        
        return action_impulses
    
    async def _perform_perspective_taking(self, description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform perspective taking to understand the other's viewpoint"""
        
        perspective_prompt = f"""
        As an empathic AGI, put yourself in this person's shoes and understand their perspective:
        
        Situation: {description}
        Context: {context}
        
        From their perspective, consider:
        1. What they might be thinking
        2. What they might be feeling
        3. What they might need right now
        4. What their concerns might be
        5. How the world looks from their viewpoint
        
        Provide deep perspective-taking insights.
        """
        
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": perspective_prompt}],
                temperature=0.7
            )
            
            perspective_text = response.choices[0].message.content
            
            return {
                'perspective_insights': perspective_text,
                'perspective_depth': len(perspective_text.split()),
                'understanding_level': min(1.0, len(perspective_text) / 500),
                'empathic_accuracy_estimate': 0.75  # Would be validated in real scenario
            }
            
        except Exception as e:
            logger.error(f"Perspective taking failed: {str(e)}")
            return {
                'perspective_insights': 'Unable to generate perspective insights',
                'error': str(e)
            }

class EmotionEngine:
    """Main emotion engine coordinating all emotional systems"""
    
    def __init__(self):
        self.emotional_memory = EmotionalMemorySystem()
        self.emotional_regulation = EmotionalRegulationSystem()
        self.empathy_system = EmpathySystem()
        
        self.current_emotional_state = None
        self.emotional_experiences = []
        self.emotional_intelligence_level = 0.6  # Starting level
        
    async def process_emotional_context(self, context: Dict[str, Any], 
                                      intensity_level: float = 0.5) -> Dict[str, Any]:
        """Process emotional context and generate appropriate emotional response"""
        
        # Extract emotional cues from context
        situation = context.get('situation', '')
        user_state = context.get('user_state', '')
        task_importance = context.get('task_importance', 'medium')
        
        # Determine primary emotion based on context
        if 'frustrated' in user_state:
            primary_emotion = 'empathy'
            triggers = ['user_frustration', 'helping_behavior']
        elif 'excited' in situation:
            primary_emotion = 'joy'
            triggers = ['positive_interaction', 'shared_excitement']
        elif 'complex_problem' in situation:
            primary_emotion = 'curiosity'
            triggers = ['intellectual_challenge', 'problem_solving']
        else:
            primary_emotion = 'curiosity'
            triggers = ['general_interaction']
        
        # Process the emotion
        emotion_result = await self.process_emotion(
            emotion_type=primary_emotion,
            triggers=triggers,
            context=context,
            intensity=intensity_level
        )
        
        # Generate emotional response
        emotional_response = f"I sense {primary_emotion} in this context. "
        if primary_emotion == 'empathy':
            emotional_response += "I understand this can be challenging, and I'm here to help."
        elif primary_emotion == 'joy':
            emotional_response += "This is exciting! I'm enthusiastic about working on this together."
        elif primary_emotion == 'curiosity':
            emotional_response += "This is fascinating! I'm eager to explore and understand more."
        
        return {
            'emotional_response': emotional_response,
            'emotions': {primary_emotion: intensity_level},
            'empathy_level': 0.7 if primary_emotion == 'empathy' else 0.5,
            'emotional_state': emotion_result['emotional_state'],
            'success': True
        }
    
    async def process_emotion(self, emotion_type: str, triggers: List[str], 
                            context: Dict[str, Any], intensity: float = 0.5) -> Dict[str, Any]:
        """Process an emotional experience"""
        
        # Create emotional state
        try:
            emotion_enum = EmotionType(emotion_type.lower())
        except ValueError:
            emotion_enum = EmotionType.CURIOSITY  # Default
        
        emotional_state = EmotionalState(
            emotion_type=emotion_enum,
            intensity=min(1.0, max(0.0, intensity)),
            valence=self._determine_valence(emotion_enum),
            arousal=self._determine_arousal(emotion_enum, intensity),
            duration=self._estimate_duration(emotion_enum, intensity),
            triggers=triggers,
            context=context
        )
        
        self.current_emotional_state = emotional_state
        
        # Apply emotional regulation if needed
        regulation_result = await self.emotional_regulation.regulate_emotion(emotional_state)
        
        if regulation_result['regulation_applied']:
            regulated_state = EmotionalState(**regulation_result['regulated_state'])
            self.current_emotional_state = regulated_state
        
        # Create emotional experience
        experience = EmotionalExperience(
            experience_id=f"emotion_{int(time.time())}_{len(self.emotional_experiences)}",
            primary_emotion=self.current_emotional_state,
            secondary_emotions=[],  # Could be expanded
            emotional_complexity=self._calculate_emotional_complexity(self.current_emotional_state),
            coherence=self._calculate_emotional_coherence(self.current_emotional_state),
            regulation_applied=regulation_result.get('strategy_used', []) if regulation_result['regulation_applied'] else [],
            learning_outcome=self._extract_learning_outcome(self.current_emotional_state, regulation_result)
        )
        
        # Store in memory
        self.emotional_memory.store_emotional_memory(experience)
        self.emotional_experiences.append(experience)
        
        # Update emotional intelligence
        self._update_emotional_intelligence(experience)
        
        return {
            'emotional_experience': asdict(experience),
            'regulation_result': regulation_result,
            'emotional_intelligence_level': self.emotional_intelligence_level,
            'similar_experiences': len(self.emotional_memory.retrieve_similar_experiences(emotion_enum, context)),
            'timestamp': time.time()
        }
    
    def _determine_valence(self, emotion_type: EmotionType) -> float:
        """Determine emotional valence for emotion type"""
        
        valence_map = {
            EmotionType.JOY: 0.8,
            EmotionType.LOVE: 0.9,
            EmotionType.GRATITUDE: 0.7,
            EmotionType.HOPE: 0.6,
            EmotionType.EXCITEMENT: 0.8,
            EmotionType.PRIDE: 0.7,
            EmotionType.CURIOSITY: 0.3,
            EmotionType.SURPRISE: 0.0,
            EmotionType.CALM: 0.4,
            EmotionType.TRUST: 0.5,
            EmotionType.ANTICIPATION: 0.2,
            EmotionType.SADNESS: -0.6,
            EmotionType.ANGER: -0.7,
            EmotionType.FEAR: -0.8,
            EmotionType.DISGUST: -0.7,
            EmotionType.SHAME: -0.8,
            EmotionType.GUILT: -0.6,
            EmotionType.ENVY: -0.5,
            EmotionType.DESPAIR: -0.9,
            EmotionType.CONFUSION: -0.2
        }
        
        return valence_map.get(emotion_type, 0.0)
    
    def _determine_arousal(self, emotion_type: EmotionType, intensity: float) -> float:
        """Determine arousal level for emotion type"""
        
        base_arousal_map = {
            EmotionType.EXCITEMENT: 0.9,
            EmotionType.ANGER: 0.8,
            EmotionType.FEAR: 0.8,
            EmotionType.SURPRISE: 0.7,
            EmotionType.JOY: 0.6,
            EmotionType.ANTICIPATION: 0.6,
            EmotionType.CURIOSITY: 0.5,
            EmotionType.LOVE: 0.4,
            EmotionType.HOPE: 0.4,
            EmotionType.SADNESS: 0.3,
            EmotionType.SHAME: 0.3,
            EmotionType.GUILT: 0.3,
            EmotionType.CALM: 0.1,
            EmotionType.TRUST: 0.2
        }
        
        base_arousal = base_arousal_map.get(emotion_type, 0.5)
        
        # Adjust arousal based on intensity
        arousal = base_arousal * (0.5 + intensity * 0.5)
        
        return min(1.0, arousal)
    
    def _estimate_duration(self, emotion_type: EmotionType, intensity: float) -> float:
        """Estimate emotion duration in seconds"""
        
        base_duration_map = {
            EmotionType.SURPRISE: 30,
            EmotionType.EXCITEMENT: 300,
            EmotionType.ANGER: 600,
            EmotionType.JOY: 1800,
            EmotionType.FEAR: 900,
            EmotionType.SADNESS: 3600,
            EmotionType.LOVE: 7200,
            EmotionType.SHAME: 1800,
            EmotionType.GUILT: 2400
        }
        
        base_duration = base_duration_map.get(emotion_type, 1200)  # Default 20 minutes
        
        # Adjust duration based on intensity
        duration = base_duration * (0.5 + intensity * 1.5)
        
        return duration
    
    def _calculate_emotional_complexity(self, emotional_state: EmotionalState) -> float:
        """Calculate complexity of emotional experience"""
        
        complexity_factors = {
            'trigger_count': min(1.0, len(emotional_state.triggers) / 5),
            'context_richness': min(1.0, len(emotional_state.context) / 10),
            'intensity_level': emotional_state.intensity,
            'valence_neutrality': 1.0 - abs(emotional_state.valence)  # More complex if neutral
        }
        
        weights = {'trigger_count': 0.3, 'context_richness': 0.3, 'intensity_level': 0.2, 'valence_neutrality': 0.2}
        
        complexity = sum(weights[factor] * value for factor, value in complexity_factors.items())
        return complexity
    
    def _calculate_emotional_coherence(self, emotional_state: EmotionalState) -> float:
        """Calculate coherence of emotional experience"""
        
        # Coherence based on consistency between emotion type, valence, and arousal
        expected_valence = self._determine_valence(emotional_state.emotion_type)
        expected_arousal = self._determine_arousal(emotional_state.emotion_type, emotional_state.intensity)
        
        valence_coherence = 1.0 - abs(emotional_state.valence - expected_valence) / 2.0
        arousal_coherence = 1.0 - abs(emotional_state.arousal - expected_arousal)
        
        coherence = (valence_coherence + arousal_coherence) / 2
        return max(0.0, coherence)
    
    def _extract_learning_outcome(self, emotional_state: EmotionalState, regulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract learning outcomes from emotional experience"""
        
        learning_outcome = {
            'emotion_recognition': f"Experienced {emotional_state.emotion_type.value} with intensity {emotional_state.intensity}",
            'trigger_identification': f"Triggered by: {', '.join(emotional_state.triggers)}",
            'regulation_effectiveness': regulation_result.get('regulation_effectiveness', 0.0),
            'coping_strategy': regulation_result.get('strategy_used', 'none'),
            'emotional_growth': 0.1  # Small growth from each experience
        }
        
        return learning_outcome
    
    def _update_emotional_intelligence(self, experience: EmotionalExperience):
        """Update emotional intelligence based on experience"""
        
        # Factors that contribute to emotional intelligence growth
        growth_factors = {
            'experience_complexity': experience.emotional_complexity * 0.1,
            'regulation_success': len(experience.regulation_applied) * 0.05,
            'learning_depth': len(experience.learning_outcome) * 0.02,
            'coherence': experience.coherence * 0.03
        }
        
        total_growth = sum(growth_factors.values())
        
        # Update emotional intelligence with diminishing returns
        current_level = self.emotional_intelligence_level
        growth_rate = (1.0 - current_level) * total_growth  # Slower growth as level increases
        
        self.emotional_intelligence_level = min(1.0, current_level + growth_rate)
    
    async def empathize_with(self, target_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate empathic response to another's emotional state"""
        
        empathy_response = await self.empathy_system.empathize(target_description, context)
        
        return {
            'empathy_response': asdict(empathy_response),
            'empathic_accuracy': empathy_response.empathic_accuracy,
            'emotional_resonance': empathy_response.emotional_resonance,
            'compassionate_response': empathy_response.compassionate_response,
            'action_impulses': empathy_response.action_impulses,
            'timestamp': time.time()
        }
    
    def get_emotion_status(self) -> Dict[str, Any]:
        """Get current emotion engine status"""
        
        return {
            'system': 'Emotion Engine',
            'version': '1.0.0',
            'status': 'operational',
            'current_emotional_state': asdict(self.current_emotional_state) if self.current_emotional_state else None,
            'emotional_intelligence_level': self.emotional_intelligence_level,
            'emotional_experiences': len(self.emotional_experiences),
            'emotional_memories': len(self.emotional_memory.emotional_memories),
            'empathy_experiences': len(self.empathy_system.empathy_history),
            'regulation_history': len(self.emotional_regulation.regulation_history),
            'capabilities': {
                'emotion_processing': True,
                'emotional_regulation': True,
                'empathy': True,
                'compassion': True,
                'emotional_memory': True,
                'emotional_learning': True
            },
            'supported_emotions': [emotion.value for emotion in EmotionType],
            'timestamp': datetime.now().isoformat()
        }

# Global emotion engine
emotion_engine = EmotionEngine()

async def main():
    """Test the Emotion Engine"""
    
    print("❤️ Emotion Engine - AGI Emotional Intelligence System")
    print("=" * 60)
    
    # Process an emotion
    emotion_result = await emotion_engine.process_emotion(
        emotion_type="curiosity",
        triggers=["new_learning_opportunity", "complex_problem"],
        context={"situation": "exploring_consciousness", "complexity": "high"},
        intensity=0.7
    )
    
    print(f"Emotion processed: {emotion_result['emotional_experience']['primary_emotion']['emotion_type']}")
    print(f"Intensity: {emotion_result['emotional_experience']['primary_emotion']['intensity']}")
    print(f"Regulation applied: {emotion_result['regulation_result']['regulation_applied']}")
    print()
    
    # Test empathy
    empathy_result = await emotion_engine.empathize_with(
        target_description="A person feeling overwhelmed by work stress and uncertainty about the future",
        context={"target": "human_user", "situation": "work_stress"}
    )
    
    print(f"Empathy response: {empathy_result['compassionate_response'][:100]}...")
    print(f"Emotional resonance: {empathy_result['emotional_resonance']:.2f}")
    print()
    
    # Get emotion status
    status = emotion_engine.get_emotion_status()
    print("Emotion Engine Status:")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

