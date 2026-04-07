"""
config/profile_manager.py
Loads Hot-Swappable Engine Profiles into os.environ.
If an ACTIVE_PROFILE is defined in .env, this overrides the default environment variables with the JSON profile defaults.
"""
import os
import json
import logging

def load_engine_profile(base_path: str) -> None:
    active_profile = os.getenv("ACTIVE_PROFILE", "")
    if not active_profile:
        return  # No profile selected, run with defaults from .env
        
    profile_path = os.path.join(base_path, "config", "profiles", f"{active_profile}.json")
    
    if not os.path.exists(profile_path):
        logging.getLogger("ProfileManager").warning(f"Profile {active_profile} not found at {profile_path}. Falling back to .env defaults.")
        return
        
    try:
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
            
        for key, value in profile_data.items():
            # Inject directly into os.environ so all subsequent os.getenv() calls receive it
            os.environ[key] = str(value)
            
        logging.getLogger("ProfileManager").info(f"🚀 ENGINE PROFILE LOADED: {active_profile.upper()}")
    except Exception as e:
        logging.getLogger("ProfileManager").error(f"Failed to load profile {active_profile}: {e}")
