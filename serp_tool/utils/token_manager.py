import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import hashlib
import secrets

from serp_tool.logging import app_logger
from serp_tool.utils.temp_manager import get_temp_dir


class TokenManager:

    def __init__(self):
        self.temp_dir = get_temp_dir()
        self.token_file = self.temp_dir / "api_tokens.json"
        self.backup_token_file = self.temp_dir / "backup_tokens.json"
        self.session_id = self._generate_session_id()
        self.quota_exceeded_tokens = set()

    def _generate_session_id(self) -> str:
        return hashlib.sha256(f"{datetime.now().isoformat()}{secrets.token_hex(16)}".encode()).hexdigest()[:16]

    def _load_tokens(self) -> Dict[str, Any]:
        if not self.token_file.exists():
            return {}

        try:
            with open(self.token_file, 'r') as f:
                data = json.load(f)

                if data.get('session_id') == self.session_id:
                    return data.get('tokens', {})
                else:
                    self._clear_tokens()
                    return {}
        except (json.JSONDecodeError, KeyError, OSError) as e:
            app_logger.warning(f"Failed to load tokens: {e}")
            return {}

    def _save_tokens(self, tokens: Dict[str, Any]) -> None:
        try:
            data = {
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'tokens': tokens
            }
            with open(self.token_file, 'w') as f:
                json.dump(data, f, indent=2)

            os.chmod(self.token_file, 0o600)
        except OSError as e:
            app_logger.error(f"Failed to save tokens: {e}")
            raise

    def _clear_tokens(self) -> None:
        try:
            if self.token_file.exists():
                self.token_file.unlink()
        except OSError as e:
            app_logger.warning(f"Failed to clear tokens: {e}")

    def has_token_in_env(self, token_type: str) -> bool:
        env_vars = {
            'google_api_key': 'GOOGLE_API_KEY',
            'google_cx': 'GOOGLE_CSE_CX'
        }

        env_var = env_vars.get(token_type)
        if not env_var:
            return False

        return bool(os.getenv(env_var))

    def get_token_from_env(self, token_type: str) -> Optional[str]:
        env_vars = {
            'google_api_key': 'GOOGLE_API_KEY',
            'google_cx': 'GOOGLE_CSE_CX'
        }

        env_var = env_vars.get(token_type)
        if not env_var:
            return None

        return os.getenv(env_var)

    def get_token(self, token_type: str) -> Optional[str]:
        if self.has_token_in_env(token_type):
            return self.get_token_from_env(token_type)

        tokens = self._load_tokens()
        return tokens.get(token_type)

    def set_token(self, token_type: str, token_value: str) -> Tuple[bool, str]:
        validation_result = self._validate_token_with_message(token_type, token_value)
        if not validation_result[0]:
            return False, validation_result[1]

        tokens = self._load_tokens()
        tokens[token_type] = token_value
        self._save_tokens(tokens)

        app_logger.info(f"Token stored temporarily: {token_type}", extra={
            "action": "token_store",
            "status": "success",
            "token_type": token_type
        })
        return True, f"{token_type} token stored successfully"

    def _validate_token_with_message(self, token_type: str, token_value: str) -> Tuple[bool, str]:
        if not token_value or not isinstance(token_value, str):
            return False, "Token value is required"

        token_value = token_value.strip()
        if not token_value:
            return False, "Token value cannot be empty"

        if token_type == 'google_api_key':
            if not token_value.startswith('AIza'):
                return False, "Google API key must start with 'AIza'"
            if len(token_value) < 30:
                return False, "Google API key must be at least 30 characters long"
            return True, "Google API key format is valid"
        elif token_type == 'google_cx':
            if len(token_value) < 10:
                return False, "Google CSE ID must be at least 10 characters long"
            cleaned = token_value.replace(':', '').replace('-', '').replace('_', '')
            if len(cleaned) < 5:
                return False, "Google CSE ID must contain at least 5 alphanumeric characters"
            if not any(c.isalnum() for c in cleaned):
                return False, "Google CSE ID must contain alphanumeric characters"
            return True, "Google CSE ID format is valid"

        return True, "Token format is valid"

    def _validate_token(self, token_type: str, token_value: str) -> bool:
        result, _ = self._validate_token_with_message(token_type, token_value)
        return result

    def validate_token_with_api(self, token_type: str, token_value: str) -> Tuple[bool, str]:
        format_result, format_message = self._validate_token_with_message(token_type, token_value)
        if not format_result:
            return False, format_message

        try:
            if token_type == 'google_api_key':
                return self._validate_google_api_key(token_value)
            else:
                return True, format_message
        except Exception as e:
            app_logger.error(f"Token validation error: {e}")
            return False, f"Validation error: {str(e)}"

    def _validate_google_api_key(self, api_key: str) -> Tuple[bool, str]:
        try:
            import requests

            test_url = "https://www.googleapis.com/customsearch/v1"
            test_params = {
                'key': api_key,
                'cx': 'test',
                'q': 'test'
            }

            response = requests.get(test_url, params=test_params, timeout=10)

            if response.status_code == 400:
                return True, "Google API key is valid"
            elif response.status_code == 403:
                return False, "Google API key is invalid or quota exceeded"
            else:
                return True, "Google API key appears valid"

        except ImportError:
            return True, "Google API key format valid (requests not available for validation)"
        except Exception as e:
            return False, f"Google API validation failed: {str(e)}"

    def clear_all_tokens(self) -> None:
        self._clear_tokens()
        app_logger.info("All temporary tokens cleared", extra={"action": "token_clear", "status": "success"})

    def get_token_status(self) -> Dict[str, Any]:
        status = {}

        for token_type in ['google_api_key', 'google_cx']:
            env_token = self.get_token_from_env(token_type)
            temp_token = self._load_tokens().get(token_type)

            status[token_type] = {
                'has_env': bool(env_token),
                'has_temp': bool(temp_token),
                'source': 'env' if env_token else ('temp' if temp_token else None)
            }

        return status

    def _load_backup_tokens(self) -> Dict[str, Any]:
        if not self.backup_token_file.exists():
            return {}

        try:
            with open(self.backup_token_file, 'r') as f:
                data = json.load(f)

                if data.get('session_id') == self.session_id:
                    return data.get('tokens', {})
                else:
                    self._clear_backup_tokens()
                    return {}
        except (json.JSONDecodeError, KeyError, OSError) as e:
            app_logger.warning(f"Failed to load backup tokens: {e}")
            return {}

    def _save_backup_tokens(self, tokens: Dict[str, Any]) -> None:
        try:
            data = {
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'tokens': tokens
            }
            with open(self.backup_token_file, 'w') as f:
                json.dump(data, f, indent=2)

            os.chmod(self.backup_token_file, 0o600)
        except OSError as e:
            app_logger.error(f"Failed to save backup tokens: {e}")
            raise

    def _clear_backup_tokens(self) -> None:
        try:
            if self.backup_token_file.exists():
                self.backup_token_file.unlink()
        except OSError as e:
            app_logger.warning(f"Failed to clear backup tokens: {e}")

    def set_backup_token(self, token_type: str, token_value: str) -> Tuple[bool, str]:
        validation_result = self._validate_token_with_message(token_type, token_value)
        if not validation_result[0]:
            return False, validation_result[1]

        backup_tokens = self._load_backup_tokens()
        backup_tokens[token_type] = token_value
        self._save_backup_tokens(backup_tokens)

        app_logger.info(f"Backup token stored: {token_type}", extra={
            "action": "backup_token_store",
            "status": "success",
            "token_type": token_type
        })
        return True, f"Backup {token_type} token stored successfully"

    def get_backup_token(self, token_type: str) -> Optional[str]:
        backup_tokens = self._load_backup_tokens()
        return backup_tokens.get(token_type)

    def has_backup_token(self, token_type: str) -> bool:
        return self.get_backup_token(token_type) is not None

    def mark_token_quota_exceeded(self, token_type: str, token_value: str) -> None:
        token_hash = hashlib.sha256(f"{token_type}:{token_value}".encode()).hexdigest()
        self.quota_exceeded_tokens.add(token_hash)
        app_logger.warning(f"Token marked as quota exceeded: {token_type}", extra={
            "action": "quota_mark",
            "status": "warning",
            "token_type": token_type
        })

    def is_token_quota_exceeded(self, token_type: str, token_value: str) -> bool:
        token_hash = hashlib.sha256(f"{token_type}:{token_value}".encode()).hexdigest()
        return token_hash in self.quota_exceeded_tokens

    def get_available_token(self, token_type: str) -> Optional[str]:
        primary_token = self.get_token(token_type)
        if primary_token and not self.is_token_quota_exceeded(token_type, primary_token):
            return primary_token

        backup_token = self.get_backup_token(token_type)
        if backup_token and not self.is_token_quota_exceeded(token_type, backup_token):
            app_logger.info(f"Using backup token for {token_type}", extra={
                "action": "backup_token_use",
                "status": "success",
                "token_type": token_type
            })
            return backup_token

        return None

    def switch_to_backup_token(self, token_type: str) -> Tuple[bool, str]:
        backup_token = self.get_backup_token(token_type)
        if not backup_token:
            return False, f"No backup {token_type} token available"

        current_token = self.get_token(token_type)
        if current_token:
            self.mark_token_quota_exceeded(token_type, current_token)

        success, message = self.set_token(token_type, backup_token)
        if success:
            app_logger.info(f"Switched to backup token for {token_type}", extra={
                "action": "backup_token_switch",
                "status": "success",
                "token_type": token_type
            })
            return True, f"Switched to backup {token_type} token"
        else:
            return False, f"Failed to switch to backup {token_type} token: {message}"

    def clear_backup_tokens(self) -> None:
        self._clear_backup_tokens()
        app_logger.info("All backup tokens cleared", extra={"action": "backup_token_clear", "status": "success"})

    def get_backup_token_status(self) -> Dict[str, Any]:
        status = {}
        backup_tokens = self._load_backup_tokens()

        for token_type in ['google_api_key', 'google_cx']:
            backup_token = backup_tokens.get(token_type)
            status[token_type] = {
                'has_backup': bool(backup_token),
                'quota_exceeded': self.is_token_quota_exceeded(token_type, backup_token) if backup_token else False
            }

        return status


token_manager = TokenManager()
