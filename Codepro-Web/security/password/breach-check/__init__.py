"""Breach and Common Password Checker."""
COMMON_WEAK_PASSWORDS = {
    '123456', 'password', '12345678', 'qwerty', '123456789', '12345', '1234', '111111',
    'admin123', 'admin', 'welcome', 'login', 'coding_oj', 'password123', 'iloveyou',
    'master', 'secret', 'letmein', 'monkey', 'dragon', 'football', 'starwars'
}

class BreachChecker:
    @staticmethod
    def is_common_password(password: str) -> bool:
        pwd_lower = password.strip().lower()
        if pwd_lower in COMMON_WEAK_PASSWORDS:
            return True
        # Check repeated characters like "aaaaaaa" or "1111111"
        if len(password) >= 6 and len(set(password)) <= 2:
            return True
        return False
