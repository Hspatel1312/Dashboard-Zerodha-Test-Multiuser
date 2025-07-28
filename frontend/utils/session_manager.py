# frontend/utils/session_manager.py
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

class SessionManager:
    """Manages user session state and authentication"""
    
    def __init__(self):
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session state variables"""
        if 'user_authenticated' not in st.session_state:
            st.session_state.user_authenticated = False
        
        if 'user_name' not in st.session_state:
            st.session_state.user_name = None
            
        if 'auth_time' not in st.session_state:
            st.session_state.auth_time = None
            
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('user_authenticated', False)
    
    def get_user_name(self) -> str:
        """Get authenticated user name"""
        return st.session_state.get('user_name', 'Guest')
    
    def get_auth_time(self) -> Optional[datetime]:
        """Get authentication time"""
        return st.session_state.get('auth_time')
    
    def get_session_duration(self) -> str:
        """Get formatted session duration"""
        auth_time = self.get_auth_time()
        if not auth_time:
            return "Not logged in"
        
        duration = datetime.now() - auth_time
        if duration.total_seconds() < 60:
            return f"{int(duration.total_seconds())}s"
        elif duration.total_seconds() < 3600:
            return f"{int(duration.total_seconds() / 60)}m"
        else:
            return f"{int(duration.total_seconds() / 3600)}h"
    
    def logout(self):
        """Clear session and logout"""
        keys_to_clear = [
            'user_authenticated', 'user_name', 'auth_time',
            'last_refresh', 'cached_data', 'portfolio_data'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def refresh_session(self):
        """Refresh session timestamp"""
        st.session_state.last_refresh = datetime.now()
    
    def get_last_refresh(self) -> datetime:
        """Get last refresh time"""
        return st.session_state.get('last_refresh', datetime.now())