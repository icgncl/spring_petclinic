from constructs import Construct
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_role_policy_attachment import IamRolePolicyAttachment
import json

def create_iam_role(scope: Construct, id: str, tfvars: dict, role_name: str, policy_principal: str, policy_arns: list[str]):
    assume_role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": policy_principal  # Interpolate here correctly
            },
            "Action": "sts:AssumeRole"
        }]
    }

    # Create the IAM role with the properly formatted assume role policy
    role = IamRole(scope, f"{id}-{role_name}-role",
        name=f"{tfvars['name']}-{tfvars['environment']}-{role_name}",
        assume_role_policy=json.dumps(assume_role_policy))  # Pass the policy directly
    

    for i, policy_arn in enumerate(policy_arns):
        IamRolePolicyAttachment(scope, f"{id}-{role_name}-role-attach-{i}",
            role=role.name,
            policy_arn=policy_arn)
        
    return role