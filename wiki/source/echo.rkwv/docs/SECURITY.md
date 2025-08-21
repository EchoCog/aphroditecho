# Deep Tree Echo Security Framework

## Overview

The Deep Tree Echo Security Framework provides comprehensive production-ready security for the cognitive architecture platform. It implements enterprise-grade authentication, authorization, encryption, and monitoring capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Security Framework                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │Authentication│  │Authorization │  │   Encryption    │    │
│  │   System     │  │   System     │  │    Manager      │    │
│  │              │  │              │  │                 │    │
│  │• JWT Tokens  │  │• RBAC        │  │• AES/RSA        │    │
│  │• MFA Support │  │• Permissions │  │• Key Rotation   │    │
│  │• Password    │  │• Resources   │  │• Data Masking   │    │
│  │  Security    │  │• Ownership   │  │• API Keys       │    │
│  └─────────────┘  └──────────────┘  └─────────────────┘    │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐                         │
│  │ Security    │  │ Security     │                         │
│  │ Monitor     │  │ Middleware   │                         │
│  │             │  │              │                         │
│  │• Event Log  │  │• Request     │                         │
│  │• Intrusion  │  │  Security    │                         │
│  │  Detection  │  │• Rate Limit  │                         │
│  │• Alerting   │  │• Headers     │                         │
│  └─────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Authentication System (`security/auth.py`)

Handles user authentication, JWT tokens, and multi-factor authentication.

**Features:**
- JWT-based authentication with configurable expiry
- Multi-factor authentication using TOTP (Time-based One-Time Password)
- Secure password hashing with PBKDF2 and salt
- Account lockout protection against brute force attacks
- User registration and profile management
- Password strength validation
- Token management and revocation

**Key Classes:**
- `User`: User data model with profile and security settings
- `AuthToken`: JWT token representation
- `AuthenticationSystem`: Main authentication management

### 2. Authorization System (`security/authorization.py`)

Implements role-based access control and fine-grained permissions.

**Features:**
- Role-based access control (RBAC) with hierarchical roles
- Fine-grained permission system
- Resource-level access controls
- Resource ownership tracking
- Dynamic permission checking
- Custom role and permission management

**Default Roles:**
- `guest`: Minimal access (status only)
- `user`: Standard user access (sessions, memory, cognitive processing)
- `premium_user`: Enhanced features (metrics, advanced memory)
- `moderator`: Content management capabilities
- `admin`: Full system access

**Key Classes:**
- `Role`: Role definition with permissions
- `Permission`: Permission definition with resource types and actions
- `AuthorizationSystem`: Main authorization management

### 3. Encryption Manager (`security/encryption.py`)

Provides data encryption, key management, and cryptographic utilities.

**Features:**
- Multi-context encryption with separate keys
- Automatic key rotation
- AES encryption for symmetric data encryption
- RSA encryption for asymmetric encryption
- API key generation and validation
- Data hashing and verification
- Data anonymization utilities
- Secure backup and restore

**Encryption Contexts:**
- `user_data`: User profiles and authentication data
- `session_data`: Session information
- `memory_data`: Cognitive memory storage
- `system_data`: System configuration and logs
- `temp_data`: Temporary data encryption

### 4. Security Monitor (`security/monitoring.py`)

Monitors security events, detects intrusions, and manages alerts.

**Features:**
- Real-time security event logging
- Intrusion detection with pattern analysis
- Brute force attack detection
- Rate limiting violation detection
- Automated threat response
- IP blocking and management
- Comprehensive audit reporting
- Alert management and escalation

**Event Types:**
- Login success/failure
- Permission denied
- Suspicious activity
- API access
- Data access
- Admin actions
- Security violations

### 5. Security Middleware (`security/middleware.py`)

Integrates security into Flask applications with comprehensive request processing.

**Features:**
- Request authentication and authorization
- Rate limiting with role-based quotas
- Security headers injection
- Input sanitization and validation
- Session management with secure cookies
- HTTPS enforcement
- CORS security controls

## Configuration

### Environment Variables

```bash
# Authentication
SECURITY_SECRET_KEY=your_secret_key_here
TOKEN_EXPIRY_HOURS=24
REFRESH_TOKEN_EXPIRY_DAYS=30

# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true

# Account Lockout
MAX_FAILED_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_GUEST_PER_MINUTE=20
RATE_LIMIT_USER_PER_MINUTE=60
RATE_LIMIT_PREMIUM_PER_MINUTE=120
RATE_LIMIT_ADMIN_PER_MINUTE=200

# Security Monitoring
SECURITY_MONITORING_ENABLED=true
ALERT_RETENTION_DAYS=90
AUTO_BLOCK_ENABLED=true

# Encryption
ENCRYPTION_ENABLED=true
KEY_ROTATION_INTERVAL_DAYS=30

# HTTPS and Security
ENFORCE_HTTPS=true
CORS_ORIGINS=https://yourdomain.com

# Default Admin (Change immediately!)
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@yourdomain.com
DEFAULT_ADMIN_PASSWORD=ChangeMe123!
```

## API Endpoints

### Authentication Endpoints

```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "string",
    "email": "string", 
    "password": "string"
}
```

```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "string",
    "password": "string",
    "mfa_token": "string" // Optional for MFA
}
```

```http
POST /api/auth/logout
Authorization: Bearer <token>
```

### Secured Endpoints

All cognitive processing endpoints now require authentication:

```http
POST /api/session
Authorization: Bearer <token>
```

```http
GET /api/session/{session_id}
Authorization: Bearer <token>
```

```http
POST /api/process
Authorization: Bearer <token>
Content-Type: application/json

{
    "session_id": "string",
    "input": "string"
}
```

### Admin Endpoints

```http
GET /api/security/summary
Authorization: Bearer <admin_token>
```

```http
GET /api/security/alerts
Authorization: Bearer <admin_token>
```

## Usage Examples

### Basic Authentication Flow

```python
# Register a new user
response = requests.post('/api/auth/register', json={
    'username': 'newuser',
    'email': 'user@example.com',
    'password': 'SecurePass123!'
})

# Login and get token
response = requests.post('/api/auth/login', json={
    'username': 'newuser',
    'password': 'SecurePass123!'
})
token = response.json()['token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('/api/session', headers=headers)
```

### Role-Based Access

```python
# Check user permissions
user_id = "user123"
has_permission = authz_system.has_permission(user_id, "session.create")

# Check resource access
can_access = authz_system.can_access_resource(
    user_id, ResourceType.SESSION, Action.READ, session_id
)

# Assign custom role
authz_system.assign_role_to_user(user_id, "premium_user")
```

### Encryption Usage

```python
# Encrypt sensitive data
encrypted = encryption_manager.encrypt_data(
    "sensitive information", 
    context="user_data"
)

# Decrypt data
decrypted = encryption_manager.decrypt_data(
    encrypted, 
    context="user_data"
)

# Generate API key
key_id, key_secret = encryption_manager.create_api_key(
    user_id, 
    scopes=["api.cognitive_process"]
)
```

### Security Monitoring

```python
# Log security event
event_id = security_monitor.log_security_event(
    SecurityEventType.LOGIN_SUCCESS,
    user_id="user123",
    ip_address="192.168.1.100",
    details={"method": "password"}
)

# Get security summary
summary = security_monitor.get_security_summary(hours=24)

# Get active alerts
alerts = security_monitor.get_active_alerts(AlertLevel.HIGH)
```

## Security Best Practices

### Production Deployment

1. **Change Default Credentials**
   ```bash
   # Change the default admin password immediately
   DEFAULT_ADMIN_PASSWORD=YourSecurePasswordHere
   ```

2. **Use Strong Secret Keys**
   ```bash
   # Generate a strong secret key
   SECURITY_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```

3. **Enable HTTPS**
   ```bash
   ENFORCE_HTTPS=true
   SESSION_COOKIE_SECURE=true
   ```

4. **Configure CORS Properly**
   ```bash
   # Don't use * in production
   CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
   ```

5. **Set Up Monitoring**
   ```bash
   SECURITY_MONITORING_ENABLED=true
   AUTO_BLOCK_ENABLED=true
   ```

### Security Headers

The framework automatically adds security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
Referrer-Policy: strict-origin-when-cross-origin
```

### Rate Limiting

Default rate limits by role:

| Role | Per Minute | Per Hour | Per Day |
|------|------------|----------|---------|
| Guest | 20 | 200 | 1,000 |
| User | 60 | 1,000 | 10,000 |
| Premium | 120 | 2,000 | 20,000 |
| Admin | 200 | 5,000 | 50,000 |

## Testing

Run the comprehensive security test suite:

```bash
cd src
python test_security_framework.py
```

Test individual components:

```python
# Test authentication
from security import AuthenticationSystem
auth = AuthenticationSystem("test_key")
success, message, user = auth.register_user("test", "test@example.com", "Pass123!")

# Test authorization
from security import AuthorizationSystem
authz = AuthorizationSystem()
authz.assign_role_to_user(user.user_id, "user")

# Test encryption
from security import EncryptionManager
encryption = EncryptionManager()
encrypted = encryption.encrypt_data("secret data")
```

## Migration from Legacy System

To migrate from the non-secure version:

1. **Install Dependencies**
   ```bash
   pip install PyJWT cryptography pyotp qrcode bcrypt
   ```

2. **Update Application**
   ```python
   # Replace app.py with secure_app.py
   # Or integrate security middleware into existing app
   from security import SecurityMiddleware
   security_middleware = SecurityMiddleware(auth, authz, monitor, encryption)
   security_middleware.init_app(app)
   ```

3. **Configure Environment**
   ```bash
   # Set up environment variables
   export SECURITY_SECRET_KEY="your_secret_key"
   export DEFAULT_ADMIN_PASSWORD="secure_admin_password"
   ```

4. **Run Migration**
   ```bash
   # Start secure application
   python secure_app.py
   ```

## Troubleshooting

### Common Issues

1. **"Security system not initialized"**
   - Ensure security framework is properly initialized before use
   - Check that all environment variables are set

2. **"Authentication required"**
   - Include valid JWT token in Authorization header
   - Verify token hasn't expired

3. **"Permission denied"**
   - Check user has required permissions/roles
   - Verify resource ownership for resource-specific operations

4. **Rate limit exceeded**
   - Reduce request frequency
   - Check if IP is blocked
   - Verify user role has appropriate limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('security').setLevel(logging.DEBUG)
```

## Support and Maintenance

### Regular Maintenance

1. **Monitor Security Alerts**
   ```bash
   # Check active alerts regularly
   curl -H "Authorization: Bearer $ADMIN_TOKEN" \
        http://localhost:8000/api/security/alerts
   ```

2. **Rotate Keys**
   ```python
   # Key rotation is automatic, but can be triggered manually
   encryption_manager.rotate_context_key("user_data")
   ```

3. **Review Audit Logs**
   ```python
   # Generate audit reports
   report = security_monitor.generate_audit_report(days=30)
   ```

4. **Update Dependencies**
   ```bash
   pip install --upgrade PyJWT cryptography pyotp qrcode bcrypt
   ```

## License

This security framework is part of the Deep Tree Echo project and is licensed under the MIT License.