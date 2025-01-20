import logging
from google.cloud import storage
from google.api_core import exceptions


# TODO: provide feedback that this is not needed
def create_bucket_if_not_exists(bucket_name: str, project: str, location: str) -> None:
    """Creates a new bucket if it doesn't already exist.
    
    Args:
        bucket_name: Name of the bucket to create
        project: Google Cloud project ID
        location: Location to create the bucket in (defaults to us-central1)
    """
    
    storage_client = storage.Client(project=project)
    # Strip 'gs://' prefix if present
    if bucket_name.startswith('gs://'):
        bucket_name = bucket_name[5:]
    try:
        storage_client.get_bucket(bucket_name)
        logging.info(f"Bucket {bucket_name} already exists")
    except exceptions.NotFound:
        bucket = storage_client.create_bucket(
            bucket_name,
            location=location,
            project=project,
        )
        logging.info(f"Created bucket {bucket.name} in {bucket.location}")
