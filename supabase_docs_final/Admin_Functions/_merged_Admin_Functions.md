# Consolidated Documentation: Admin Functions

This file merges 5 sections.

---

## --- get_user_by_id() ---

## Examples

### Fetch the user object using the access_token jwt

```python
response = supabase.auth.admin.get_user_by_id(1)
```
---

## --- list_users() ---

## Examples

### Get a page of users

```python
response = supabase.auth.admin.list_users()
```


### Paginated list of users

```python
response = supabase.auth.admin.list_users(
    page=1,
    per_page=1000,
)
```
---

## --- create_user() ---

## Examples

### With custom user metadata

```python
response = supabase.auth.admin.create_user(
    {
        "email": "user@email.com",
        "password": "password",
        "user_metadata": {"name": "Yoda"},
    }
)
```


### Auto-confirm the user's email

```python
response = supabase.auth.admin.create_user(
    {
        "email": "user@email.com",
        "email_confirm": True,
    }
)
```


### Auto-confirm the user's phone number

```python
response = supabase.auth.admin.create_user(
    {
        "phone": "1234567890",
        "phone_confirm": True,
    }
)
```
---

## --- delete_user() ---

Delete a user. Requires a `service_role` key.

## Examples

### Removes a user

```python
supabase.auth.admin.delete_user(
    "715ed5db-f090-4b8c-a067-640ecee36aa0"
)
```
---

## --- invite_user_by_email() ---

Sends an invite link to an email address.

## Examples

### Invite a user

```python
response = supabase.auth.admin.invite_user_by_email("email@example.com")
```