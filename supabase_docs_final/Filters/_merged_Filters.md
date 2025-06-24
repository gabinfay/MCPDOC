# Consolidated Documentation: Filters

This file merges 15 sections.

---

## --- eq() ---

Match only rows where `column` is equal to `value`.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .eq("name", "Earth")
    .execute()
)
```
---

## --- neq() ---

Match only rows where `column` is not equal to `value`.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .neq("name", "Earth")
    .execute()
)
```
---

## --- gt() ---

Match only rows where `column` is greather than `value`.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .gt("id", 2)
    .execute()
)
```
---

## --- gte() ---

Match only rows where `column` is greater than or equal to `value`.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .gte("id", 2)
    .execute()
)
```
---

## --- lt() ---

Match only rows where `column` is less than `value`.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .lt("id", 2)
    .execute()
)
```
---

## --- lte() ---

Match only rows where `column` is less than or equal to `value`.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .lte("id", 2)
    .execute()
)
```
---

## --- like() ---

Match only rows where `column` matches `pattern` case-sensitively.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .like("name", "%Ea%")
    .execute()
)
```
---

## --- ilike() ---

Match only rows where `column` matches `pattern` case-insensitively.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .ilike("name", "%ea%")
    .execute()
)
```
---

## --- is_() ---

Match only rows where `column` IS `value`.


## Examples

### Checking for nullness, True or False

```python
response = (
    supabase.table("planets")
    .select("*")
    .is_("name", "null")
    .execute()
)
```
---

## --- in_() ---

Match only rows where `column` is included in the `values` array.


## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .in_("name", ["Earth", "Mars"])
    .execute()
)
```
---

## --- range_gt() ---

Only relevant for range columns. Match only rows where every element in `column` is greater than any element in `range`.


## Examples

### With `select()`

```python
response = (
    supabase.table("reservations")
    .select("*")
    .range_gt("during", ["2000-01-02 08:00", "2000-01-02 09:00"])
    .execute()
)
```
---

## --- range_gte() ---

Only relevant for range columns. Match only rows where every element in `column` is either contained in `range` or greater than any element in `range`.


## Examples

### With `select()`

```python
response = (
    supabase.table("reservations")
    .select("*")
    .range_gte("during", ["2000-01-02 08:30", "2000-01-02 09:30"])
    .execute()
)
```
---

## --- range_lt() ---

Only relevant for range columns. Match only rows where every element in `column` is less than any element in `range`.


## Examples

### With `select()`

```python
response = (
    supabase.table("reservations")
    .select("*")
    .range_lt("during", ["2000-01-01 15:00", "2000-01-01 16:00"])
    .execute()
)
```
---

## --- range_lte() ---

Only relevant for range columns. Match only rows where every element in `column` is less than any element in `range`.


## Examples

### With `select()`

```python
response = (
    supabase.table("reservations")
    .select("*")
    .range_lte("during", ["2000-01-01 14:00", "2000-01-01 16:00"])
    .execute()
)
```
---

## --- filter() ---

## Examples

### With `select()`

```python
response = (
    supabase.table("planets")
    .select("*")
    .filter("name", "in", '("Mars","Tatooine")')
    .execute()
)
```


### On a foreign table

```python
response = (
    supabase.table("orchestral_sections")
    .select("name, instruments!inner(name)")
    .filter("instruments.name", "eq", "flute")
    .execute()
)
```