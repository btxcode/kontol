import os
from datetime import timedelta

class Config:
    """Base configuration."""
    # Base directory for the application
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Directory for storing scan results
    RESULTS_DIR = os.path.join(BASE_DIR, 'scan_results')
    
    # API Settings
    API_PREFIX = '/apiv1'
    
    # Scan Settings
    SCAN_TIMEOUT = 300  # seconds
    MAX_CONCURRENT_SCANS = 3
    SCAN_COOLDOWN = timedelta(minutes=5)
    
    # Result Storage Settings
    MAX_RESULTS_PER_COMPANY = 1000
    RESULTS_RETENTION_DAYS = 90
    
    # Database configuration
    DB_HOST = 'localhost'
    DB_USER = 'newuser'
    DB_PASSWORD = 'newpassword'
    DB_NAME = 'kamehameha_scanner'
    
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
    
    # Directory Structure
    @staticmethod
    def get_company_dir(company_name):
        """Get the directory path for a company's scan results."""
        return os.path.join(Config.RESULTS_DIR, company_name)
    
    @staticmethod
    def get_date_dir(company_name, date_str):
        """Get the directory path for a specific date's scan results."""
        return os.path.join(Config.get_company_dir(company_name), date_str)
    
    @staticmethod
    def get_result_file(company_name, date_str, time_str):
        """Get the file path for a specific scan result."""
        return os.path.join(
            Config.get_date_dir(company_name, date_str),
            f'{time_str}.json'
        )

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

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'default')
    return config.get(env, config['default'])
