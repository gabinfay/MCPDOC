# Consolidated Documentation: Utilities

This file is a consolidation of 1 smaller documents from the 'Utilities' category.



---

## --- Merged from: Overview.md ---

# Overview

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