# Consolidated Documentation: Database Operations

This file merges 7 sections.

---

## --- Fetch data: select() ---

## Examples

### Getting your data

```python
response = (
    supabase.table("planets")
    .select("*")
    .execute()
)
```


### Selecting specific columns

```python
response = (
    supabase.table("planets")
    .select("name")
    .execute()
)
```


### Query referenced tables

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments(name)")
    .execute()
)
```


### Query referenced tables through a join table

```python
response = (
    supabase.table("users")
    .select("name, teams(name)")
    .execute()
)
```


### Query the same referenced table multiple times

```python
response = (
    supabase.table("messages")
    .select("content,from:sender_id(name),to:receiver_id(name)")
    .execute()
)
```


### Filtering through referenced tables

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments(*)")
    .eq("instruments.name", "guqin")
    .execute()
)
```


### Querying referenced table with count

```python
response = (
    supabase.table("orchestral_sections")
    .select("*, instruments(count)")
    .execute()
)
```


### Querying with count option

```python
response = (
    supabase.table("planets")
    .select("*", count="exact")
    .execute()
)
```


### Querying JSON data

```python
response = (
    supabase.table("users")
    .select("id, name, address->city")
    .execute()
)
```


### Querying referenced table with inner join

```python
response = (
    supabase.table("instruments")
    .select("name, orchestral_sections!inner(name)")
    .eq("orchestral_sections.name", "woodwinds")
    .execute()
)
```


### Switching schemas per query

```python
response = (
    supabase.schema("myschema")
    .table("mytable")
    .select("*")
    .execute()
)
```
---

## --- Create data: insert() ---

## Examples

### Create a record

```python
response = (
    supabase.table("planets")
    .insert({"id": 1, "name": "Pluto"})
    .execute()
)
```


### Bulk create

```python
try:
    response = (
        supabase.table("characters")
        .insert([
            {"id": 1, "name": "Frodo"},
            {"id": 2, "name": "Sam"},
        ])
        .execute()
    )
    return response
except Exception as exception:
    return exception
```
---

## --- Modify data: update() ---

## Examples

### Updating your data

```python
response = (
    supabase.table("instruments")
    .update({"name": "piano"})
    .eq("id", 1)
    .execute()
)
```


### Updating JSON data

```python
response = (
    supabase.table("users")
    .update({"address": {"street": "Melrose Place", "postcode": 90210}})
    .eq("address->postcode", 90210)
    .execute()
)
```
---

## --- Upsert data: upsert() ---

## Examples

### Upsert your data

```python
response = (
    supabase.table("instruments")
    .upsert({"id": 1, "name": "piano"})
    .execute()
)
```


### Bulk Upsert your data

```python
response = (
    supabase.table("instruments")
    .upsert([{"id": 1, "name": "piano"}, {"id": 2, "name": "guitar"}])
    .execute()
)
```


### Upserting into tables with constraints

```python
response = (
    supabase.table("users")
    .upsert(
        {"id": 42, "handle": "saoirse", "display_name": "Saoirse"},
        on_conflict="handle",
    )
    .execute()
)
```
---

## --- Delete data: delete() ---

## Examples

### Delete records

```python
response = (
    supabase.table("countries")
    .delete()
    .eq("id", 1)
    .execute()
)
```


### Delete multiple records

```python
response = (
    supabase.table("countries")
    .delete()
    .in_("id", [1, 2, 3])
    .execute()
)
```
---

## --- Postgres functions: rpc() ---

You can call Postgres functions as _Remote Procedure Calls_, logic in your database that you can execute from anywhere.
Functions are useful when the logic rarely changes—like for password resets and updates.

```sql
create or replace function hello_world() returns text as $$
  select 'Hello world';
$$ language sql;
```


## Examples

### Call a Postgres function without arguments

```python
response = (
    supabase.rpc("hello_world")
    .execute()
)
```


### Call a Postgres function with arguments

```python
response = (
    supabase.rpc("echo", { "say": "👋" })
    .execute()
)
```


### Bulk processing

```python
response = (
    supabase.rpc("add_one_each", {"arr": [1, 2, 3]})
    .execute()
)
```


### Call a Postgres function with filters

```python
response = (
    supabase.rpc("list_stored_planets")
    .eq("id", 1)
    .single()
    .execute()
)
```


### Call a read-only Postgres function

```python
response = (
    supabase.rpc("hello_world", get=True)
    .execute()
)
```
---

## --- from_.update() ---

Replaces an existing file at the specified path with a new one.

## Examples

### Update file

```python
with open("./public/avatar1.png", "rb") as f:
    response = (
        supabase.storage
        .from_("avatars")
        .update(
            file=f,
            path="public/avatar1.png",
            file_options={"cache-control": "3600", "upsert": "true"}
        )
    )
```