from google.cloud import storage

def upload_to_gcs(bucket_name, source_file_path, destination_blob_name, credentials_file):
    # Initialize the Google Cloud Storage client with the credentials
    storage_client = storage.Client.from_service_account_json(credentials_file)

    # Get the target bucket
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)

    print(f"File {source_file_path} uploaded to gs://{bucket_name}/{destination_blob_name}")

if __name__ == "__main__":
    # Replace the following variables with your specific values
    BUCKET_NAME = "cdn.emacsvi.com"
    SOURCE_FILE_PATH = "/Users/liwei/Desktop/py/newsau/newsau/images/full/4f3453be9b091a00f5180495e295239f63d2a76b.jpg"
    DESTINATION_BLOB_NAME = "test.jpg"
    CREDENTIALS_FILE = "/emacsvi.json"

    upload_to_gcs(BUCKET_NAME, SOURCE_FILE_PATH, DESTINATION_BLOB_NAME, CREDENTIALS_FILE)