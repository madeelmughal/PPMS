"""
Firebase Configuration Module
Initializes Firebase connection and provides access to database services.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db, firestore, auth

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def get_app_data_path():
    """Get the appropriate path for storing application data.
    
    For bundled exe: Uses a 'PPMS_Data' folder next to the exe
    For development: Uses the 'data' folder in the project
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled exe - store data next to the exe
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'PPMS_Data')
    else:
        # Running in development
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')


class MockFirestore:
    """Mock Firestore for offline/demo mode with persistent local storage."""
    
    # Path to store persistent data
    DATA_FILE = os.path.join(get_app_data_path(), 'local_db.json')
    
    def __init__(self):
        self.data = {}
        self._load_data()
        self._seed_data()
    
    def _load_data(self):
        """Load data from local JSON file."""
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.dirname(self.DATA_FILE)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Load existing data if file exists
            if os.path.exists(self.DATA_FILE):
                with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Loaded persistent data from {self.DATA_FILE}")
            else:
                self.data = {}
                logger.info("No existing data file, starting fresh")
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            self.data = {}
    
    def _save_data(self):
        """Save data to local JSON file."""
        try:
            # Create data directory if it doesn't exist
            data_dir = os.path.dirname(self.DATA_FILE)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Data saved to {self.DATA_FILE}")
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
    
    def _seed_data(self):
        """Populate with initial demo data only if users collection doesn't exist."""
        # Only seed if users collection is empty or doesn't exist
        if 'users' not in self.data or not self.data['users']:
            self.data['users'] = {
                'admin123': {
                    'id': 'admin123',
                    'email': 'admin@ppms.com',
                    'name': 'Admin User',
                    'role': 'admin',
                    'status': 'active',
                    'department': 'Management',
                    'created_at': '2024-01-01T00:00:00'
                },
                'operator123': {
                    'id': 'operator123',
                    'email': 'operator@ppms.com',
                    'name': 'Operator User',
                    'role': 'operator',
                    'status': 'active',
                    'department': 'Operations',
                    'created_at': '2024-01-01T00:00:00'
                },
                'manager123': {
                    'id': 'manager123',
                    'email': 'manager@ppms.com',
                    'name': 'Manager User',
                    'role': 'manager',
                    'status': 'active',
                    'department': 'Management',
                    'created_at': '2024-01-01T00:00:00'
                }
            }
            self._save_data()
    
    def collection(self, name):
        return MockCollection(self.data, name, self._save_data)


class MockCollection:
    """Mock Firestore collection with persistent storage."""
    
    def __init__(self, data, name, save_callback=None):
        self.data = data
        self.name = name
        self.save_callback = save_callback
        if name not in data:
            data[name] = {}
    
    def document(self, doc_id=None):
        # If no doc_id provided, generate one
        if doc_id is None:
            import uuid
            doc_id = str(uuid.uuid4())
        return MockDocument(self.data[self.name], doc_id, self.save_callback)
    
    def where(self, field, op, value):
        return MockQuery(self.data[self.name], field, op, value)
    
    def stream(self):
        return [MockDocSnapshot(doc_id, self.data[self.name][doc_id]) 
                for doc_id in self.data[self.name]]


class MockDocument:
    """Mock Firestore document with persistent storage."""
    
    def __init__(self, collection_data, doc_id, save_callback=None):
        self.collection_data = collection_data
        self.doc_id = doc_id
        self.save_callback = save_callback
    
    @property
    def id(self):
        """Return document ID."""
        return self.doc_id
    
    def set(self, data):
        self.collection_data[self.doc_id] = data
        if self.save_callback:
            self.save_callback()
    
    def get(self):
        if self.doc_id in self.collection_data:
            return MockDocSnapshot(self.doc_id, self.collection_data[self.doc_id])
        return MockDocSnapshot(self.doc_id, None)
    
    def update(self, data):
        if self.doc_id in self.collection_data:
            self.collection_data[self.doc_id].update(data)
            if self.save_callback:
                self.save_callback()
    
    def delete(self):
        if self.doc_id in self.collection_data:
            del self.collection_data[self.doc_id]
            if self.save_callback:
                self.save_callback()


class MockDocSnapshot:
    """Mock Firestore document snapshot."""
    
    def __init__(self, doc_id, data):
        self.doc_id = doc_id
        self._data = data
        self.exists = data is not None and len(data) > 0
    
    def to_dict(self):
        return self._data or {}


class MockQuery:
    """Mock Firestore query."""
    
    def __init__(self, collection_data, field, op, value):
        self.collection_data = collection_data
        self.field = field
        self.op = op
        self.value = value
        self.filters = [(field, op, value)]
    
    def where(self, field, op, value):
        self.filters.append((field, op, value))
        return self
    
    def stream(self):
        results = []
        for doc_id, doc in self.collection_data.items():
            match = True
            for f, o, v in self.filters:
                if f not in doc:
                    match = False
                    break
                if o == '==' and doc[f] != v:
                    match = False
                    break
            if match:
                results.append(MockDocSnapshot(doc_id, doc))
        return results


class MockAuth:
    """Mock Firebase Auth."""
    
    class UserNotFoundError(Exception):
        pass
    
    def __init__(self):
        self.users = {
            'admin@ppms.com': {
                'uid': 'admin123',
                'email': 'admin@ppms.com',
                'name': 'Admin User',
                'role': 'admin'
            },
            'admin': {
                'uid': 'admin123',
                'email': 'admin@ppms.com',
                'name': 'Admin User',
                'role': 'admin'
            },
            'operator@ppms.com': {
                'uid': 'operator123',
                'email': 'operator@ppms.com',
                'name': 'Operator User',
                'role': 'operator'
            },
            'operator': {
                'uid': 'operator123',
                'email': 'operator@ppms.com',
                'name': 'Operator User',
                'role': 'operator'
            },
            'manager@ppms.com': {
                'uid': 'manager123',
                'email': 'manager@ppms.com',
                'name': 'Manager User',
                'role': 'manager'
            },
            'manager': {
                'uid': 'manager123',
                'email': 'manager@ppms.com',
                'name': 'Manager User',
                'role': 'manager'
            }
        }
    
    def get_user_by_email(self, email):
        email_lower = email.lower().strip()
        if email_lower not in self.users:
            raise MockAuth.UserNotFoundError(f"User not found: {email}")
        user_data = self.users[email_lower]
        return type('UserRecord', (), user_data)()
    
    def create_user(self, **kwargs):
        pass


class MockRealtimeDB:
    """Mock Firebase Realtime Database with persistent storage."""
    
    # Path to store persistent data
    DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'realtime_db.json')
    
    def __init__(self):
        self.data = {}
        self._load_data()
    
    def _load_data(self):
        """Load data from local JSON file."""
        try:
            data_dir = os.path.dirname(self.DATA_FILE)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            if os.path.exists(self.DATA_FILE):
                with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading realtime db data: {str(e)}")
            self.data = {}
    
    def _save_data(self):
        """Save data to local JSON file."""
        try:
            data_dir = os.path.dirname(self.DATA_FILE)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving realtime db data: {str(e)}")
    
    def child(self, path):
        return MockRealtimeDBReference(self.data, path, self._save_data)
    
    def get(self):
        return type('DataSnapshot', (), {'val': lambda: self.data})()
    
    def set(self, value):
        self.data = value
        self._save_data()
    
    def update(self, updates):
        self.data.update(updates)
        self._save_data()


class MockRealtimeDBReference:
    """Mock Realtime Database reference/path with persistent storage."""
    
    def __init__(self, data, path, save_callback=None):
        self.data = data
        self.path = path
        self.save_callback = save_callback
    
    def child(self, path):
        return MockRealtimeDBReference(self.data, f"{self.path}/{path}", self.save_callback)
    
    def get(self):
        return type('DataSnapshot', (), {'val': lambda: None})()
    
    def set(self, value):
        self.data[self.path] = value
        if self.save_callback:
            self.save_callback()
    
    def update(self, updates):
        if self.path not in self.data:
            self.data[self.path] = {}
        self.data[self.path].update(updates)
        if self.save_callback:
            self.save_callback()


class FirebaseConfig:
    """Firebase configuration and initialization."""

    _db_instance = None
    _firestore_instance = None
    _is_initialized = False

    @classmethod
    def initialize(cls):
        """Initialize Firebase connection with credentials."""
        if cls._is_initialized:
            return

        try:
            # Check if in test/demo mode
            if os.getenv('OFFLINE_MODE', 'false').lower() == 'true':
                logger.info("Running in OFFLINE_MODE - Firebase not initialized")
                cls._is_initialized = True
                return

            # Get credentials path from environment
            creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'serviceAccountKey.json')

            # Check if credentials file exists
            if not os.path.exists(creds_path):
                logger.warning(f"Firebase credentials file not found at: {creds_path}")
                logger.warning("Running in demo mode with mock data")
                # Set offline mode for demo purposes
                os.environ['OFFLINE_MODE'] = 'true'
                cls._is_initialized = True
                return

            # Initialize Firebase with credentials
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
                'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
            })

            cls._is_initialized = True
            logger.info("Firebase initialized successfully")

        except Exception as e:
            logger.warning(f"Firebase initialization failed: {str(e)}")
            logger.warning("Running in demo mode with mock data")
            os.environ['OFFLINE_MODE'] = 'true'
            cls._is_initialized = True

    @classmethod
    def get_firestore(cls):
        """Get Firestore database instance."""
        if not cls._is_initialized:
            cls.initialize()

        if cls._firestore_instance is None:
            # Check if offline mode
            if os.getenv('OFFLINE_MODE', 'false').lower() == 'true':
                cls._firestore_instance = MockFirestore()
                logger.info("Using Mock Firestore for offline mode")
            else:
                cls._firestore_instance = firestore.client()

        return cls._firestore_instance

    @classmethod
    def get_realtime_db(cls):
        """Get Realtime Database instance."""
        if not cls._is_initialized:
            cls.initialize()

        if cls._db_instance is None:
            # Check if offline mode
            if os.getenv('OFFLINE_MODE', 'false').lower() == 'true':
                cls._db_instance = MockRealtimeDB()
                logger.info("Using Mock Realtime DB for offline mode")
            else:
                cls._db_instance = db.reference()

        return cls._db_instance

    @classmethod
    def get_auth(cls):
        """Get Firebase Auth instance."""
        if os.getenv('OFFLINE_MODE', 'false').lower() == 'true':
            return MockAuth()
        return auth


class AppConfig:
    """Application-level configuration."""

    APP_NAME = os.getenv('APP_NAME', 'Petrol Pump Management System')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', 'Rs.')
    CURRENCY_CODE = os.getenv('CURRENCY_CODE', 'PKR')

    # Database settings
    DB_ENCRYPTION_ENABLED = os.getenv('DB_ENCRYPTION_ENABLED', 'true').lower() == 'true'
    OFFLINE_MODE = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'

    # Paths
    REPORT_OUTPUT_PATH = os.getenv('REPORT_OUTPUT_PATH', './reports')
    REPORT_LOGO_PATH = os.getenv('REPORT_LOGO_PATH', './assets/logo.png')

    # Audit settings
    ENABLE_AUDIT_LOG = os.getenv('ENABLE_AUDIT_LOG', 'true').lower() == 'true'
    AUDIT_LOG_RETENTION_DAYS = int(os.getenv('AUDIT_LOG_RETENTION_DAYS', 180))

    # UI Settings
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

    # Role definitions
    ROLES = {
        'admin': {
            'display_name': 'Administrator',
            'permissions': ['all'],
            'description': 'Full system control'
        },
        'manager': {
            'display_name': 'Manager',
            'permissions': [
                'view_dashboard', 'manage_fuel', 'manage_nozzles',
                'view_sales', 'manage_customers', 'manage_expenses',
                'view_reports', 'manage_shifts'
            ],
            'description': 'Daily operations and reports'
        },
        'operator': {
            'display_name': 'Operator',
            'permissions': ['record_sales', 'submit_readings', 'view_shift_data'],
            'description': 'Fuel sales entry only'
        },
        'accountant': {
            'display_name': 'Accountant',
            'permissions': [
                'view_ledger', 'view_expenses', 'view_reports',
                'generate_reports', 'view_customers'
            ],
            'description': 'Ledger, expenses, and profit reports'
        }
    }

    # Fuel types
    FUEL_TYPES = ['Petrol', 'Diesel', 'CNG']

    # Expense categories
    EXPENSE_CATEGORIES = [
        'Electricity',
        'Salaries',
        'Maintenance',
        'Miscellaneous',
        'Water',
        'Rent'
    ]

    # Payment methods
    PAYMENT_METHODS = [
        'Cash',
        'Credit',
        'EasyPaisa',
        'JazzCash',
        'Bank Transfer'
    ]

    # Shift status
    SHIFT_STATUS = ['Open', 'Closed']

    # Nozzle status
    NOZZLE_STATUS = ['Active', 'Inactive', 'Locked', 'Maintenance']

    # Create report output path if it doesn't exist
    os.makedirs(REPORT_OUTPUT_PATH, exist_ok=True)


class DatabaseConfig:
    """Database-related constants."""

    # Collection names
    COLLECTIONS = {
        'users': 'users',
        'fuel_types': 'fuel_types',
        'tanks': 'tanks',
        'nozzles': 'nozzles',
        'readings': 'readings',
        'sales': 'sales',
        'purchases': 'purchases',
        'customers': 'customers',
        'expenses': 'expenses',
        'shifts': 'shifts',
        'reports': 'reports',
        'audit_logs': 'audit_logs',
        'payments': 'payments'
    }

    # Batch operation limits
    BATCH_SIZE = 500  # Firestore batch write limit

    # Transaction retry settings
    MAX_RETRIES = 3
    RETRY_DELAY_MS = 100
