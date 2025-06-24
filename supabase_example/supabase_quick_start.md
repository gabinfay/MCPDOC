# Supabase Quick Start Guide

## You can initialize a new Supabase client using the `create_client()` method.
The Supabase client is your entrypoint to the rest of the Supabase functionality and is the easiest way to interact with everything we offer within the Supabase ecosystem.

```python
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
```

## Fetch data: select()
```python response = ( supabase.table("planets") .select("*") .execute() ) ```

```python
response = (
    supabase.table("planets")
    .select("*")
    .execute()
)
```

## Create data: insert()
```python response = ( supabase.table("planets") .insert({"id": 1, "name": "Pluto"}) .execute() ) ```

```python
response = (
    supabase.table("planets")
    .insert({"id": 1, "name": "Pluto"})
    .execute()
)
```

## sign_up()
```python response = supabase.auth.sign_up( { "email": "email@example.com", "password": "password", } ) ```

```python
response = supabase.auth.sign_up(
    {
        "email": "email@example.com",
        "password": "password",
    }
)
```

## sign_in_with_password
```python response = supabase.auth.sign_in_with_password( { "email": "email@example.com", "password": "example-password", } ) ```

```python
response = supabase.auth.sign_in_with_password(
    {
        "email": "email@example.com",
        "password": "example-password",
    }
)
```

