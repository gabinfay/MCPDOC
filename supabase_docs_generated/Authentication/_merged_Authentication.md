# Consolidated Documentation: Authentication

This file is a consolidation of 21 smaller documents from the 'Authentication' category.



---

## --- Merged from: exchange_code_for_session.md ---

# exchange_code_for_session()

## Examples

### Exchange Auth Code

```python
response = supabase.auth.exchange_code_for_session(
    {"auth_code": "34e770dd-9ff9-416c-87fa-43b31d7ef225"}
)
```

---

## --- Merged from: get_session.md ---

# get_session

## Examples

### Get the session data

```python
response = supabase.auth.get_session()
```

---

## --- Merged from: get_user.md ---

# get_user

## Examples

### Get the logged in user with the current existing session

```
response = supabase.auth.get_user()
```


### Get the logged in user with a custom access token jwt

```
response = supabase.auth.get_user(jwt)
```

---

## --- Merged from: get_user_identities.md ---

# get_user_identities()

## Examples

### Returns a list of identities linked to the user

```python
response = supabase.auth.get_user_identities()
```

---

## --- Merged from: link_identity.md ---

# link_identity()

## Examples

### Link an identity to a user

```python
response = supabase.auth.link_identity(
    {provider: "github"}
)
```

---

## --- Merged from: reauthenticate.md ---

# reauthenticate()

## Examples

### Send reauthentication nonce

```python
response = supabase.auth.reauthenticate()
```

---

## --- Merged from: refresh_session.md ---

# refresh_session()

Returns a new session, regardless of expiry status.
Takes in an optional refresh token. If not passed in, then refresh_session() will attempt to retrieve it from get_session().
If the current session's refresh token is invalid, an error will be thrown.


## Examples

### Refresh session using the current session

```
response = supabase.auth.refresh_session()
```

---

## --- Merged from: resend.md ---

# resend()

## Examples

### Resend an email signup confirmation

```python
response = supabase.auth.resend(
    {
        "type": "signup",
        "email": "email@example.com",
        "options": {
            "email_redirect_to": "https://example.com/welcome",
        },
    }
)
```


### Resend a phone signup confirmation

```python
response = supabase.auth.resend(
    {
        "type": "sms",
        "phone": "1234567890",
    }
)
```


### Resend email change email

```python
response = supabase.auth.resend(
    {
        "type": "email_change",
        "email": "email@example.com",
    }
)
```


### Resend phone change OTP

```python
response = supabase.auth.resend(
    {
        "type": "phone_change",
        "phone": "1234567890",
    }
)
```

---

## --- Merged from: reset_password_for_email.md ---

# reset_password_for_email()

## Examples

### Reset password

```python
supabase.auth.reset_password_for_email(
    email,
    {
        "redirect_to": "https://example.com/update-password",
    }
)
```

---

## --- Merged from: set_session.md ---

# set_session()

Sets the session data from the current session. If the current session is expired, setSession will take care of refreshing it to obtain a new session.
If the refresh token or access token in the current session is invalid, an error will be thrown.


## Examples

### Refresh the session

```python
response = supabase.auth.set_session(access_token, refresh_token)
```

---

## --- Merged from: sign_in_anonymously.md ---

# sign_in_anonymously()

## Examples

### Create an anonymous user

```python
response = supabase.auth.sign_in_anonymously(
    {"options": {"captcha_token": ""}}
)
```


### Create an anonymous user with custom user metadata

```python
response = supabase.auth.sign_in_anonymously(
    {"options": {"data": {}}}
)
```

---

## --- Merged from: sign_in_with_id_token.md ---

# sign_in_with_id_token

## Examples

### Sign In using ID Token

```python
response = supabase.auth.sign_in_with_id_token(
    {
        "provider": "google",
        "token": "your-id-token",
    }
)
```

---

## --- Merged from: sign_in_with_oauth.md ---

# sign_in_with_oauth

## Examples

### Sign in using a third-party provider

```python
response = supabase.auth.sign_in_with_oauth(
    {"provider": "github"}
)
```


### Sign in using a third-party provider with redirect

```python
response = supabase.auth.sign_in_with_oauth(
    {
        "provider": "github",
        "options": {
            "redirect_to": "https://example.com/welcome",
        }
    }
)
```


### Sign in with scopes

```python
response = supabase.auth.sign_in_with_oauth(
    {
        "provider": "github",
        "options": {
            "scopes": "repo gist notifications",
        }
    }
)
```

---

## --- Merged from: sign_in_with_otp.md ---

# sign_in_with_otp

## Examples

### Sign in with email

```python
response = supabase.auth.sign_in_with_otp(
    {
        "email": "email@example.com",
        "options": {
            "email_redirect_to": "https://example.com/welcome",
        },
    }
)
```


### Sign in with SMS OTP

```python
response = supabase.auth.sign_in_with_otp(
    {"phone": "+13334445555"}
)
```


### Sign in with WhatsApp OTP

```python
response = supabase.auth.sign_in_with_otp(
    {
        "phone": "+13334445555",
        "options": {
            "channel": "whatsapp",
        },
    }
)
```

---

## --- Merged from: sign_in_with_password.md ---

# sign_in_with_password

## Examples

### Sign in with email and password

```python
response = supabase.auth.sign_in_with_password(
    {
        "email": "email@example.com",
        "password": "example-password",
    }
)
```


### Sign in with phone and password

```python
response = supabase.auth.sign_in_with_password(
    {
        "phone": "+13334445555",
        "password": "some-password",
    }
)
```

---

## --- Merged from: sign_in_with_sso.md ---

# sign_in_with_sso()

## Examples

### Sign in with email domain

```python
response = supabase.auth.sign_in_with_sso(
    {"domain": "company.com"}
)
```


### Sign in with provider UUID

```python
response = supabase.auth.sign_in_with_sso(
    {"provider_id": "21648a9d-8d5a-4555-a9d1-d6375dc14e92"}
)
```

---

## --- Merged from: sign_out.md ---

# sign_out()

## Examples

### Sign out

```python
response = supabase.auth.sign_out()
```

---

## --- Merged from: sign_up.md ---

# sign_up()

## Examples

### Sign up with an email and password

```python
response = supabase.auth.sign_up(
    {
        "email": "email@example.com",
        "password": "password",
    }
)
```


### Sign up with a phone number and password (SMS)

```python
response = supabase.auth.sign_up(
    {
        "phone": "123456789",
        "password": "password",
    }
)
```


### Sign up with a phone number and password (whatsapp)

```python
response = supabase.auth.sign_up(
    {
        "phone": "123456789",
        "password": "password",
        "options": {"channel": "whatsapp"},
    }
)
```


### Sign up with additional user metadata

```python
response = supabase.auth.sign_up(
    {
        "email": "email@example.com",
        "password": "password",
        "options": {"data": {"first_name": "John", "age": 27}},
    }
)
```


### Sign up with a redirect URL

```python
response = supabase.auth.sign_up(
    {
        "email": "hello1@example.com",
        "password": "password",
        "options": {
            "email_redirect_to": "https://example.com/welcome",
        },
    }
)
```

---

## --- Merged from: unlink_identity.md ---

# unlink_identity()

## Examples

### Unlink an identity

```python
# retrieve all identites linked to a user
response = supabase.auth.get_user_identities()

# find the google identity
google_identity = list(
    filter(lambda identity: identity.provider == "google", res.identities)
).pop()

# unlink the google identity
response = supabase.auth.unlink_identity(google_identity)
```

---

## --- Merged from: update_user.md ---

# update_user()

## Examples

### Update the email for an authenticated user

```python
response = supabase.auth.update_user(
    {"email": "new@email.com"}
)
```


### Update the phone number for an authenticated user

```python
response = supabase.auth.update_user(
    {"phone": "123456789"}
)
```


### Update the password for an authenticated user

```python
response = supabase.auth.update_user(
    {"password": "new password"}
)
```


### Update the user's metadata

```python
response = supabase.auth.update_user(
    {
        "data": {"hello": "world"},
    }
)
```


### Update the user's password with a nonce

```python
response = supabase.auth.update_user(
    {
        "password": "new password",
        "nonce": "123456",
    }
)
```

---

## --- Merged from: verify_otp.md ---

# verify_otp

## Examples

### Verify Signup One-Time Password (OTP)

```python
response = supabase.auth.verify_otp(
    {
        "email": "email@example.com",
        "token": "123456",
        "type": "email",
    }
)
```


### Verify SMS One-Time Password (OTP)

```python
response = supabase.auth.verify_otp(
    {
        "phone": "+13334445555",
        "token": "123456",
        "type": "sms",
    }
)
```


### Verify Email Auth (Token Hash)

```python
response = supabase.auth.verify_otp(
    {
        "email": "email@example.com",
        "token_hash": "<token-hash>",
        "type": "email",
    }
)
```