# Consolidated Documentation: Edge Functions

This file merges 1 sections.

---

## --- invoke() ---

Invoke a Supabase Function.


## Examples

### Basic invocation

```python
response = supabase.functions.invoke(
    "hello-world",
    invoke_options={
        "body": {"name": "Functions"},
    },
)
```


### Error handling

```python
from supafunc.errors import FunctionsRelayError, FunctionsHttpError

try:
    response = supabase.functions.invoke(
        "hello-world",
        invoke_options={
            "body": {"foo": "bar"},
            "headers": {"my-custom-header": "my-custom-header-value"},
        },
    )
except FunctionsHttpError as exception:
    err = exception.to_dict()
    print(f'Function returned an error {err.get("message")}')
except FunctionsRelayError as exception:
    err = exception.to_dict()
    print(f'Relay error: {err.get("message")}')
```


### Passing custom headers

```python
response = supabase.functions.invoke(
    "hello-world",
    invoke_options={
        "headers": {
            "my-custom-header": "my-custom-header-value",
        },
        "body": {"foo": "bar"},
    },
)
```