import os
from datetime import timedelta
from typing import Optional

class Config:
    """Base configuration with environment variable support."""
    
    # Base directory for the application
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Directory for storing scan results
    RESULTS_DIR = os.path.join(BASE_DIR, 'scan_results')
    
    # API Settings
    API_PREFIX = '/apiv1'
    
    # Scan Settings
    SCAN_TIMEOUT = int(os.getenv('SCAN_TIMEOUT', '300'))  # seconds
    MAX_CONCURRENT_SCANS = int(os.getenv('MAX_CONCURRENT_SCANS', '3'))
    SCAN_COOLDOWN = timedelta(minutes=int(os.getenv('SCAN_COOLDOWN_MINUTES', '5')))
    
    # Result Storage Settings
    MAX_RESULTS_PER_COMPANY = int(os.getenv('MAX_RESULTS_PER_COMPANY', '1000'))
    RESULTS_RETENTION_DAYS = int(os.getenv('RESULTS_RETENTION_DAYS', '90'))
    
    # Database configuration with environment variable support
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'scanner_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'secure_password')
    DB_NAME = os.getenv('DB_NAME', 'kamehameha_scanner')
    
    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
    
    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', os.path.join(BASE_DIR, 'scanner.log'))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # seconds
    
    # Severity Levels and Weights
    SEVERITY_LEVELS = {
        'critical': {
            'weight': 5,
            'color': '#ef4444',  # red-500
            'threshold': 9.0
        },
        'high': {
            'weight': 4,
            'color': '#f97316',  # orange-500
            'threshold': 7.0
        },
        'medium': {
            'weight': 3,
            'color': '#f59e0b',  # amber-500
            'threshold': 4.0
        },
        'low': {
            'weight': 2,
            'color': '#10b981',  # emerald-500
            'threshold': 0.1
        },
        'info': {
            'weight': 1,
            'color': '#3b82f6',  # blue-500
            'threshold': 0.0
        }
    }
    
    # Chart Colors
    CHART_COLORS = {
        'critical': '#ef4444',  # red-500
        'high': '#f97316',      # orange-500
        'medium': '#f59e0b',    # amber-500
        'low': '#10b981',       # emerald-500
        'info': '#3b82f6'       # blue-500
    }
    
    # Input validation
    ALLOWED_DOMAIN_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-"
    MAX_DOMAIN_LENGTH = 253
    MAX_COMPANY_NAME_LENGTH = 100
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    @classmethod
    def validate_domain(cls, domain: str) -> bool:
        """Validate domain name input."""
        if not domain or len(domain) > cls.MAX_DOMAIN_LENGTH:
            return False
        
        # Check for valid characters
        for char in domain:
            if char not in cls.ALLOWED_DOMAIN_CHARS:
                return False
        
        # Basic domain structure validation
        if domain.startswith('.') or domain.endswith('.') or domain.startswith('-') or domain.endswith('-'):
            return False
        
        # Check for at least one dot
        if '.' not in domain:
            return False
        
        return True
    
    @classmethod
    def validate_company_name(cls, name: str) -> bool:
        """Validate company name input."""
        if not name or len(name) > cls.MAX_COMPANY_NAME_LENGTH:
            return False
        
        # Allow alphanumeric, spaces, hyphens, and underscores
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_"
        for char in name:
            if char not in allowed_chars:
                return False
        
        return True
    
    @staticmethod
    def get_company_dir(company_name: str) -> str:
        """Get the directory path for a company's scan results."""
        return os.path.join(Config.RESULTS_DIR, company_name)
    
    @staticmethod
    def get_date_dir(company_name: str, date_str: str) -> str:
        """Get the directory path for a specific date's scan results."""
        return os.path.join(Config.get_company_dir(company_name), date_str)
    
    @staticmethod
    def get_result_file(company_name: str, date_str: str, time_str: str) -> str:
        """Get the file path for a specific scan result."""
        return os.path.join(
            Config.get_date_dir(company_name, date_str),
            f'{time_str}.json'
        )
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL."""
        return f"mariadb+mariadbconnector://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    SCAN_TIMEOUT = 60  # shorter timeout for development
    MAX_CONCURRENT_SCANS = 1
    SCAN_COOLDOWN = timedelta(seconds=30)
    
    # Shorter retention for development
    RESULTS_RETENTION_DAYS = 7
    
    # Development database
    DB_NAME = os.getenv('DB_NAME', 'kamehameha_scanner_dev')
    
    # More permissive CORS for development
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000', 'http://127.0.0.1:5000']

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    
    # Test-specific settings
    RESULTS_DIR = os.path.join(Config.BASE_DIR, 'test_results')
    SCAN_TIMEOUT = 5
    MAX_CONCURRENT_SCANS = 1
    SCAN_COOLDOWN = timedelta(seconds=1)
    
    # Minimal retention for testing
    RESULTS_RETENTION_DAYS = 1
    MAX_RESULTS_PER_COMPANY = 10
    
    # Test database
    DB_NAME = os.getenv('DB_NAME', 'kamehameha_scanner_test')
    
    # Disable some security features for testing
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret-key'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SCAN_TIMEOUT = 600  # longer timeout for production
    MAX_CONCURRENT_SCANS = 5
    SCAN_COOLDOWN = timedelta(minutes=15)
    
    # Longer retention for production
    RESULTS_RETENTION_DAYS = 365
    MAX_RESULTS_PER_COMPANY = 10000
    
    # Stricter security for production
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else []
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 50
    RATE_LIMIT_WINDOW = 3600

class DockerConfig(ProductionConfig):
    """Configuration for Docker environment."""
    # Docker-specific database settings
    DB_HOST = os.getenv('DB_HOST', 'db')
    DB_PORT = int(os.getenv('DB_PORT', '3306'))
    DB_USER = os.getenv('DB_USER', 'scanner_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'scanner_password')
    DB_NAME = os.getenv('DB_NAME', 'kamehameha_scanner')
    
    # Docker-specific settings
    RESULTS_DIR = os.getenv('RESULTS_DIR', '/app/scan_results')
    
    # Docker networking
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'default')
    
    # Special case for Docker
    if os.getenv('DOCKER_ENV'):
        env = 'docker'
    
    return config.get(env, config['default'])

def create_env_file_example():
    """Create an example .env file."""
    env_example = """# Kamehameha Scanner Configuration
# Copy this file to .env and modify as needed

# Environment
FLASK_ENV=development
DOCKER_ENV=false

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=scanner_user
DB_PASSWORD=your_secure_password_here
DB_NAME=kamehameha_scanner

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# Application Settings
SCAN_TIMEOUT=300
MAX_CONCURRENT_SCANS=3
SCAN_COOLDOWN_MINUTES=5
MAX_RESULTS_PER_COMPANY=1000
RESULTS_RETENTION_DAYS=90

# Logging
LOG_LEVEL=INFO
LOG_FILE=scanner.log

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_example)
    
    print("Example .env file created as .env.example")

if __name__ == '__main__':
    create_env_file_example()