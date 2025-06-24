# Consolidated Documentation: Client Setup

This file merges 1 sections.

---

## --- You can initialize a new Supabase client using the `create_client()` method. ---

The Supabase client is your entrypoint to the rest of the Supabase functionality
and is the easiest way to interact with everything we offer within the Supabase ecosystem.


## Examples

### create_client()

```python
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
```


### With timeout option

```python
import os
from supabase import create_client, Client
from supabase.client import ClientOptions

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(
    url,
    key,
    options=ClientOptions(
        postgrest_client_timeout=10,
        storage_client_timeout=10,
        schema="public",
    )
)
```