# Consolidated Documentation: Authentication

This file merges 14 sections.

---

## --- sign_up() ---

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

## --- sign_in_anonymously() ---

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

## --- sign_in_with_password ---

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

## --- sign_in_with_id_token ---

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

## --- sign_in_with_otp ---

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

## --- sign_in_with_oauth ---

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

## --- sign_in_with_sso() ---

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

## --- sign_out() ---

## Examples

### Sign out

```python
response = supabase.auth.sign_out()
```
---

## --- reset_password_for_email() ---

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

## --- verify_otp ---

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
---

## --- get_session ---

## Examples

### Get the session data

```python
response = supabase.auth.get_session()
```
---

## --- refresh_session() ---

Returns a new session, regardless of expiry status.
Takes in an optional refresh token. If not passed in, then refresh_session() will attempt to retrieve it from get_session().
If the current session's refresh token is invalid, an error will be thrown.


## Examples

### Refresh session using the current session

```
response = supabase.auth.refresh_session()
```
---

## --- get_user ---

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

## --- get_user_identities() ---

## Examples

### Returns a list of identities linked to the user

```python
response = supabase.auth.get_user_identities()
```