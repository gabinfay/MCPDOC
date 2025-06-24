# Consolidated Documentation: Admin Functions

This file is a consolidation of 7 smaller documents from the 'Admin_Functions' category.



---

## --- Merged from: create_user.md ---

# create_user()

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

## --- Merged from: delete_user.md ---

# delete_user()

Delete a user. Requires a `service_role` key.

## Examples

### Removes a user

```python
supabase.auth.admin.delete_user(
    "715ed5db-f090-4b8c-a067-640ecee36aa0"
)
```

---

## --- Merged from: generate_link.md ---

# generate_link()

## Examples

### Generate a signup link

```python
response = supabase.auth.admin.generate_link(
    {
        "type": "signup",
        "email": "email@example.com",
        "password": "secret",
    }
)
```


### Generate an invite link

```python
response = supabase.auth.admin.generate_link(
    {
        "type": "invite",
        "email": "email@example.com",
    }
)
```


### Generate a magic link

```python
response = supabase.auth.admin.generate_link(
    {
        "type": "magiclink",
        "email": "email@example.com",
    }
)
```


### Generate a recovery link

```python
response = supabase.auth.admin.generate_link(
    {
        "type": "recovery",
        "email": "email@example.com",
    }
)
```


### Generate links to change current email address

```python
# Generate an email change link to be sent to the current email address
response = supabase.auth.admin.generate_link(
    {
        "type": "email_change_current",
        "email": "current.email@example.com",
        "new_email": "new.email@example.com",
    }
)

# Generate an email change link to be sent to the new email address
response = supabase.auth.admin.generate_link(
    {
        "type": "email_change_new",
        "email": "current.email@example.com",
        "new_email": "new.email@example.com",
    }
)
```

---

## --- Merged from: get_user_by_id.md ---

# get_user_by_id()

## Examples

### Fetch the user object using the access_token jwt

```python
response = supabase.auth.admin.get_user_by_id(1)
```

---

## --- Merged from: invite_user_by_email.md ---

# invite_user_by_email()

Sends an invite link to an email address.

## Examples

### Invite a user

```python
response = supabase.auth.admin.invite_user_by_email("email@example.com")
```

---

## --- Merged from: list_users.md ---

# list_users()

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

## --- Merged from: update_user_by_id.md ---

# update_user_by_id()

## Examples

### Updates a user's email

```python
response = supabase.auth.admin.update_user_by_id(
    "11111111-1111-1111-1111-111111111111",
    {
        "email": "new@email.com",
    }
)
```


### Updates a user's password

```python
response = supabase.auth.admin.update_user_by_id(
    "6aa5d0d4-2a9f-4483-b6c8-0cf4c6c98ac4",
    {
        "password": "new_password",
    }
)
```


### Updates a user's metadata

```python
response = supabase.auth.admin.update_user_by_id(
    "6aa5d0d4-2a9f-4483-b6c8-0cf4c6c98ac4",
    {
        "user_metadata": {"hello": "world"},
    }
)
```


### Updates a user's app_metadata

```python
response = supabase.auth.admin.update_user_by_id(
    "6aa5d0d4-2a9f-4483-b6c8-0cf4c6c98ac4",
    {
        "app_metadata": {"plan": "trial"},
    }
)
```


### Confirms a user's email address

```python
response = supabase.auth.admin.update_user_by_id(
    "6aa5d0d4-2a9f-4483-b6c8-0cf4c6c98ac4",
    {
        "email_confirm": True,
    }
)
```


### Confirms a user's phone number

```python
response = supabase.auth.admin.update_user_by_id(
    "6aa5d0d4-2a9f-4483-b6c8-0cf4c6c98ac4",
    {
        "phone_confirm": True,
    }
)
```