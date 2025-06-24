# Consolidated Documentation: Realtime

This file is a consolidation of 5 smaller documents from the 'Realtime' category.



---

## --- Merged from: broadcastMessage.md ---

# broadcastMessage()

Broadcast a message to all connected clients to a channel.


## Examples

### Send a message via websocket

```python
channel = supabase.channel("room1")

def on_subscribe(status, err):
    if status == RealtimeSubscribeStates.SUBSCRIBED:
        asyncio.create_task(channel.send_broadcast('cursor-pos', {"x": random.random(), "y": random.random()}))

await channel.subscribe(on_subscribe)
```

---

## --- Merged from: getChannels.md ---

# getChannels()

## Examples

### Get all channels

```python
channels = supabase.get_channels()
```

---

## --- Merged from: onsubscribe.md ---

# on().subscribe()

## Examples

### Listen to broadcast messages

```python
channel = supabase.channel("room1")

def on_subscribe(status, err):
    if status == RealtimeSubscribeStates.SUBSCRIBED:
        asyncio.create_task(channel.send_broadcast(
            "cursor-pos",
            {"x": random.random(), "y": random.random()}
        ))

def handle_broadcast(payload):
    print("Cursor position received!", payload)

await channel.on_broadcast(event="cursor-pos", callback=handle_broadcast).subscribe(on_subscribe)
```


### Listen to presence sync

```python
channel = supabase.channel("room1")

def on_subscribe(status, err):
    if status == RealtimeSubscribeStates.SUBSCRIBED:
        asyncio.create_task(channel.track({"online_at": datetime.datetime.now().isoformat()}))

def handle_presence_sync():
    print("Synced presence state: ", channel.presence.state)

await channel.on_presence_sync(callback=handle_presence_sync).subscribe(on_subscribe)
```


### Listen to presence join

```python
channel = supabase.channel("room1")

def handle_presence_join(key, current_presence, new_presence):
    print("Newly joined presences: ", new_presence)

def on_subscribe(status, err):
    if status == RealtimeSubscribeStates.SUBSCRIBED:
        asyncio.create_task(channel.track({"online_at": datetime.datetime.now().isoformat()}))

await channel.on_presence_join(callback=handle_presence_join).subscribe(on_subscribe)
```


### Listen to presence leave

```python
channel = supabase.channel("room1")

def handle_presence_leave(key, current_presence, left_presence):
    print("Newly left presences: ", left_presence)

def on_subscribe(status, err):
    if status == RealtimeSubscribeStates.SUBSCRIBED:
        asyncio.create_task(channel.track({"online_at": datetime.datetime.now().isoformat()}))
        asyncio.create_task(channel.untrack())

await channel.on_presence_leave(callback=handle_presence_leave).subscribe(on_subscribe)
```


### Listen to all database changes

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("*", schema="*", callback=handle_record_updated)
    .subscribe()
)
```


### Listen to a specific table

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("*", schema="public", table="countries", callback=handle_record_updated)
    .subscribe()
)
```


### Listen to inserts

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("INSERT", schema="public", table="countries", callback=handle_record_inserted)
    .subscribe()
)
```


### Listen to updates

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("UPDATE", schema="public", table="countries", callback=handle_record_updated)
    .subscribe()
)
```


### Listen to deletes

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("DELETE", schema="public", table="countries", callback=handle_record_deleted)
    .subscribe()
)
```


### Listen to multiple events

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("INSERT", schema="public", table="countries", callback=handle_record_inserted)
    .on_postgres_changes("DELETE", schema="public", table="countries", callback=handle_record_deleted)
    .subscribe()
)
```


### Listen to row level changes

```python
response = (
    await supabase.channel("room1")
    .on_postgres_changes("UPDATE", schema="public", table="countries", filter="id=eq.200", callback=handle_record_updated)
    .subscribe()
)
```

---

## --- Merged from: removeAllChannels.md ---

# removeAllChannels()

## Examples

### Remove all channels

```python
await supabase.remove_all_channels()
```

---

## --- Merged from: removeChannel.md ---

# removeChannel()

## Examples

### Removes a channel

```python
await supabase.remove_channel(myChannel)
```