# app/services/s3_storage.py
import boto3
import orjson
import gzip
from botocore.exceptions import ClientError
from fastapi.responses import StreamingResponse
from app.config import settings

# Initialize S3 Client once
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION
)

def upload_telemetry_to_s3(data: dict, year: int, round_num: int, frame_skip: int):
    """
    Compresses data and uploads to S3.
    Key format: telemetry/2023/5/skip_1.json.gz
    """
    key = f"telemetry/{year}/{round_num}/skip_{frame_skip}.json.gz"
    
    # 1. Serialize and Compress in memory
    json_bytes = orjson.dumps(data, option=orjson.OPT_SERIALIZE_NUMPY)
    compressed_data = gzip.compress(json_bytes, compresslevel=6)
    
    # 2. Upload to S3
    try:
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=compressed_data,
            ContentType='application/json',
            ContentEncoding='gzip'  # Important: Tells browser it's gzipped
            
        )
        return True
    except ClientError as e:
        print(f"S3 Upload Error: {e}")
        return False

def get_stream_from_s3(year: int, round_num: int, frame_skip: int):
    """
    Returns a StreamingResponse if file exists, else None.
    """
    key = f"telemetry/{year}/{round_num}/skip_{frame_skip}.json.gz"
    
    try:
        # Get the object stream from S3 (does not download the whole file)
        response = s3_client.get_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        
        # Generator to yield chunks of data
        def stream_generator():
            for chunk in response['Body'].iter_chunks(chunk_size=8192):
                yield chunk

        # Return the stream directly
        return StreamingResponse(
            stream_generator(),
            media_type="application/json",
            headers={"Content-Encoding": "gzip"} # Browser will auto-decompress
        )
    except ClientError as e:
        # 404 Not Found or other S3 errors
        return None