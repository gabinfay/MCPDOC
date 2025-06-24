# Consolidated Documentation: Modifiers

This file merges 6 sections.

---

## --- order() ---

Order the query result by `column`.

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .order("name", desc=True)
    .execute()
)
```


### On a foreign table

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments(name)")
    .order("name", desc=True, foreign_table="instruments")
    .execute()
)
```


### Order parent table by a referenced table

```python
response = (
    supabase.table("instruments")
    .select("name, section:orchestral_sections(name)")
    .order("section(name)", desc=False)
)
```
---

## --- limit() ---

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("name")
    .limit(1)
    .execute()
)
```


### On a foreign table

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments(name)")
    .limit(1, foreign_table="instruments")
    .execute()
)
```
---

## --- range() ---

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("name")
    .range(0, 1)
    .execute()
)
```


### On a foreign table

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments(name)")
    .range(0, 1, foreign_table="instruments")
    .execute()
)
```
---

## --- single() ---

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("name")
    .limit(1)
    .single()
    .execute()
)
```
---

## --- maybe_single() ---

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .eq("name", "Earth")
    .maybe_single()
    .execute()
)
```
---

## --- csv() ---

## Examples

### Return data as CSV

```python
response = (
    supabase.table("planets")
    .select("*")
    .csv()
    .execute()
)
```