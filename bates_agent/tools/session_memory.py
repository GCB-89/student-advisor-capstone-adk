"""
Session Management and Memory System for Bates Agent

Implements:
- Session state management using InMemorySessionService
- Long-term memory for student interactions
- Context compaction and management
- Student profile persistence
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.adk.runners import InMemorySessionService
from .observability import BatesLogger, monitor_performance, get_metrics
from pathlib import Path
import threading

logger = BatesLogger.get_logger(__name__)

class StudentProfile:
    """Represents a student's profile and interaction history"""
    
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.interests = []
        self.programs_viewed = []
        self.questions_asked = []
        self.recommendations_given = []
        self.interaction_count = 0
        self.preferences = {}
        
    def update_activity(self):
        """Update the last active timestamp"""
        self.last_active = datetime.now()
        self.interaction_count += 1
    
    def add_interest(self, interest: str):
        """Add a student interest"""
        if interest not in self.interests:
            self.interests.append(interest)
    
    def add_program_view(self, program: str):
        """Record that a student viewed a program"""
        if program not in self.programs_viewed:
            self.programs_viewed.append(program)
    
    def add_question(self, question: str, category: str = "general"):
        """Record a question asked by the student"""
        self.questions_asked.append({
            "question": question,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 50 questions for memory management
        if len(self.questions_asked) > 50:
            self.questions_asked = self.questions_asked[-50:]
    
    def add_recommendation(self, recommendation: str, context: str):
        """Record a recommendation given to the student"""
        self.recommendations_given.append({
            "recommendation": recommendation,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 20 recommendations
        if len(self.recommendations_given) > 20:
            self.recommendations_given = self.recommendations_given[-20:]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary"""
        return {
            "student_id": self.student_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "interests": self.interests,
            "programs_viewed": self.programs_viewed,
            "questions_asked": self.questions_asked,
            "recommendations_given": self.recommendations_given,
            "interaction_count": self.interaction_count,
            "preferences": self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StudentProfile':
        """Create profile from dictionary"""
        profile = cls(data["student_id"])
        profile.created_at = datetime.fromisoformat(data["created_at"])
        profile.last_active = datetime.fromisoformat(data["last_active"])
        profile.interests = data.get("interests", [])
        profile.programs_viewed = data.get("programs_viewed", [])
        profile.questions_asked = data.get("questions_asked", [])
        profile.recommendations_given = data.get("recommendations_given", [])
        profile.interaction_count = data.get("interaction_count", 0)
        profile.preferences = data.get("preferences", {})
        return profile

class BatesMemoryBank:
    """Long-term memory system for storing and retrieving student information"""
    
    def __init__(self, storage_path: str = "data/memory_bank"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, StudentProfile] = {}
        self.interaction_history: Dict[str, List[Dict]] = {}
        self._lock = threading.Lock()
        self.metrics = get_metrics()
        
        # Load existing profiles
        self._load_profiles()
    
    def _load_profiles(self):
        """Load existing student profiles from storage"""
        try:
            profiles_file = self.storage_path / "profiles.json"
            if profiles_file.exists():
                with open(profiles_file, 'r') as f:
                    data = json.load(f)
                    for student_id, profile_data in data.items():
                        self.profiles[student_id] = StudentProfile.from_dict(profile_data)
            
            # Load interaction history
            history_file = self.storage_path / "interactions.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    self.interaction_history = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
    
    def _save_profiles(self):
        """Save student profiles to storage"""
        try:
            with self._lock:
                # Save profiles
                profiles_data = {
                    student_id: profile.to_dict()
                    for student_id, profile in self.profiles.items()
                }
                
                with open(self.storage_path / "profiles.json", 'w') as f:
                    json.dump(profiles_data, f, indent=2)
                
                # Save interaction history
                with open(self.storage_path / "interactions.json", 'w') as f:
                    json.dump(self.interaction_history, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
    
    @monitor_performance("memory_get_profile")
    def get_or_create_profile(self, student_id: str) -> StudentProfile:
        """Get existing profile or create new one"""
        with self._lock:
            if student_id not in self.profiles:
                self.profiles[student_id] = StudentProfile(student_id)
                self.metrics.increment_counter("new_student_profiles")
            
            profile = self.profiles[student_id]
            profile.update_activity()
            return profile
    
    @monitor_performance("memory_store_interaction")
    def store_interaction(self, student_id: str, interaction_type: str, 
                         content: str, metadata: Optional[Dict] = None):
        """Store an interaction in memory"""
        with self._lock:
            if student_id not in self.interaction_history:
                self.interaction_history[student_id] = []
            
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "type": interaction_type,
                "content": content,
                "metadata": metadata or {}
            }
            
            self.interaction_history[student_id].append(interaction)
            
            # Limit history size per student
            if len(self.interaction_history[student_id]) > 100:
                self.interaction_history[student_id] = self.interaction_history[student_id][-100:]
            
            self.metrics.increment_counter("interactions_stored")
            
        # Auto-save periodically
        if self.metrics.counters.get("interactions_stored", 0) % 10 == 0:
            self._save_profiles()
    
    def get_student_context(self, student_id: str) -> Dict[str, Any]:
        """Get comprehensive context for a student"""
        profile = self.get_or_create_profile(student_id)
        recent_interactions = self.interaction_history.get(student_id, [])[-10:]  # Last 10
        
        return {
            "profile": profile.to_dict(),
            "recent_interactions": recent_interactions,
            "context_summary": self._generate_context_summary(profile, recent_interactions)
        }
    
    def _generate_context_summary(self, profile: StudentProfile, 
                                interactions: List[Dict]) -> str:
        """Generate a compact context summary for the agent"""
        summary_parts = []
        
        if profile.interests:
            summary_parts.append(f"Student interests: {', '.join(profile.interests[:3])}")
        
        if profile.programs_viewed:
            summary_parts.append(f"Programs viewed: {', '.join(profile.programs_viewed[-3:])}")
        
        if interactions:
            recent_topics = [i.get("metadata", {}).get("topic", "general") for i in interactions[-3:]]
            summary_parts.append(f"Recent topics: {', '.join(recent_topics)}")
        
        return "; ".join(summary_parts) if summary_parts else "New student interaction"

class BatesSessionManager:
    """Enhanced session management for the Bates Agent system"""
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.memory_bank = BatesMemoryBank()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.metrics = get_metrics()
    
    @monitor_performance("session_create")
    def create_session(self, student_id: Optional[str] = None) -> str:
        """Create a new session for a student"""
        session_id = str(uuid.uuid4())
        
        if not student_id:
            student_id = f"anonymous_{session_id[:8]}"
        
        with self._lock:
            session_data = {
                "session_id": session_id,
                "student_id": student_id,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "interaction_count": 0,
                "current_topic": None,
                "agent_context": {}
            }
            
            self.active_sessions[session_id] = session_data
            self.metrics.increment_counter("sessions_created")
        
        # Get student context from memory bank
        context = self.memory_bank.get_student_context(student_id)
        logger.info(f"Created session {session_id} for student {student_id}")
        
        return session_id
    
    @monitor_performance("session_get")
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        with self._lock:
            session = self.active_sessions.get(session_id)
            if session:
                session["last_activity"] = datetime.now()
                return session.copy()
        return None
    
    @monitor_performance("session_update")
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data"""
        with self._lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id].update(updates)
                self.active_sessions[session_id]["last_activity"] = datetime.now()
                self.metrics.increment_counter("sessions_updated")
    
    def record_interaction(self, session_id: str, interaction_type: str, 
                         content: str, agent_response: str = None):
        """Record an interaction in both session and long-term memory"""
        session = self.get_session(session_id)
        if not session:
            return
        
        student_id = session["student_id"]
        
        # Update session
        self.update_session(session_id, {
            "interaction_count": session["interaction_count"] + 1
        })
        
        # Store in long-term memory
        metadata = {
            "session_id": session_id,
            "agent_response": agent_response,
            "topic": session.get("current_topic", "general")
        }
        
        self.memory_bank.store_interaction(
            student_id, interaction_type, content, metadata
        )
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._lock:
            expired_sessions = [
                session_id for session_id, session_data in self.active_sessions.items()
                if session_data["last_activity"] < cutoff_time
            ]
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                self.metrics.increment_counter("sessions_expired")
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global session manager instance
session_manager = BatesSessionManager()