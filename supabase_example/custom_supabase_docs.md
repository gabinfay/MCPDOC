# Custom Supabase Documentation

# Authentication

## sign_up()
```python response = supabase.auth.sign_up( { "email": "email@example.com", "password": "password", } ) ```

**Examples:** 5 available
**Reference:** Line 1351

## sign_in_anonymously()
```python response = supabase.auth.sign_in_anonymously( {"options": {"captcha_token": ""}} ) ```

**Examples:** 2 available
**Reference:** Line 1424

## sign_in_with_password
```python response = supabase.auth.sign_in_with_password( { "email": "email@example.com", "password": "example-password", } ) ```

**Examples:** 2 available
**Reference:** Line 1450

## sign_in_with_id_token
```python response = supabase.auth.sign_in_with_id_token( { "provider": "google", "token": "your-id-token", } ) ```

**Examples:** 1 available
**Reference:** Line 1482

## sign_in_with_otp
```python response = supabase.auth.sign_in_with_otp( { "email": "email@example.com", "options": { "email_redirect_to": "https://example.com/welcome", }, } ) ```

**Examples:** 3 available
**Reference:** Line 1502

## sign_in_with_oauth
```python response = supabase.auth.sign_in_with_oauth( {"provider": "github"} ) ```

**Examples:** 3 available
**Reference:** Line 1547

## sign_in_with_sso()
```python response = supabase.auth.sign_in_with_sso( {"domain": "company.com"} ) ```

**Examples:** 2 available
**Reference:** Line 1592

## sign_out()
```python response = supabase.auth.sign_out() ```

**Examples:** 1 available
**Reference:** Line 1618

## reset_password_for_email()
```python supabase.auth.reset_password_for_email( email, { "redirect_to": "https://example.com/update-password", } ) ```

**Examples:** 1 available
**Reference:** Line 1633

## verify_otp
```python response = supabase.auth.verify_otp( { "email": "email@example.com", "token": "123456", "type": "email", } ) ```

**Examples:** 3 available
**Reference:** Line 1653

## get_session
```python response = supabase.auth.get_session() ```

**Examples:** 1 available
**Reference:** Line 1700

## refresh_session()
Returns a new session, regardless of expiry status. Takes in an optional refresh token. If not passed in, then refresh_session() will attempt to retrieve it from get_session(). If the current session's refresh token is invalid, an error will be thrown.

**Examples:** 1 available
**Reference:** Line 1715

## get_user
``` response = supabase.auth.get_user() ```

**Examples:** 2 available
**Reference:** Line 1733

## update_user()
```python response = supabase.auth.update_user( {"email": "new@email.com"} ) ```

**Examples:** 5 available
**Reference:** Line 1755

## get_user_identities()
```python response = supabase.auth.get_user_identities() ```

**Examples:** 1 available
**Reference:** Line 1813

## link_identity()
```python response = supabase.auth.link_identity( {provider: "github"} ) ```

**Examples:** 1 available
**Reference:** Line 1828

## unlink_identity()
```python

**Examples:** 1 available
**Reference:** Line 1845

## reauthenticate()
```python response = supabase.auth.reauthenticate() ```

**Examples:** 1 available
**Reference:** Line 1869

## resend()
```python response = supabase.auth.resend( { "type": "signup", "email": "email@example.com", "options": { "email_redirect_to": "https://example.com/welcome", }, } ) ```

**Examples:** 4 available
**Reference:** Line 1884

## set_session()
Sets the session data from the current session. If the current session is expired, setSession will take care of refreshing it to obtain a new session. If the refresh token or access token in the current session is invalid, an error will be thrown.

**Examples:** 1 available
**Reference:** Line 1943

## exchange_code_for_session()
```python response = supabase.auth.exchange_code_for_session( {"auth_code": "34e770dd-9ff9-416c-87fa-43b31d7ef225"} ) ```

**Examples:** 1 available
**Reference:** Line 1960

## get_user_by_id()
```python response = supabase.auth.admin.get_user_by_id(1) ```

**Examples:** 1 available
**Reference:** Line 2125

## update_user_by_id()
```python response = supabase.auth.admin.update_user_by_id( "11111111-1111-1111-1111-111111111111", { "email": "new@email.com", } ) ```

**Examples:** 6 available
**Reference:** Line 2322

# Storage

## create_bucket()
Creates a new Storage bucket

**Examples:** 1 available
**Reference:** Line 2731

## get_bucket()
Retrieves the details of an existing Storage bucket.

**Examples:** 1 available
**Reference:** Line 2757

## list_buckets()
Retrieves the details of all Storage buckets within an existing project.

**Examples:** 1 available
**Reference:** Line 2773

## update_bucket()
Updates a Storage bucket

**Examples:** 1 available
**Reference:** Line 2789

## delete_bucket()
Deletes an existing bucket. A bucket can't be deleted with existing objects inside it. You must first `empty()` the bucket.

**Examples:** 1 available
**Reference:** Line 2815

## empty_bucket()
Removes all objects inside a single bucket.

**Examples:** 1 available
**Reference:** Line 2831

## from_.upload()
Uploads a file to an existing bucket.

**Examples:** 1 available
**Reference:** Line 2847

## from_.download()
Downloads a file from a private bucket. For public buckets, make a request to the URL returned from `get_public_url` instead.

**Examples:** 2 available
**Reference:** Line 2871

## from_.list()
Lists all the files within a bucket.

**Examples:** 2 available
**Reference:** Line 2908

## from_.move()
Moves an existing file to a new path in the same bucket.

**Examples:** 1 available
**Reference:** Line 2977

## from_.copy()
Copies an existing file to a new path in the same bucket.

**Examples:** 1 available
**Reference:** Line 2999

## from_.remove()
Deletes files within the same bucket

**Examples:** 1 available
**Reference:** Line 3021

## from_.create_signed_url()
Creates a signed URL for a file. Use a signed URL to share a file for a fixed amount of time.

**Examples:** 3 available
**Reference:** Line 3040

## from_.create_signed_urls()
Creates multiple signed URLs. Use a signed URL to share a file for a fixed amount of time.

**Examples:** 1 available
**Reference:** Line 3092

## from_.create_signed_upload_url()
Creates a signed upload URL. Signed upload URLs can be used to upload files to the bucket without further authentication. They are valid for 2 hours.

**Examples:** 1 available
**Reference:** Line 3114

## from_.upload_to_signed_url()
Upload a file with a token generated from `create_signed_upload_url`.

**Examples:** 1 available
**Reference:** Line 3133

## from_.get_public_url()
A simple convenience function to get the URL for an asset in a public bucket. If you do not want to use this function, you can construct the public URL by concatenating the bucket URL with the path to the asset. This function does not verify if the bucket is public. If a public URL is created for a bucket which is not public, you will not be able to download the asset.

**Examples:** 3 available
**Reference:** Line 3157

