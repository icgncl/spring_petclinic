from constructs import Construct
from cdktf_cdktf_provider_aws.secretsmanager_secret import SecretsmanagerSecret
from cdktf_cdktf_provider_aws.secretsmanager_secret_version import SecretsmanagerSecretVersion
import time

def create_or_get_secret(scope: Construct, id: str, tfvars: dict, provider) -> SecretsmanagerSecret:
    """
    Attempts to use an existing secret with a fixed name.
    If not found, creates it with prevent_destroy and ignore_changes protection.
    """
    secret = SecretsmanagerSecret(scope, id,
        name=f"{tfvars["db_secret_name"]}-{time.time()}",
        provider=provider,
        description="Master password for gorilla-clinic DB"
    )


    SecretsmanagerSecretVersion(scope, f"{id}-version",
        secret_id=secret.id,
        secret_string=tfvars["db_password"],
        provider=provider,
        lifecycle={
            "ignore_changes": ["secret_string"]
        }
    )

    return secret.arn