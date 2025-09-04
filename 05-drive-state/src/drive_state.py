"""
Drive State Management for User Mood/Needs Simulation
Implements bounded random walk with decay to baseline
"""

import json
import os
import random
import time
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class DriveState:
    """User drive state with 5 core drives"""
    user_id: str
    energy: float = 0.5  # Physical/energy level [0..1]
    sociability: float = 0.5  # Desire for social interaction [0..1]
    curiosity: float = 0.5  # Interest in learning/exploring [0..1]
    empathy_reserve: float = 0.5  # Capacity for emotional support [0..1]
    novelty_seek: float = 0.5  # Desire for new experiences [0..1]
    timestamp: float = 0.0  # Last update timestamp

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DriveState':
        """Create from dictionary"""
        return cls(**data)

    def clamp_values(self):
        """Ensure all drive values are clamped to [0..1]"""
        self.energy = max(0.0, min(1.0, self.energy))
        self.sociability = max(0.0, min(1.0, self.sociability))
        self.curiosity = max(0.0, min(1.0, self.curiosity))
        self.empathy_reserve = max(0.0, min(1.0, self.empathy_reserve))
        self.novelty_seek = max(0.0, min(1.0, self.novelty_seek))


class DriveStateManager:
    """Manages drive states with persistence and simulation"""

    def __init__(self, storage_file: str = "drive_states.json"):
        self.storage_file = storage_file
        self.states: Dict[str, DriveState] = {}
        self.baseline_decay_rate = 0.001  # Slow decay to baseline
        self.random_walk_step = 0.02  # Small random changes
        self.load_states()

    def load_states(self):
        """Load drive states from persistent storage"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for user_id, state_data in data.items():
                        self.states[user_id] = DriveState.from_dict(state_data)
            except (json.JSONDecodeError, KeyError):
                # Reset to empty if file is corrupted
                self.states = {}

    def save_states(self):
        """Save drive states to persistent storage"""
        data = {user_id: state.to_dict() for user_id, state in self.states.items()}
        with open(self.storage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_drive_state(self, user_id: str) -> DriveState:
        """Get or create drive state for user"""
        if user_id not in self.states:
            self.states[user_id] = DriveState(user_id=user_id, timestamp=time.time())

        state = self.states[user_id]

        # Apply time-based decay and random walk
        self._apply_time_decay(state)
        self._apply_random_walk(state)

        state.timestamp = time.time()
        self.save_states()

        return state

    def update_drive_state(self, user_id: str, deltas: Dict[str, float],
                          reason: str = "") -> DriveState:
        """Update drive state with deltas"""
        state = self.get_drive_state(user_id)

        # Apply deltas
        if 'energy' in deltas:
            state.energy += deltas['energy']
        if 'sociability' in deltas:
            state.sociability += deltas['sociability']
        if 'curiosity' in deltas:
            state.curiosity += deltas['curiosity']
        if 'empathy_reserve' in deltas:
            state.empathy_reserve += deltas['empathy_reserve']
        if 'novelty_seek' in deltas:
            state.novelty_seek += deltas['novelty_seek']

        # Clamp values to valid range
        state.clamp_values()
        state.timestamp = time.time()

        self.save_states()
        return state

    def _apply_time_decay(self, state: DriveState):
        """Apply slow decay toward baseline (0.5)"""
        current_time = time.time()
        time_diff = current_time - state.timestamp

        if time_diff > 0:
            # Decay factor based on time elapsed (more aggressive for testing)
            decay_factor = min(1.0, time_diff * self.baseline_decay_rate * 10)

            # Decay toward 0.5 baseline
            baseline = 0.5
            state.energy = state.energy + (baseline - state.energy) * decay_factor
            state.sociability = state.sociability + (baseline - state.sociability) * decay_factor
            state.curiosity = state.curiosity + (baseline - state.curiosity) * decay_factor
            state.empathy_reserve = state.empathy_reserve + (baseline - state.empathy_reserve) * decay_factor
            state.novelty_seek = state.novelty_seek + (baseline - state.novelty_seek) * decay_factor

    def _apply_random_walk(self, state: DriveState):
        """Apply small random changes (bounded random walk)"""
        # Small random changes in each direction
        state.energy += random.uniform(-self.random_walk_step, self.random_walk_step)
        state.sociability += random.uniform(-self.random_walk_step, self.random_walk_step)
        state.curiosity += random.uniform(-self.random_walk_step, self.random_walk_step)
        state.empathy_reserve += random.uniform(-self.random_walk_step, self.random_walk_step)
        state.novelty_seek += random.uniform(-self.random_walk_step, self.random_walk_step)

        # Clamp after random walk
        state.clamp_values()

    def get_style_policy(self, user_id: str) -> Dict[str, Any]:
        """Generate style hints based on current drive state"""
        state = self.get_drive_state(user_id)

        policy = {
            "energy_level": self._categorize_drive(state.energy),
            "social_style": self._categorize_drive(state.sociability),
            "curiosity_level": self._categorize_drive(state.curiosity),
            "empathy_approach": self._categorize_drive(state.empathy_reserve),
            "novelty_preference": self._categorize_drive(state.novelty_seek),
            "style_hints": self._generate_style_hints(state)
        }

        return policy

    def _categorize_drive(self, value: float) -> str:
        """Categorize drive value into descriptive levels"""
        if value < 0.25:
            return "very_low"
        elif value < 0.4:
            return "low"
        elif value < 0.6:
            return "moderate"
        elif value < 0.75:
            return "high"
        else:
            return "very_high"

    def _generate_style_hints(self, state: DriveState) -> List[str]:
        """Generate concise style hints based on drive state"""
        hints = []

        # Energy-based hints
        if state.energy < 0.3:
            hints.append("Keep responses brief and focused")
        elif state.energy > 0.7:
            hints.append("Provide detailed, energetic responses")

        # Sociability-based hints
        if state.sociability < 0.3:
            hints.append("Minimize social chit-chat")
        elif state.sociability > 0.7:
            hints.append("Include friendly, conversational elements")

        # Curiosity-based hints
        if state.curiosity < 0.3:
            hints.append("Stick to practical, direct information")
        elif state.curiosity > 0.7:
            hints.append("Include interesting facts and connections")

        # Empathy-based hints
        if state.empathy_reserve < 0.3:
            hints.append("Focus on solutions over emotional support")
        elif state.empathy_reserve > 0.7:
            hints.append("Show understanding and emotional awareness")

        # Novelty-based hints
        if state.novelty_seek < 0.3:
            hints.append("Use familiar, established approaches")
        elif state.novelty_seek > 0.7:
            hints.append("Introduce novel ideas and perspectives")

        return hints if hints else ["Maintain balanced, neutral communication style"]


# Global instance
drive_manager = DriveStateManager()
