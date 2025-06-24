# Consolidated Documentation: Utilities

This file merges 24 sections.

---

## --- Using Filters ---

Filters allow you to only return rows that match certain conditions.

Filters can be used on `select()`, `update()`, `upsert()`, and `delete()` queries.

If a Postgres function returns a table response, you can also apply filters.


## Examples

### Applying Filters

```python
# Correct
response = (
    supabase.table("instruments")
    .select("name, section_id")
    .eq("name", "flute")
    .execute()
)

# Incorrect
response = (
    supabase.table("instruments")
    .eq("name", "flute")
    .select("name, section_id")
    .execute()
)
```


### Chaining

```python
response = (
    supabase.table("instruments")
    .select("name, section_id")
    .gte("octave_range", 3)
    .lt("octave_range", 7)
    .execute()
)
```


### Conditional chaining

```python
filterByName = None
filterOctaveLow = 3
filterOctaveHigh = 7

query = supabase.table("instruments").select("name, section_id")

if filterByName:
    query = query.eq("name", filterByName)

if filterAgeLow:
    query = query.gte("octave_range", filterOctaveLow)

if filterAgeHigh:
    query = query.lt("octave_range", filterOctaveHigh)

response = query.execute()
```


### Filter by values within JSON column

```python
response = (
    supabase.table("users")
    .select("*")
    .eq("address->postcode", 90210)
    .execute()
)
```


### Filter Foreign Tables

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments!inner(name)")
    .eq("instruments.name", "flute")
    .execute()
)
```
---

## --- contains() ---

Only relevant for jsonb, array, and range columns. Match only rows where `column` contains every element appearing in `value`.


## Examples

### On array columns

```python
response = (
    supabase.table("issues")
    .select("*")
    .contains("tags", ["is:open", "priority:low"])
    .execute()
)
```


### On range columns

```python
response = (
    supabase.table("reservations")
    .select("*")
    .contains("during", "[2000-01-01 13:00, 2000-01-01 13:30)")
    .execute()
)
```


### On `jsonb` columns

```python
response = (
    supabase.table("users")
    .select("*")
    .contains("address", {"postcode": 90210})
    .execute()
)
```
---

## --- contained_by() ---

Only relevant for jsonb, array, and range columns. Match only rows where every element appearing in `column` is contained by `value`.


## Examples

### On array columns

```python
response = (
    supabase.table("classes")
    .select("name")
    .contained_by("days", ["monday", "tuesday", "wednesday", "friday"])
    .execute()
)
```


### On range columns

```python
response = (
    supabase.table("reservations")
    .select("*")
    .contained_by("during", "[2000-01-01 00:00, 2000-01-01 23:59)")
    .execute()
)
```


### On `jsonb` columns

```python
response = (
    supabase.table("users")
    .select("name")
    .contained_by("address", {})
    .execute()
)
```
---

## --- range_adjacent() ---

Only relevant for range columns. Match only rows where `column` is mutually exclusive to `range` and there can be no element between the two ranges.


## Examples

### With `select()`

```python
response = (
    supabase.table("reservations")
    .select("*")
    .range_adjacent("during", ["2000-01-01 12:00", "2000-01-01 13:00"])
    .execute()
)
```
---

## --- overlaps() ---

Only relevant for array and range columns. Match only rows where `column` and `value` have an element in common.


## Examples

### On array columns

```python
response = (
    supabase.table("issues")
    .select("title")
    .overlaps("tags", ["is:closed", "severity:high"])
    .execute()
)
```


### On range columns

```python
response = (
    supabase.table("reservations")
    .select("*")
    .overlaps("during", "[2000-01-01 12:45, 2000-01-01 13:15)")
    .execute()
)
```
---

## --- text_search() ---

Only relevant for text and tsvector columns. Match only rows where `column` matches the query string in `query`.


## Examples

### Text search

```python
response = (
    supabase.table("texts")
    .select("content")
    .text_search(
        "content",
        "'eggs' & 'ham'",
        options={"config": "english"},
    )
    .execute()
)
```


### Basic normalization

```python
response = (
    supabase.table("quotes")
    .select("catchphrase")
    .text_search(
        "catchphrase",
        "'fat' & 'cat'",
        options={"type": "plain", "config": "english"},
    )
    .execute()
)
```


### Full normalization

```python
response = (
    supabase.table("quotes")
    .select("catchphrase")
    .text_search(
        "catchphrase",
        "'fat' & 'cat'",
        options={"type": "phrase", "config": "english"},
    )
    .execute()
)
```


### Websearch

```python
response = (
    supabase.table("quotes")
    .select("catchphrase")
    .text_search(
        "catchphrase",
        "'fat or cat'",
        options={"type": "websearch", "config": "english"},
    )
    .execute()
)
```
---

## --- match() ---

Match only rows where each column in `query` keys is equal to its associated value. Shorthand for multiple `.eq()`s.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .match({"id": 2, "name": "Earth"})
    .execute()
)
```
---

## --- not_() ---

Match only rows which doesn't satisfy the filter. `not_` expects you to use the raw PostgREST syntax for the filter values.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .not_.is_("name", "null")
    .execute()
)
```
---

## --- or_() ---

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("name")
    .or_("id.eq.2,name.eq.Mars")
    .execute()
)
```


### Use `or` with `and`

```python
response = (
    supabase.table("planets")
    .select("name")
    .or_("id.gt.3,and(id.eq.1,name.eq.Mercury)")
    .execute()
)
```


### Use `or` on referenced tables

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments!inner(name)")
    .or_("book_id.eq.1,name.eq.guqin", reference_table="instruments")
    .execute()
)
```
---

## --- Using Modifiers ---

Filters work on the row level—they allow you to return rows that
only match certain conditions without changing the shape of the rows.
Modifiers are everything that don't fit that definition—allowing you to
change the format of the response (e.g., returning a CSV string).

Modifiers must be specified after filters. Some modifiers only apply for
queries that return rows (e.g., `select()` or `rpc()` on a function that
returns a table response).


## Examples
---

## --- Using Explain ---

For debugging slow queries, you can get the [Postgres `EXPLAIN` execution plan](https://www.postgresql.org/docs/current/sql-explain.html) of a query
using the `explain()` method. This works on any query, even for `rpc()` or writes.

Explain is not enabled by default as it can reveal sensitive information about your database.
It's best to only enable this for testing environments but if you wish to enable it for production you can provide additional protection by using a `pre-request` function.

Follow the [Performance Debugging Guide](/docs/guides/database/debugging-performance) to enable the functionality on your project.


## Examples

### Get the execution plan

```python
response = (
    supabase.table("planets")
    .select("*")
    .explain()
    .execute()
)
```


### Get the execution plan with analyze and verbose

```python
response = (
    supabase.table("planets")
    .select("*")
    .explain(analyze=True, verbose=True)
    .execute()
)
```
---

## --- Overview ---

## Examples
---

## --- update_user() ---

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

## --- link_identity() ---

## Examples

### Link an identity to a user

```python
response = supabase.auth.link_identity(
    {provider: "github"}
)
```
---

## --- unlink_identity() ---

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

## --- reauthenticate() ---

## Examples

### Send reauthentication nonce

```python
response = supabase.auth.reauthenticate()
```
---

## --- resend() ---

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

## --- set_session() ---

Sets the session data from the current session. If the current session is expired, setSession will take care of refreshing it to obtain a new session.
If the refresh token or access token in the current session is invalid, an error will be thrown.


## Examples

### Refresh the session

```python
response = supabase.auth.set_session(access_token, refresh_token)
```
---

## --- exchange_code_for_session() ---

## Examples

### Exchange Auth Code

```python
response = supabase.auth.exchange_code_for_session(
    {"auth_code": "34e770dd-9ff9-416c-87fa-43b31d7ef225"}
)
```
---

## --- Overview ---

## Examples
---

## --- Overview ---

## Examples

### Create server-side auth client

```python
from supabase import create_client
from supabase.lib.client_options import ClientOptions

supabase = create_client(
    supabase_url,
    service_role_key,
    options=ClientOptions(
        auto_refresh_token=False,
        persist_session=False,
    )
)

# Access auth admin api
admin_auth_client = supabase.auth.admin
```
---

## --- generate_link() ---

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

## --- update_user_by_id() ---

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
---

## --- Overview ---

Realtime in Python only works with the asynchronous client.
You can initialize a new Supabase client using the `acreate_client()` method.

- Some Realtime methods are asynchronous and must be awaited. Ensure these methods are called within an `async` function.
- In the following Realtime examples, certain methods are awaited. These should be enclosed within an `async` function.
- When an asynchronous method needs to be used within a synchronous context, such as the callback for `.subscribe()`, utilize `asyncio.create_task()` to schedule the coroutine. This is why the `acreate_client` example includes an import of `asyncio`.


## Examples

### acreate_client()

```python
import os
import asyncio
from supabase import acreate_client, AsyncClient

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

async def create_supabase():
  supabase: AsyncClient = await acreate_client(url, key)
  return supabase
```