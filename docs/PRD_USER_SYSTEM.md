# User System PRD

Last updated: 2026-06-22
Current version: v6.0.8
Scope: public account system, email verification, Google login, sessions, trips, and admin visibility.

## Product Goal

VisePanda should let guests explore and ask travel questions immediately, then invite them to create an account when they want to save work, recover trips, or continue planning across sessions.

The account system must feel familiar and low-friction:

- Sign in with Google.
- Sign up with email and password only.
- Verify email with a code before the account is treated as trusted.
- Keep travel planning usable for guests.
- Keep saved trips and admin operations behind authentication.

## User Roles

| Role | Purpose | Access |
| --- | --- | --- |
| Guest | Evaluate the product before committing | Plan, Ask, Cities, Tools, local trip draft |
| User | Save and return to travel plans | Guest access plus saved trips and profile |
| Admin | Maintain user base | User access plus user management endpoints |

Ops is not an active product role in v6.0.8. If operational review returns, add it deliberately instead of assuming old v3 documents are still valid.

## Core Requirements

### Registration

- The registration form asks only for email and password.
- No name field is required.
- The backend stores a password hash, email verification status, timestamps, and role.
- A newly registered email/password account must verify email before normal sign-in is considered complete.
- Duplicate emails return a clear error.
- Weak or malformed inputs return clear errors without leaking internal details.

### Email Verification

- Registration creates an email verification code.
- `RESEND_API_KEY` and `EMAIL_FROM` enable real email delivery through Resend.
- If Resend is not configured, local and test flows still work through controlled test exposure.
- The user confirms the code through `/api/auth/verify-email`.
- The user can request a fresh code through `/api/auth/resend-verification`.
- Verification codes must expire and must not be treated as passwords.

### Google Login

- Google login starts at `/api/auth/google/start`.
- The callback endpoint exchanges the code, reads the Google email, creates or updates the local user, and returns a normal VisePanda session.
- Google accounts are considered email-verified after a successful Google identity response.
- If Google credentials are missing, the API should fail gracefully and the UI should not present a broken primary path.

### Email And Password Login

- Login requires email and password only.
- The form should not ask for display name.
- Unverified email/password users should be guided to verification or resend, not silently logged in as fully active.
- Disabled or deleted users must not receive sessions.

### Session

- The frontend stores the active token in `sessionStorage["vp_token"]`.
- `/api/auth/me` returns the public user object for the current token.
- Logout clears the server-side session and local token.
- The public user shape must avoid password hashes, reset tokens, verification codes, and internal secrets.

### Trips

- Guests can create a local draft experience.
- Saving to the backend requires authentication.
- A user can list and delete only their own trips.
- Trip API responses should be stable enough for the frontend to render even when content is partial.

### Admin

- Admin access requires a valid session and admin role.
- Admin can list users and delete users.
- Admin credentials are seeded only from environment variables.
- Weak default admin passwords are ignored.

## Current API Surface

- `POST /api/auth/register`
- `POST /api/auth/verify-email`
- `POST /api/auth/resend-verification`
- `GET /api/auth/google/start`
- `GET /api/auth/google/callback`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/update-profile`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/trips`
- `POST /api/trips`
- `DELETE /api/trips/:id`
- `GET /api/admin/users`
- `DELETE /api/admin/users/:id`

## Acceptance Criteria

- A new user can register with email and password only.
- A verification code can be generated, delivered or exposed in test mode, and confirmed.
- A verified user can log in, refresh the page, remain signed in for the session, save trips, and log out.
- Google OAuth can create a verified local account and session when configured.
- A guest can still use Plan, Ask, Cities, and Tools without account friction.
- Admin endpoints reject guests and normal users.
- Tests cover register, verify, login, Google fallback behavior, session lookup, trips ownership, and admin gating.

## Non-Goals

- Paid subscriptions.
- User avatars.
- Social login beyond Google.
- Long-lived refresh-token rotation.
- External hosted database migration.
- Full admin analytics dashboard.

## Risks

- SQLite on Vercel serverless storage is not durable across cold-start environments. It is acceptable for the current prototype, but production account durability requires Turso, Supabase, Neon, or another hosted database.
- Email delivery depends on Resend configuration and DNS sender reputation.
- OAuth redirect URIs must match the deployed domain exactly: `go2china.space`.

## Next Improvements

- Add clear UI states for pending verification.
- Add resend countdown and code expiry copy.
- Add browser smoke tests for email registration and Google-start fallback.
- Move account storage to a durable managed database before real user acquisition.
