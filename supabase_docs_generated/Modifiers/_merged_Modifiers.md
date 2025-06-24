# Consolidated Documentation: Modifiers

This file is a consolidation of 8 smaller documents from the 'Modifiers' category.



---

## --- Merged from: Using_Explain.md ---

# Using Explain

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

## --- Merged from: Using_Modifiers.md ---

# Using Modifiers

Filters work on the row level—they allow you to return rows that
only match certain conditions without changing the shape of the rows.
Modifiers are everything that don't fit that definition—allowing you to
change the format of the response (e.g., returning a CSV string).

Modifiers must be specified after filters. Some modifiers only apply for
queries that return rows (e.g., `select()` or `rpc()` on a function that
returns a table response).


## Examples

---

## --- Merged from: csv.md ---

# csv()

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

---

## --- Merged from: limit.md ---

# limit()

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

## --- Merged from: maybe_single.md ---

# maybe_single()

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

## --- Merged from: order.md ---

# order()

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

## --- Merged from: range.md ---

# range()

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

## --- Merged from: single.md ---

# single()

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