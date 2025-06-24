# Consolidated Documentation: Filters

This file is a consolidation of 24 smaller documents from the 'Filters' category.



---

## --- Merged from: Using_Filters.md ---

# Using Filters

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

## --- Merged from: contained_by.md ---

# contained_by()

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

## --- Merged from: contains.md ---

# contains()

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

## --- Merged from: eq.md ---

# eq()

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

## --- Merged from: filter.md ---

# filter()

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

---

## --- Merged from: gt.md ---

# gt()

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

## --- Merged from: gte.md ---

# gte()

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

## --- Merged from: ilike.md ---

# ilike()

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

## --- Merged from: in.md ---

# in_()

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

## --- Merged from: is.md ---

# is_()

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

## --- Merged from: like.md ---

# like()

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

## --- Merged from: lt.md ---

# lt()

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

## --- Merged from: lte.md ---

# lte()

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

## --- Merged from: match.md ---

# match()

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

## --- Merged from: neq.md ---

# neq()

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

## --- Merged from: not.md ---

# not_()

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

## --- Merged from: or.md ---

# or_()

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

## --- Merged from: overlaps.md ---

# overlaps()

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

## --- Merged from: range_adjacent.md ---

# range_adjacent()

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

## --- Merged from: range_gt.md ---

# range_gt()

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

## --- Merged from: range_gte.md ---

# range_gte()

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

## --- Merged from: range_lt.md ---

# range_lt()

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

## --- Merged from: range_lte.md ---

# range_lte()

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

## --- Merged from: text_search.md ---

# text_search()

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