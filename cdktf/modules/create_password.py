from constructs import Construct
from cdktf import TerraformProvider
from cdktf_cdktf_provider_random.password import Password


def create_password(scope: Construct, id: str, provider: TerraformProvider):
    
    password = Password(scope, f"{id}-password",
        length=16,
        special=True,
        override_special="_%@",
        provider=provider
    )
    return password