
import boto3
import os
import sys

# Get config from env (or hardcode based on .env for testing)
endpoint = os.environ.get("R2_ENDPOINT", "https://9a78c994885c508464474e842a2934a8.r2.cloudflarestorage.com")
key_id = os.environ.get("R2_ACCESS_KEY_ID")
secret = os.environ.get("R2_SECRET_ACCESS_KEY")
bucket_name = os.environ.get("R2_BUCKET_NAME", "rawdrive")

print(f"Connecting to R2...")
print(f"Endpoint: {endpoint}")
print(f"Bucket: {bucket_name}")
print(f"Access Key: {key_id[:5]}...")

try:
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
    )
    
    print("Listing buckets...")
    response = s3.list_buckets()
    print("Buckets found:")
    for bucket in response.get("Buckets", []):
        print(f" - {bucket['Name']}")
        
    print(f"\nChecking specific bucket '{bucket_name}'...")
    # Just check if we can list objects in rawdrive
    objs = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
    print(f"Objects in {bucket_name}:")
    if 'Contents' in objs:
        for obj in objs['Contents']:
            print(f" - {obj['Key']}")
    else:
        print(" - (Empty or no access)")

    print("\nSUCCESS: R2 Connection Verified")

except Exception as e:
    print(f"\nFAILURE: {e}")
    sys.exit(1)
