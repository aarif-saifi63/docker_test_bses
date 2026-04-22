# BSES Rajdhani Power Limited
# Chatbot Application — Security Implementation Document

**Version:** 1.0
**Prepared for:** BSES Rajdhani Power Limited
**Document Type:** Security Implementation & VAPT Closure Report
**Application:** BSES E-Mitra Chatbot & Admin Panel

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope of Security Assessment](#2-scope-of-security-assessment)
3. [Vulnerability Summary](#3-vulnerability-summary)
4. [Critical Severity — Findings & Implementations](#4-critical-severity--findings--implementations)
5. [Medium Severity — Findings & Implementations](#5-medium-severity--findings--implementations)
6. [Low Severity — Findings & Implementations](#6-low-severity--findings--implementations)
7. [External VAPT Closure](#7-external-vapt-closure)
8. [Security Implementation Overview](#8-security-implementation-overview)

---

## 1. Executive Summary

This document presents a comprehensive account of all security vulnerabilities identified during the internal and external Vulnerability Assessment and Penetration Testing (VAPT) conducted on the **BSES Rajdhani Power Limited E-Mitra Chatbot** and its **Admin Panel**. It details the nature of each vulnerability, the risk it posed, and the specific security measures implemented to remediate it.

All identified vulnerabilities — **Critical**, **Medium**, and **Low** severity — have been fully addressed and closed. The application has been hardened against common attack vectors including unauthorized access, privilege escalation, injection attacks, file upload exploits, session hijacking, brute force, and information disclosure.

**Status: All VAPT findings — CLOSED**

---

## 2. Scope of Security Assessment

The security assessment covered the following components:

| Component | Description |
|---|---|
| Chatbot Frontend (Bot UI) | User-facing chatbot interface served to BSES consumers |
| Admin Panel (Admin UI) | Internal web panel for BSES staff to manage chatbot content |
| Backend API (Flask) | REST API endpoints serving both the chatbot and admin panel |
| Authentication System | Login, OTP verification, session management |
| File Upload Functionality | All endpoints accepting file uploads |
| User & Role Management | User creation, role assignment, permission enforcement |
| Database Layer | SQL query handling, input sanitization |

---

## 3. Vulnerability Summary

| Severity | Internal VAPT | External VAPT (Additional) | Total Fixed | Status |
|---|---|---|---|---|
| Critical | 7 | 0 | 7 | All Closed |
| Medium | 6 | 2 (Email Validation, Clickjacking) | 8 | All Closed |
| Low | 3 | 7 (Weak Password, Security Headers, Server Banner, Right Click, Copy-Paste, Concurrent Login, CSP) | 10 | All Closed |
| **Total** | **16** | **9** | **25** | **All Closed** |

---

## 4. Critical Severity — Findings & Implementations

---

### 4.1 CWE-284 — API Endpoint Publicly Accessible (Improper Access Control)

| Field | Details |
|---|---|
| **CWE** | CWE-284: Improper Access Control |
| **Severity** | Critical |
| **Affected Function** | `/api/get-user-permission` and all API endpoints |

**Description:**
API endpoints were accessible without any authentication or authorization checks. Any unauthenticated user could call these endpoints directly, bypassing the login requirement entirely.

**Risk:**
An attacker could directly query any API endpoint, access restricted data, and perform unauthorized operations on the system.

**Solution Implemented:**
Authentication and authorization middleware has been enforced on all API endpoints. Every request is validated against a valid session before any operation is performed. Endpoints without a valid authenticated session now return a `401 Unauthorized` response immediately.

**Status: Closed**

---

### 4.2 CWE-639 — IDOR Leading to Account Takeover (Authorization Bypass Through User-Controlled Keys)

| Field | Details |
|---|---|
| **CWE** | CWE-639: Authorization Bypass Through User-Controlled Keys |
| **Severity** | Critical |
| **Affected Function** | `/api/get-user-permission` |

**Description:**
The application was using a user-supplied `user_id` from the request body or headers to perform authorization checks. An attacker could manipulate this value to impersonate another user and access or modify their data, leading to a complete account takeover.

**Risk:**
Any logged-in user could take over another user's account by simply changing the `user_id` value in the request.

**Solution Implemented:**
The `user_id` is no longer accepted from the request body, headers, or any user-controlled input. It is now exclusively extracted from the **server-side authenticated session**. The application retrieves the user identity from the session token after authentication, making it impossible for a user to inject or spoof a different `user_id`.

**Status: Closed**

---

### 4.3 CWE-269 — Vertical Privilege Escalation (Improper Privilege Management)

| Field | Details |
|---|---|
| **CWE** | CWE-269: Improper Privilege Management |
| **Severity** | Critical |
| **Affected Function** | `/api/get-user-permission` |

**Description:**
A lower-privileged user (e.g. Analyst) could access endpoints and perform actions meant only for higher-privileged users (e.g. Super Admin, Admin). The application was not properly enforcing role-based access control at the API level.

**Risk:**
Regular users could perform admin-level operations such as deleting users, creating roles, or modifying system configuration.

**Solution Implemented:**
Role-Based Access Control (RBAC) is now strictly enforced on the server side. The user's role and permissions are fetched from the database using the server-side session identity. All sensitive endpoints check the user's permission set before allowing the operation. The `user_id` is sourced from the session (not from headers or request body), and permission checks are performed on every request.

**Status: Closed**

---

### 4.4 CWE-306 — Unauthorized File Access (Missing Authentication for Critical Function)

| Field | Details |
|---|---|
| **CWE** | CWE-306: Missing Authentication for Critical Function |
| **Severity** | Critical |
| **Affected Function** | File serving endpoints |

**Description:**
Files stored on the server (e.g. uploaded advertisements, documents) were accessible via their URLs without requiring any authentication. Anyone with or without a valid account could directly access these files.

**Risk:**
Sensitive files and documents uploaded to the system could be accessed by unauthorized external parties.

**Solution Implemented:**
Authentication and authorization checks are now required before serving any file. File endpoints validate the user's session before returning file content. Files are stored in secure, non-publicly accessible locations on the server. Path traversal protections have been implemented to prevent access to files outside the intended storage directory.

**Status: Closed**

---

### 4.5 CWE-434 — Unrestricted File Upload (Unrestricted Upload of File with Dangerous Type)

| Field | Details |
|---|---|
| **CWE** | CWE-434: Unrestricted Upload of File with Dangerous Type |
| **Severity** | Critical |
| **Affected Function** | All file upload endpoints (Advertisement, Feedback, Polls, etc.) |

**Description:**
The application allowed users to upload files of any type without validating the file extension or MIME type. An attacker could upload malicious files (e.g. `.php`, `.exe`, `.sh` scripts) and potentially execute them on the server.

**Risk:**
Successful upload of a malicious file could lead to Remote Code Execution (RCE) on the server.

**Solution Implemented:**
- **Whitelist validation:** Only specific, safe file types are now accepted (PNG, JPG, JPEG, PDF, SVG, MP4, DOC, DOCX)
- **MIME type validation:** The actual file signature (MIME type) is verified server-side, not just the file extension
- **File storage:** Uploaded files are stored outside the web root in a secure directory
- **Executable permissions removed:** Uploaded files are stripped of executable permissions
- **File renaming:** Uploaded files are renamed to a system-generated name to prevent directory traversal or execution by filename

**Status: Closed**

---

### 4.6 CWE-79 — Cross-Site Scripting via File Upload (XSS Through File Upload)

| Field | Details |
|---|---|
| **CWE** | CWE-79: Improper Neutralization of Input During Web Page Generation |
| **Severity** | Critical |
| **Affected Function** | All file upload endpoints |

**Description:**
The application allowed upload of files containing embedded malicious JavaScript (e.g. SVG files with `<script>` tags, HTML files, images with malicious EXIF metadata). When an admin viewed or previewed an uploaded file, the script would execute in their browser context.

**Risk:**
An attacker could steal admin session cookies, perform actions on behalf of the admin, or redirect the admin to a malicious site.

**Solution Implemented:**
- Malicious file types (HTML, SVG with scripts, XML) are blocked by the upload whitelist
- File content is validated server-side before storage
- SVG files are sanitized to remove any `<script>` tags or event handlers
- All uploaded file content is treated as untrusted data and served with appropriate `Content-Disposition: attachment` headers to prevent browser execution
- Input sanitization is applied on all user-supplied data

**Status: Closed**

---

### 4.7 CWE-287 — OTP Bypass (Improper Authentication)

| Field | Details |
|---|---|
| **CWE** | CWE-287: Improper Authentication |
| **Severity** | Critical |
| **Affected Function** | OTP verification (`/validate_otp`) |

**Description:**
The OTP (One-Time Password) implementation had logic flaws that could allow an attacker to bypass the OTP verification step. One-time passwords could potentially be reused, predicted, or brute-forced due to insufficient rate limiting and lack of OTP expiry enforcement.

**Risk:**
An attacker could bypass the second-factor OTP verification and authenticate as any user without possessing their mobile phone.

**Solution Implemented:**
- **Rate limiting using Redis:** OTP requests are limited to a maximum of **3 attempts per mobile number** within a **10-minute window** (`OTP_LIMIT = 3`, `OTP_WINDOW_SECONDS = 600`). Exceeding this limit blocks further OTP requests until the window expires
- **OTP expiry:** OTPs are tied to the user session and expire after the session window
- **Retry lockout:** After 3 failed mobile validation attempts, the session is reset and the user is required to start the flow again
- **No static OTP:** All static/hardcoded OTP fallbacks (e.g. `"123456"`) have been removed from the codebase
- **Server-side validation:** OTP is stored and validated entirely on the server side; the client has no control over the expected OTP value

**Status: Closed**

---

## 5. Medium Severity — Findings & Implementations

---

### 5.1 CWE-294 — Session Tokens via Session Manipulation (Authentication Bypass by Capture-Replay)

| Field | Details |
|---|---|
| **CWE** | CWE-294: Authentication Bypass by Capture-replay |
| **Severity** | Medium |
| **Affected Function** | `/login` and all authenticated endpoints |

**Description:**
After a user logged out, the session token remained valid. An attacker who captured the session token (e.g. via network sniffing or browser history) could replay it to re-authenticate as the logged-out user. The server was not automatically terminating sessions after logout or inactivity.

**Risk:**
Session hijacking after logout, allowing unauthorized re-access to a terminated session.

**Solution Implemented:**
- Session tokens are **immediately invalidated on logout** on the server side
- The server no longer relies on the client-side to invalidate sessions
- Permission checks are re-validated on every API request using the server-side session
- Sessions are automatically terminated after a predefined period of inactivity
- The `user_id` and permission data are freshly fetched from the session on each request — a manipulated or expired session results in immediate rejection

**Status: Closed**

---

### 5.2 CWE-20 — Improper Input Validation

| Field | Details |
|---|---|
| **CWE** | CWE-20: Improper Input Validation |
| **Severity** | Medium |
| **Affected Function** | All endpoints accepting user input |

**Description:**
User input was not being properly validated or sanitized across all endpoints. Unvalidated input could be used to perform injection attacks, XSS, or manipulate application logic.

**Risk:**
Injection attacks, XSS, logic manipulation, and other input-based exploits.

**Solution Implemented:**
- Input validation has been implemented on all endpoints that accept user data
- **Email validation:** Strict regex validation enforces the correct format (`^(?!\.)(?!.*\.\.)[a-zA-Z0-9._]+(?<!\.)@gmail\.com$`)
- **Mobile number validation:** Format and length are validated before processing
- **Language validation:** Input text is validated against an allowed language list (English, Hindi, Hinglish only). Inputs in unsupported languages (Arabic, Chinese, French, etc.) are rejected
- All user-supplied data is treated as untrusted and sanitized before use in queries or responses

**Status: Closed**

---

### 5.3 CWE-613 — Improper Session Management (Insufficient Session Expiration)

| Field | Details |
|---|---|
| **CWE** | CWE-613: Insufficient Session Expiration |
| **Severity** | Medium |
| **Affected Function** | `/api/get-user-permission` and authentication system |

**Description:**
JWT (JSON Web Tokens) used for authentication had long expiry times and no revocation mechanism. A compromised token remained valid indefinitely, and there was no way to invalidate it server-side.

**Risk:**
A stolen JWT could be used by an attacker for an extended period with no way to invalidate it.

**Solution Implemented:**
- **Short-lived access tokens** with a reduced expiry time have been implemented
- **Refresh token rotation** has been introduced — access tokens are refreshed using short-lived refresh tokens
- **Server-side token deny list:** Logout invalidates the token immediately on the server side, preventing replay attacks
- Token expiry is enforced on every authenticated request

**Status: Closed**

---

### 5.4 CWE-209 — SQL Query Disclosure in Error Messages

| Field | Details |
|---|---|
| **CWE** | CWE-209: Generation of Error Message Containing Sensitive Information |
| **Severity** | Medium |
| **Affected Function** | `/api/create_menu_with_submenu` and other API endpoints |

**Description:**
When an internal exception occurred, the application returned detailed error messages to the client that included raw SQL queries, table names, and column names. This information could be used by an attacker to craft targeted SQL injection attacks.

**Risk:**
Exposure of database schema information assists attackers in building precise SQL injection payloads.

**Solution Implemented:**
- All detailed error messages have been removed from API responses
- Custom error handling middleware now returns generic error messages (e.g. `"An internal error occurred"`) to the client
- Full error details (including stack traces and SQL queries) are logged **server-side only** — never exposed to the client
- All SQL queries use parameterized queries / ORM methods to prevent SQL injection at the source

**Status: Closed**

---

### 5.5 CWE-319 — Credentials Stored and Transmitted in Plain Text

| Field | Details |
|---|---|
| **CWE** | CWE-319: Cleartext Transmission of Sensitive Information |
| **Severity** | Medium |
| **Affected Function** | `/api/users` — User login and registration |

**Description:**
User credentials (username/email and password) were being stored or transmitted in plaintext. This meant that anyone with access to the database or network traffic could read credentials directly.

**Risk:**
Credential exposure via database breach or network interception.

**Solution Implemented:**
- **Passwords** are stored using strong one-way hashing (bcrypt) — never in plaintext
- **Usernames/emails** are now also stored in encrypted form in the database
- All communication between the client and server occurs over **HTTPS/TLS** to prevent network-level interception
- No sensitive credential data is logged in application logs

**Status: Closed**

---

### 5.6 CWE-307 — No Rate Limiting (Improper Restriction of Excessive Authentication Attempts)

| Field | Details |
|---|---|
| **CWE** | CWE-307: Improper Restriction of Excessive Authentication Attempts |
| **Severity** | Medium |
| **Affected Function** | `/api/users` — Login, OTP, Refresh Token endpoints |

**Description:**
The login, OTP, and token refresh endpoints had no rate limiting. An attacker could make an unlimited number of requests to brute-force passwords, OTP codes, or cause a denial-of-service.

**Risk:**
Brute-force attacks on login and OTP, credential stuffing, OTP bombing, API abuse, and denial-of-service.

**Solution Implemented:**
- **Rate limiting** has been applied on the login, OTP, and refresh token APIs using **Redis-based counters**
- **OTP rate limit:** Maximum 3 OTP requests per mobile number within a 10-minute window
- **Login rate limit:** Excessive failed login attempts trigger a lockout period
- **Machine-based rate limiting:** Rate limits are tracked by machine/IP ID to prevent distributed brute-force attempts
- **CAPTCHA:** CAPTCHA validation has been added to the login endpoint to prevent automated attack tools
- **Exponential backoff:** Retry delays increase with each failed attempt

**Status: Closed**

---

## 6. Low Severity — Findings & Implementations

---

### 6.1 CWE-203 — User Enumeration (Observable Discrepancy)

| Field | Details |
|---|---|
| **CWE** | CWE-203: Observable Discrepancy |
| **Severity** | Low |
| **Affected Function** | `/login` |

**Description:**
The login API returned different error messages depending on whether the email address existed in the system or not (e.g. *"User not found"* vs *"Incorrect password"*). An attacker could use this to enumerate valid user email addresses registered in the system.

**Risk:**
Attackers can build a list of valid email accounts for use in targeted phishing or credential stuffing attacks.

**Solution Implemented:**
The login API now returns a single **generic error message** for all failed login attempts regardless of the reason: *"Invalid credentials"*. This makes it impossible to determine whether an email address is registered or not from the API response.

**Status: Closed**

---

### 6.2 CWE-200 — Server Banner Grabbing (Exposure of Sensitive Information)

| Field | Details |
|---|---|
| **CWE** | CWE-200: Exposure of Sensitive Information to an Unauthorized Actor |
| **Severity** | Low |
| **Affected Function** | HTTP response headers — `/login` and all endpoints |

**Description:**
The HTTP response headers revealed server software details (e.g. web server name, version, framework). Attackers performing active reconnaissance could use this information to identify known vulnerabilities for the specific software version.

**Risk:**
Provides attackers with a roadmap to version-specific exploits.

**Solution Implemented:**
Server response headers have been configured to suppress or remove identifying information (server name, framework version, technology stack). This will be fully applied in the **BSES production environment** during final deployment.

**Status: Closed (To be applied on BSES production environment)**

---

### 6.3 CWE-306 — CAPTCHA Missing on Login (Missing Authentication for Critical Function)

| Field | Details |
|---|---|
| **CWE** | CWE-306: Missing Authentication for Critical Function |
| **Severity** | Low |
| **Affected Function** | `/login` |

**Description:**
The login page had no CAPTCHA or bot-detection mechanism. Automated tools (bots) could submit unlimited login attempts without any human verification challenge.

**Risk:**
Enables automated brute-force and credential stuffing attacks on the login form.

**Solution Implemented:**
CAPTCHA validation has been added to the login endpoint. Automated login requests that do not include a valid CAPTCHA response are rejected. This, combined with rate limiting (Section 5.6), provides two independent layers of protection against automated login attacks.

**Status: Closed**

---

## 7. External VAPT Closure

An external Vulnerability Assessment and Penetration Testing (VAPT) was conducted on the application by a third-party security assessor. All findings from the external VAPT — including items not identified during the internal VAPT — have been reviewed and fully addressed.

### 7.1 External VAPT Findings Summary

| Severity | Vulnerability | Identified In | Status |
|---|---|---|---|
| **High** | SQL Injection | Internal + External VAPT | Closed |
| **High** | Cross-Site Scripting (XSS) | Internal + External VAPT | Closed |
| **Medium** | Improper Input Validation | Internal + External VAPT | Closed |
| **Medium** | Improper Session Management | Internal + External VAPT | Closed |
| **Medium** | SQL Query Disclosure in Error Messages | Internal + External VAPT | Closed |
| **Medium** | Username and Password in Plain Text | Internal + External VAPT | Closed |
| **Medium** | No Rate Limit / Brute Force | Internal + External VAPT | Closed |
| **Medium** | Improper Email Validation | External VAPT Only | Closed |
| **Medium** | Clickjacking | External VAPT Only | Closed |
| **Low** | User Enumeration | Internal + External VAPT | Closed |
| **Low** | CAPTCHA Missing | Internal + External VAPT | Closed |
| **Low** | Weak Password Policy | External VAPT Only | Closed |
| **Low** | Security Headers Missing (Updated) | External VAPT Only | Closed |
| **Low** | Server Banner Grabbing | Internal + External VAPT | Closed |
| **Low** | Right Click Enabled | External VAPT Only | Closed |
| **Low** | Copy-Paste Buffer | External VAPT Only | Closed |
| **Low** | Concurrent Login | External VAPT Only | Closed |
| **Low** | CSP Header Missing | External VAPT Only | Closed |

---

### 7.2 High Severity — External VAPT Closures

**SQL Injection:**
All database queries have been rewritten to use parameterized queries and ORM methods (SQLAlchemy). No user-supplied input is directly concatenated into SQL strings. Detailed SQL error messages are suppressed from client responses.

**Cross-Site Scripting (XSS):**
All user input is sanitized before rendering. File upload restrictions prevent upload of HTML, SVG-with-scripts, or other executable content. Content Security Policy (CSP) headers have been configured at the Nginx server level to restrict script execution.

---

### 7.3 Medium Severity — External VAPT Only Closures

**Improper Email Validation:**
This issue was not identified during the internal VAPT but was highlighted in the external VAPT. Robust email validation has now been implemented in accordance with secure input validation standards. All email inputs are validated using strict regex patterns server-side before being accepted or processed by the application.

**Clickjacking:**
Clickjacking was not identified as a vulnerability during the internal VAPT. Following the external VAPT assessment, appropriate mitigation has been implemented by adding the `X-Frame-Options` header to all responses. This prevents the application from being embedded inside an `<iframe>` on an external malicious website, blocking UI redress attacks.

---

### 7.4 Low Severity — External VAPT Only Closures

**Weak Password Policy:**
This issue was not identified during the internal VAPT. Based on the external VAPT recommendation, a strong password policy has now been enforced. Users are required to set passwords that meet minimum complexity requirements (length, uppercase, lowercase, numeric, and special character criteria) before a new account is created or a password is changed.

**Security Headers Missing (Updated):**
During the internal VAPT, the "Security Headers Missing" observation was closed after implementing the recommended headers. The external VAPT identified additional headers to further strengthen HTTP response hardening. The Nginx configuration has been updated to include all recommended security headers including `Strict-Transport-Security`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`, and `Permissions-Policy`.

**Server Banner Grabbing:**
To mitigate server banner grabbing, necessary configuration updates have been applied to the Nginx server to suppress server version information from all HTTP response headers. Custom error pages have also been implemented to ensure that server information is not exposed in error responses, thereby improving the security posture of the application.

**Right Click Enabled:**
The "Right Click Enabled" observation was not identified as a security concern during the internal VAPT. However, during the external VAPT it was highlighted as an additional hardening recommendation. The right-click context menu restriction has been implemented on the Admin Panel login screen as an additional precautionary measure to prevent easy inspection or tampering by casual users.

**Copy-Paste Buffer:**
The Copy-Paste buffer control was not part of the initial implementation. Following the external VAPT recommendation as an additional security hardening measure, copy, paste, and related clipboard operations have been disabled on sensitive input fields (e.g. password fields) in the Admin Panel to reduce the risk of credential exposure via clipboard managers or browser extensions.

**Concurrent Login (New):**
To mitigate the Concurrent Login vulnerability, code-level modifications have been implemented to restrict users to a **single active session** at any given time. When a user logs in from a new device or browser, the previous session is automatically invalidated. Furthermore, a **15-minute idle session timeout** has been configured to automatically log out users after a period of inactivity, in accordance with security best practices.

**CSP Header Missing (New):**
The Content Security Policy (CSP) header was not identified as a finding during the internal VAPT and was not implemented initially. Based on the recommendation from the external VAPT, the CSP header has now been configured at the **Nginx server level** as an additional security layer. The CSP policy restricts the sources from which scripts, styles, images, and other resources can be loaded, significantly reducing the attack surface for XSS and data injection attacks.

---

## 8. Security Implementation Overview

The following table provides a consolidated view of all security controls implemented across the application:

| Security Control | Implementation | Area Covered |
|---|---|---|
| Authentication on all endpoints | Session-based auth check on every API call | All APIs |
| Authorization (RBAC) | Role and permission check from server-side session | All APIs |
| Server-side session identity | `user_id` sourced from session only, never from request | All APIs |
| Session invalidation on logout | Server-side token invalidation on logout | Auth system |
| Single active session enforcement | Concurrent login restricted to one active session | Auth system |
| 15-minute idle session timeout | Auto logout after inactivity | Auth system |
| Short-lived JWT + refresh token rotation | Reduced token expiry + server-side deny list | Auth system |
| OTP rate limiting (Redis) | Max 3 OTPs per mobile per 10 minutes | OTP flow |
| Login rate limiting | Redis-based counter + machine ID tracking | Login |
| CAPTCHA on login | Bot-detection challenge on login form | Login |
| Strong password policy | Complexity requirements enforced on password set/change | Login / User management |
| Generic error messages | No SQL, stack trace, or system info exposed to client | All APIs |
| File type whitelist | Only PNG/JPG/PDF/SVG/MP4/DOC/DOCX accepted | File upload |
| MIME type validation | Server-side file signature verification | File upload |
| File stored outside web root | Uploaded files not directly accessible via URL | File upload |
| Input validation (email, mobile) | Strict regex validation before processing | All inputs |
| Language restriction | Only English, Hindi, Hinglish accepted | Chatbot input |
| Password hashing (bcrypt) | Passwords never stored in plaintext | User management |
| Email/username encryption | Credentials stored encrypted in database | User management |
| HTTPS/TLS communication | All traffic encrypted in transit | All traffic |
| Server banner suppression | Nginx configured to hide server/framework version | HTTP headers / Nginx |
| X-Frame-Options header | Clickjacking protection via Nginx header | HTTP headers |
| Security headers (full set) | HSTS, X-Content-Type, X-XSS-Protection, Referrer-Policy, Permissions-Policy | HTTP headers / Nginx |
| Content Security Policy (CSP) | CSP configured at Nginx level to restrict resource sources | HTTP headers / Nginx |
| Parameterized SQL queries | ORM/parameterized queries prevent SQL injection | Database layer |
| Right-click restriction | Context menu disabled on Admin Panel login screen | Admin Panel UI |
| Copy-paste restriction | Clipboard operations disabled on sensitive input fields | Admin Panel UI |

---

*All identified vulnerabilities from both the internal and external VAPT assessments have been fully addressed and closed.*

*For any queries regarding this document, please contact the development team.*

---

*End of Document*
