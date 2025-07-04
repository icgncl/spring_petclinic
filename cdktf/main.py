from cdktf import App, TerraformStack
from constructs import Construct
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_random.provider import RandomProvider

from utils.config_loader import load_tfvars
from stacks.global_stack import create_global_resources
from stacks.region_stack import create_region_stack
from modules.backend_resources import create_backend_resources
from modules.create_password import create_password

import os
from cdktf import App

branch_name = os.getenv("BRANCH_NAME", "production")  # default to 'production' if not set

# Use the branch name to build the tfvars path prefix
tfvars_path_prefix = f"variables/{branch_name}"

global_vars = load_tfvars(f"{tfvars_path_prefix}/global.tfvars")
primary_vars = load_tfvars(f"{tfvars_path_prefix}/primary_region.tfvars")
secondary_vars = load_tfvars(f"{tfvars_path_prefix}/secondary_region.tfvars")

class GorillaClinicStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        
        random_provider = RandomProvider(self, "random")
        
        global_vars["db_password"] = create_password(self, "password", provider=random_provider)

        global_vars["primary_region"] = primary_vars["region"]
        global_vars["secondary_region"] = secondary_vars["region"]

        primary_vars.update(global_vars)
        secondary_vars.update(global_vars)
        
        create_backend_resources(self, "backend", primary_vars, branch_name)
        primary_provider = AwsProvider(self, "aws_primary", region=primary_vars["region"], alias="primary")
        secondary_provider = AwsProvider(self, "aws_secondary", region=secondary_vars["region"], alias="secondary")

        # Create shared global resources
        route53_zone, roles = create_global_resources(self, "global", primary_vars)


        # Create region-specific resources
        primary_region = create_region_stack(self, "primary-region",
            primary_vars, True, roles, route53_zone, primary_provider)
        secondary_region = create_region_stack(self, "secondary-region",
            secondary_vars, False, roles, route53_zone, secondary_provider)


app = App()
GorillaClinicStack(app, "gorilla-clinic")
app.synth()