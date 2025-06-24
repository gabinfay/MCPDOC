# Consolidated Documentation: Multi Factor Authentication

This file is a consolidation of 7 smaller documents from the 'Multi_Factor_Authentication' category.



---

## --- Merged from: mfachallenge.md ---

# mfa.challenge()

## Examples

### Create a challenge for a factor

```python
response = supabase.auth.mfa.challenge(
    {"factor_id": "34e770dd-9ff9-416c-87fa-43b31d7ef225"}
)
```

---

## --- Merged from: mfachallenge_and_verify.md ---

# mfa.challenge_and_verify()

## Examples

### Create and verify a challenge for a factor

```python
response = supabase.auth.mfa.challenge_and_verify(
    {
        "factor_id": "34e770dd-9ff9-416c-87fa-43b31d7ef225",
        "code": "123456",
    }
)
```

---

## --- Merged from: mfadelete_factor.md ---

# mfa.delete_factor()

## Examples

### Delete a factor for a user

```python
response = supabase.auth.admin.mfa.delete_factor(
    {
        "id": "34e770dd-9ff9-416c-87fa-43b31d7ef225",
        "user_id": "a89baba7-b1b7-440f-b4bb-91026967f66b"
    }
)
```

---

## --- Merged from: mfaenroll.md ---

# mfa.enroll()

## Examples

### Enroll a time-based, one-time password (TOTP) factor

```python
response = supabase.auth.mfa.enroll(
    {
        "factor_type": "totp",
        "friendly_name": "your_friendly_name",
    }
)
```

---

## --- Merged from: mfaget_authenticator_assurance_level.md ---

# mfa.get_authenticator_assurance_level()

## Examples

### Get the AAL details of a session

```python
response = supabase.auth.mfa.get_authenticator_assurance_level()
```

---

## --- Merged from: mfaunenroll.md ---

# mfa.unenroll()

## Examples

### Unenroll a factor

```python
response = supabase.auth.mfa.unenroll(
    {"factor_id": "34e770dd-9ff9-416c-87fa-43b31d7ef225"}
)
```

---

## --- Merged from: mfaverify.md ---

# mfa.verify()

## Examples

### Verify a challenge for a factor

```python
response = supabase.auth.mfa.verify(
    {
        "factor_id": "34e770dd-9ff9-416c-87fa-43b31d7ef225",
        "challenge_id": "4034ae6f-a8ce-4fb5-8ee5-69a5863a7c15",
        "code": "123456",
    }
)
```