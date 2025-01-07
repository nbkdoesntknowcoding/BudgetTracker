from datetime import datetime, timedelta
import re

class AuthService:
    def __init__(self):
        self.allowed_domains = ['theboringpeople.in', 'myacolyte.in']
        self.login_attempts = {}
        self.max_attempts = 3
        self.lockout_duration = timedelta(minutes=15)
        self.session_duration = timedelta(hours=8)
    
    def is_email_allowed(self, email):
        """Check if email domain is allowed"""
        if not email or '@' not in email:
            return False
        
        # Email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False
            
        domain = email.split('@')[1]
        return domain in self.allowed_domains
    
    def check_login_attempts(self, email):
        """Check if account is locked due to too many attempts"""
        if email in self.login_attempts:
            attempts, last_attempt = self.login_attempts[email]
            if attempts >= self.max_attempts:
                if datetime.now() - last_attempt < self.lockout_duration:
                    return False
                else:
                    # Reset attempts after lockout period
                    self.login_attempts[email] = (0, datetime.now())
        return True
    
    def record_login_attempt(self, email, success):
        """Record login attempt"""
        attempts, _ = self.login_attempts.get(email, (0, datetime.now()))
        if success:
            self.login_attempts[email] = (0, datetime.now())
        else:
            self.login_attempts[email] = (attempts + 1, datetime.now())
    
    def get_remaining_attempts(self, email):
        """Get remaining login attempts"""
        attempts, _ = self.login_attempts.get(email, (0, datetime.now()))
        return max(0, self.max_attempts - attempts)
    
    def get_lockout_time(self, email):
        """Get remaining lockout time"""
        if email in self.login_attempts:
            attempts, last_attempt = self.login_attempts[email]
            if attempts >= self.max_attempts:
                time_passed = datetime.now() - last_attempt
                if time_passed < self.lockout_duration:
                    return self.lockout_duration - time_passed
        return timedelta(0)
    
    def check_session_validity(self, login_time):
        """Check if current session is still valid"""
        if not login_time:
            return False
        return datetime.now() - login_time < self.session_duration