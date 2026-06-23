# User System Technical Notes

Last updated: 2026-06-22
Current version: v6.0.8

## Current State

The user system is active and lives mainly in `api/auth.py` and the auth dialog in `web/index.html` / `web/app.js`.

Current capabilities:

- Email/password registration
- Registration without name collection
- Email verification codes
- Resend verification code
- Password login only after email verification
- Session token issuance
- Session restore through `/api/auth/me`
- Logout
- Profile update
- Password reset
- Optional Google OAuth
- Minimal admin user list/delete
- Authenticated Trips API

## Data Storage

SQLite is currently used.

Relevant tables include:

- `users`
- `sessions`
- `password_resets`
- `trips`
- `email_verifications`
- `oauth_states`

The database path can be configured with:

- `AUTH_DB_PATH`

## Registration Flow

```text
POST /api/auth/register
        |
        v
create or update unverified password user
        |
        v
create six-digit verification code
        |
        v
send through Resend if configured
        |
        v
frontend switches to Verify email state
```

Important behavior:

- Name is not required.
- Email is required.
- Password is required.
- Public registration never creates admin users.
- Verification code is hashed before storage.
- Development can expose the code only with `AUTH_EXPOSE_EMAIL_CODE=1`.

## Email Verification Flow

```text
POST /api/auth/verify-email
        |
        v
validate code, expiry, attempts
        |
        v
mark user email verified
        |
        v
return token + public user
```

Unverified users receive a password-login failure and must verify first.

## Resend Integration

Optional variables:

- `RESEND_API_KEY`
- `EMAIL_FROM`

If Resend is not configured, the backend returns development delivery behavior. Do not rely on that in production.

## Google OAuth Flow

Optional variables:

- `APP_BASE_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`

Flow:

```text
GET /api/auth/google/start
        |
        v
create oauth state
        |
        v
redirect to Google OAuth
        |
        v
GET /api/auth/google/callback
        |
        v
validate state, exchange code, fetch userinfo
        |
        v
create or link user
        |
        v
store token in sessionStorage from callback page
```

Frontend behavior:

- `GET /api/auth/config` determines whether Google is enabled.
- Google login button is hidden unless both client id and secret are configured.

## Session Model

Frontend stores the session token in:

```text
sessionStorage["vp_token"]
```

This is intentional. Avoid changing it to persistent local storage without a security review.

## Public User Shape

The frontend expects user data such as:

- `id`
- `email`
- `name`
- `role`
- `emailVerified`
- `authProvider`

## Admin

Admin is intentionally minimal.

Current endpoints:

- `GET /api/admin/users`
- `DELETE /api/admin/users/:id`

Admin seed variables:

- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

Weak default admin passwords are ignored.

## Security Rules

- Never commit real API keys or OAuth secrets.
- Never enable `AUTH_EXPOSE_EMAIL_CODE=1` in production.
- Never enable `AUTH_EXPOSE_RESET_TOKEN=1` in production.
- Never allow public registration to choose role.
- Keep verification-code and reset-token responses generic where appropriate.
- Keep password login blocked until email is verified.

## Test Coverage

Primary tests:

- `tests/test_auth_contract.py`
- `tests/test_admin_contract.py`
- `tests/test_trips_contract.py`
- `web/tests/auth-state.test.js`
- `web/tests/stability-ui.test.js`

Run:

```powershell
python -m unittest discover -s tests -v
node --test web/tests/*.test.js
```

## Next Improvements

- Production Google OAuth test on `go2china.space`.
- Production Resend delivery test.
- Better profile UX copy.
- Browser smoke test for register -> verify -> signed-in profile.
- Consider managed Postgres after product behavior stabilizes.
