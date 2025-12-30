"""
Authentication Service
Handles user authentication and session management with Firebase.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.config.firebase_config import FirebaseConfig, AppConfig
from src.config.logger_config import setup_logger
from src.models import User, UserRole

logger = setup_logger(__name__)


class AuthenticationService:
    """Manages user authentication and session handling."""

    def __init__(self):
        """Initialize authentication service."""
        self.firestore = FirebaseConfig.get_firestore()
        self.auth = FirebaseConfig.get_auth()
        self.current_user: Optional[User] = None
        self.session_token: Optional[str] = None

    def login_with_email_password(
        self, email: str, password: str
    ) -> tuple[bool, str, Optional[User]]:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (success, message, user_object)
        """
        try:
            # Verify with Firebase
            user_record = self.auth.get_user_by_email(email)

            # Fetch user document from Firestore
            user_doc = self.firestore.collection('users').document(user_record.uid).get()

            if not user_doc.exists:
                return False, "User profile not found in database", None

            user_data = user_doc.to_dict()

            # Check if user is active
            if user_data.get('status') != 'active':
                return False, "User account is inactive", None

            # Create user object
            user = User(
                uid=user_record.uid,
                email=user_record.email,
                name=user_data.get('name', ''),
                role=UserRole(user_data.get('role', 'operator')),
                status=user_data.get('status', 'active'),
                department=user_data.get('department', '')
            )

            self.current_user = user
            self.session_token = self._generate_session_token()

            logger.info(f"User logged in successfully: {email}")
            return True, "Login successful", user

        except Exception as e:
            # Handle both Firebase and Mock auth errors
            error_msg = str(e).lower()
            if 'not found' in error_msg or 'user' in error_msg:
                logger.warning(f"Login attempt with non-existent email: {email}")
                return False, "Invalid email or password", None
            logger.error(f"Authentication error: {str(e)}")
            return False, f"Authentication failed: {str(e)}", None

    def logout(self) -> bool:
        """
        Logout current user.

        Returns:
            True if logout successful
        """
        try:
            if self.current_user:
                logger.info(f"User logged out: {self.current_user.email}")
            self.current_user = None
            self.session_token = None
            return True
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False

    def create_user(
        self,
        email: str,
        password: str,
        name: str,
        role: str,
        department: str = ""
    ) -> tuple[bool, str, Optional[str]]:
        """
        Create new user account.

        Args:
            email: User email
            password: User password (min 6 characters)
            name: User full name
            role: User role (admin, manager, operator, accountant)
            department: User department

        Returns:
            Tuple of (success, message, user_uid)
        """
        try:
            # Validate role
            if role not in AppConfig.ROLES:
                return False, f"Invalid role: {role}", None

            # Create Firebase auth user
            user_record = self.auth.create_user(
                email=email,
                password=password,
                display_name=name
            )

            # Create user document in Firestore
            user_data = {
                'email': email,
                'name': name,
                'role': role,
                'status': 'active',
                'department': department,
                'created_at': datetime.now().isoformat(),
                'created_by': self.current_user.uid if self.current_user else 'system'
            }

            self.firestore.collection('users').document(user_record.uid).set(user_data)

            logger.info(f"New user created: {email} with role {role}")
            return True, "User created successfully", user_record.uid

        except self.auth.EmailAlreadyExistsError:
            logger.warning(f"User creation failed - email already exists: {email}")
            return False, "Email already registered", None
        except self.auth.WeakPasswordError:
            return False, "Password must be at least 6 characters", None
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            return False, f"Error creating user: {str(e)}", None

    def update_user_role(self, user_id: str, new_role: str) -> tuple[bool, str]:
        """
        Update user role.

        Args:
            user_id: User UID
            new_role: New role

        Returns:
            Tuple of (success, message)
        """
        try:
            if new_role not in AppConfig.ROLES:
                return False, f"Invalid role: {new_role}"

            self.firestore.collection('users').document(user_id).update({
                'role': new_role,
                'updated_at': datetime.now().isoformat()
            })

            logger.info(f"User role updated: {user_id} -> {new_role}")
            return True, "Role updated successfully"

        except Exception as e:
            logger.error(f"Error updating user role: {str(e)}")
            return False, f"Error: {str(e)}"

    def disable_user(self, user_id: str) -> tuple[bool, str]:
        """
        Disable user account.

        Args:
            user_id: User UID

        Returns:
            Tuple of (success, message)
        """
        try:
            self.firestore.collection('users').document(user_id).update({
                'status': 'inactive',
                'updated_at': datetime.now().isoformat()
            })

            self.auth.update_user(user_id, disabled=True)

            logger.info(f"User disabled: {user_id}")
            return True, "User disabled successfully"

        except Exception as e:
            logger.error(f"Error disabling user: {str(e)}")
            return False, f"Error: {str(e)}"

    def change_password(self, user_id: str, new_password: str) -> tuple[bool, str]:
        """
        Change user password.

        Args:
            user_id: User UID
            new_password: New password

        Returns:
            Tuple of (success, message)
        """
        try:
            self.auth.update_user(user_id, password=new_password)
            logger.info(f"Password changed for user: {user_id}")
            return True, "Password changed successfully"

        except self.auth.WeakPasswordError:
            return False, "Password must be at least 6 characters"
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return False, f"Error: {str(e)}"

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by UID.

        Args:
            user_id: User UID

        Returns:
            User object or None
        """
        try:
            user_doc = self.firestore.collection('users').document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                return User(
                    uid=user_id,
                    email=user_data.get('email', ''),
                    name=user_data.get('name', ''),
                    role=UserRole(user_data.get('role', 'operator')),
                    status=user_data.get('status', 'active'),
                    department=user_data.get('department', '')
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching user: {str(e)}")
            return None

    def list_all_users(self) -> list[User]:
        """
        Get all users.

        Returns:
            List of User objects
        """
        try:
            users = []
            docs = self.firestore.collection('users').stream()
            for doc in docs:
                user_data = doc.to_dict()
                user = User(
                    uid=doc.id,
                    email=user_data.get('email', ''),
                    name=user_data.get('name', ''),
                    role=UserRole(user_data.get('role', 'operator')),
                    status=user_data.get('status', 'active'),
                    department=user_data.get('department', '')
                )
                users.append(user)
            return users
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return []

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self.current_user is not None

    def has_permission(self, permission: str) -> bool:
        """
        Check if current user has specific permission.

        Args:
            permission: Permission name

        Returns:
            True if user has permission
        """
        if not self.current_user:
            return False

        role_config = AppConfig.ROLES.get(self.current_user.role.value, {})
        permissions = role_config.get('permissions', [])

        return 'all' in permissions or permission in permissions

    def _generate_session_token(self) -> str:
        """Generate session token."""
        from datetime import datetime
        return f"{self.current_user.uid}_{datetime.now().timestamp()}"
