"""Setup S3 bucket for code validation system"""
import boto3
import sys

BUCKET_NAME = 'code-validation-hackathon-bucket'
REGION = 'us-east-1'

def create_bucket():
    s3 = boto3.client('s3', region_name=REGION)
    
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"✓ Created bucket: {BUCKET_NAME}")
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=BUCKET_NAME,
            VersioningConfiguration={'Status': 'Enabled'}
        )
        print(f"✓ Enabled versioning")
        
        # Create uploads folder
        s3.put_object(Bucket=BUCKET_NAME, Key='uploads/')
        print(f"✓ Created uploads/ folder")
        
        print(f"\n✓ Setup complete!")
        print(f"\nBucket name: {BUCKET_NAME}")
        print(f"Upload files to: s3://{BUCKET_NAME}/uploads/")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_bucket()
