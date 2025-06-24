# Consolidated Documentation: Storage

This file is a consolidation of 17 smaller documents from the 'Storage' category.



---

## --- Merged from: create_bucket.md ---

# create_bucket()

Creates a new Storage bucket


## Examples

### Create bucket

```python
response = (
    supabase.storage
    .create_bucket(
        "avatars",
        options={
            "public": False,
            "allowed_mime_types": ["image/png"],
            "file_size_limit": 1024,
        }
    )
)
```

---

## --- Merged from: delete_bucket.md ---

# delete_bucket()

Deletes an existing bucket. A bucket can't be deleted with existing objects inside it. You must first `empty()` the bucket.


## Examples

### Delete bucket

```python
response = supabase.storage.delete_bucket("avatars")
```

---

## --- Merged from: empty_bucket.md ---

# empty_bucket()

Removes all objects inside a single bucket.


## Examples

### Empty bucket

```python
response = supabase.storage.empty_bucket("avatars")
```

---

## --- Merged from: from_copy.md ---

# from_.copy()

Copies an existing file to a new path in the same bucket.

## Examples

### Copy file

```python
response = (
    supabase.storage
    .from_("avatars")
    .copy(
        "public/avatar1.png",
        "private/avatar2.png"
    )
)
```

---

## --- Merged from: from_create_signed_upload_url.md ---

# from_.create_signed_upload_url()

Creates a signed upload URL. Signed upload URLs can be used to upload files to the bucket without further authentication. They are valid for 2 hours.

## Examples

### Create Signed URL

```python
response = (
    supabase.storage
    .from_("avatars")
    .create_signed_upload_url("folder/avatar1.png")
)
```

---

## --- Merged from: from_create_signed_url.md ---

# from_.create_signed_url()

Creates a signed URL for a file. Use a signed URL to share a file for a fixed amount of time.

## Examples

### Create Signed URL

```python
response = (
    supabase.storage
    .from_("avatars")
    .create_signed_url(
        "folder/avatar1.png",
        60
    )
)
```


### Create a signed URL for an asset with transformations

```python
response = (
    supabase.storage
    .from_("avatars")
    .create_signed_url(
        "folder/avatar1.png",
        60,
        {"transform": {"width": 100, "height": 100}}
    )
)
```


### Create a signed URL which triggers the download of the asset

```python
response = (
    supabase.storage
    .from_("avatars")
    .create_signed_url(
        "folder/avatar1.png",
        60,
        {"download": True}
    )
)
```

---

## --- Merged from: from_create_signed_urls.md ---

# from_.create_signed_urls()

Creates multiple signed URLs. Use a signed URL to share a file for a fixed amount of time.

## Examples

### Create Signed URLs

```python
response = (
    supabase.storage
    .from_("avatars")
    .create_signed_urls(
        ["folder/avatar1.png", "folder/avatar2.png"],
        60
    )
)
```

---

## --- Merged from: from_download.md ---

# from_.download()

Downloads a file from a private bucket. For public buckets, make a request to the URL returned from `get_public_url` instead.

## Examples

### Download file

```python
with open("./myfolder/avatar1.png", "wb+") as f:
    response = (
        supabase.storage
        .from_("avatars")
        .download("folder/avatar1.png")
    )
    f.write(response)
```


### Download file with transformations

```python
with open("./myfolder/avatar1.png", "wb+") as f:
    response = (
        supabase.storage
        .from_("avatars")
        .download(
            "folder/avatar1.png",
            {"transform": {"width": 100, "height": 100, "quality": 80}},
        )
    )
    f.write(response)
```

---

## --- Merged from: from_get_public_url.md ---

# from_.get_public_url()

A simple convenience function to get the URL for an asset in a public bucket. If you do not want to use this function, you can construct the public URL by concatenating the bucket URL with the path to the asset. This function does not verify if the bucket is public. If a public URL is created for a bucket which is not public, you will not be able to download the asset.


## Examples

### Returns the URL for an asset in a public bucket

```python
response = (
    supabase.storage
    .from_("avatars")
    .get_public_url("folder/avatar1.jpg")
)
```


### Returns the URL for an asset in a public bucket with transformations

```python
response = (
    supabase.storage
    .from_("avatars")
    .get_public_url(
        "folder/avatar1.jpg",
        {"transform": {"width": 100, "height": 100}}
    )
)
```


### Returns the URL which triggers the download of an asset in a public bucket

```python
response = (
    supabase.storage
    .from_("avatars")
    .get_public_url(
        "folder/avatar1.jpg",
        {"download": True}
    )
)
```

---

## --- Merged from: from_list.md ---

# from_.list()

Lists all the files within a bucket.

## Examples

### List files in a bucket

```python
response = (
    supabase.storage
    .from_("avatars")
    .list(
        "folder",
        {
            "limit": 100,
            "offset": 0,
            "sortBy": {"column": "name", "order": "desc"},
        }
    )
)
```


### Search files in a bucket

```python
response = (
    supabase.storage
    .from_("avatars")
    .list(
        "folder",
        {
            "limit": 100,
            "offset": 0,
            "sortBy": {"column": "name", "order": "desc"},
            "search": "jon",
        }
    )
)
```

---

## --- Merged from: from_move.md ---

# from_.move()

Moves an existing file to a new path in the same bucket.

## Examples

### Move file

```python
response = (
    supabase.storage
    .from_("avatars")
    .move(
        "public/avatar1.png",
        "private/avatar2.png"
    )
)
```

---

## --- Merged from: from_remove.md ---

# from_.remove()

Deletes files within the same bucket

## Examples

### Delete file

```python
response = (
    supabase.storage
    .from_("avatars")
    .remove(["folder/avatar1.png"])
)
```

---

## --- Merged from: from_upload.md ---

# from_.upload()

Uploads a file to an existing bucket.

## Examples

### Upload file using filepath

```python
with open("./public/avatar1.png", "rb") as f:
    response = (
        supabase.storage
        .from_("avatars")
        .upload(
            file=f,
            path="public/avatar1.png",
            file_options={"cache-control": "3600", "upsert": "false"}
        )
    )
```

---

## --- Merged from: from_upload_to_signed_url.md ---

# from_.upload_to_signed_url()

Upload a file with a token generated from `create_signed_upload_url`.

## Examples

### Create Signed URL

```python
with open("./public/avatar1.png", "rb") as f:
    response = (
        supabase.storage
        .from_("avatars")
        .upload_to_signed_url(
            path="folder/cat.jpg",
            token="token-from-create_signed_upload_url",
            file=f,
        )
    )
```

---

## --- Merged from: get_bucket.md ---

# get_bucket()

Retrieves the details of an existing Storage bucket.


## Examples

### Get bucket

```python
response = supabase.storage.get_bucket("avatars")
```

---

## --- Merged from: list_buckets.md ---

# list_buckets()

Retrieves the details of all Storage buckets within an existing project.


## Examples

### List buckets

```python
response = supabase.storage.list_buckets()
```

---

## --- Merged from: update_bucket.md ---

# update_bucket()

Updates a Storage bucket


## Examples

### Update bucket

```python
response = (
    supabase.storage
    .update_bucket(
        "avatars",
        options={
            "public": False,
            "allowed_mime_types": ["image/png"],
            "file_size_limit": 1024,
        }
    )
)
```