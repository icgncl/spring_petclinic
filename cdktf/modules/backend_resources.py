from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable
from cdktf import S3Backend

def create_backend_resources(scope, id, tfvars, branch_name):
    bucket_name = f"{tfvars['name']}-terraform-state"
    table_name = f"{tfvars['name']}-terraform-locks"

    # Backend configuration must use raw strings, NOT token references
    S3Backend(scope,
        bucket=bucket_name,  # not s3_bucket.bucket
        key=f"state/{branch_name}/terraform.tfstate",
        region="eu-west-1",
        encrypt=True,
        dynamodb_table=table_name
    )
