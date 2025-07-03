from constructs import Construct
from cdktf_cdktf_provider_aws.iam_role import IamRole
from cdktf_cdktf_provider_aws.iam_role_policy_attachment import IamRolePolicyAttachment
from modules.iam_role import create_iam_role
from modules.dns import create_dns_zone


def create_global_resources(scope: Construct, id: str, tfvars: dict):
    ecs_policy_arns = [
        "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
        "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
        "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
    ]
    ecs_role = create_iam_role(scope, id, tfvars, "ecsTaskExecutionRole", "ecs-tasks.amazonaws.com", ecs_policy_arns)

    # CodeDeploy Role
    cd_policy_arns = [
        "arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS"
    ]
    cd_role = create_iam_role(scope, id, tfvars, "codeDeployRole", "codedeploy.amazonaws.com", cd_policy_arns)

    # Route53 Zone
    zone = create_dns_zone(scope, id, tfvars)

    return zone, {
        "ecs_task_execution_role": ecs_role,
        "codedeploy_role": cd_role
    }