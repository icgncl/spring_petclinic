from constructs import Construct
from cdktf_cdktf_provider_aws.alb import Alb
from cdktf_cdktf_provider_aws.alb_target_group import AlbTargetGroup
from cdktf_cdktf_provider_aws.alb_listener import AlbListener, AlbListenerDefaultAction
from cdktf_cdktf_provider_aws.alb_listener_rule import (
    AlbListenerRule,
    AlbListenerRuleAction,
    AlbListenerRuleCondition,
)
from cdktf import TerraformProvider


def create_alb(scope: Construct, id: str, tfvars: dict, net: dict, sg: dict, provider: TerraformProvider):
    alb = Alb(scope, f"{id}-alb",
        provider=provider,
        name=f"{tfvars['name']}-alb",
        internal=False,
        load_balancer_type="application",
        subnets=[s.id for s in net["public_subnets"]],
        security_groups=[sg["alb_sg"].id]
    )

    blue_tg = AlbTargetGroup(scope, f"{id}-blue-lb-tg",
        provider=provider,
        name=f"{tfvars['name']}-blue-tg",
        port=tfvars["container_port"],
        protocol="HTTP",
        vpc_id=net["vpc_id"],
        target_type="ip",
        health_check={"path": tfvars["health_check_path"], "protocol": "HTTP"}
    )

    green_tg = AlbTargetGroup(scope, f"{id}-green-lb-tg",
        provider=provider,
        name=f"{tfvars['name']}-green-tg",
        port=tfvars["container_port"],
        protocol="HTTP",
        vpc_id=net["vpc_id"],
        target_type="ip",
        health_check={"path": tfvars["health_check_path"], "protocol": "HTTP"}
    )

    alb_listener = AlbListener(scope, f"{id}-listener",
        provider=provider,
        load_balancer_arn=alb.arn,
        port=tfvars["alb_listener_port"],
        protocol="HTTP",
        default_action=[AlbListenerDefaultAction(type="forward", target_group_arn=blue_tg.arn)],
        lifecycle={"create_before_destroy": True}
    )

    alb_test_listener = AlbListener(scope, f"{id}-listener-test",
        provider=provider,
        load_balancer_arn=alb.arn,
        port=tfvars["alb_test_listener_port"],
        protocol="HTTP",
        default_action=[AlbListenerDefaultAction(type="forward", target_group_arn=green_tg.arn)],
        lifecycle={"create_before_destroy": True}
    )

    return {
        "alb_listener": alb_listener,
        "alb_test_listener": alb_test_listener,
        "alb_dns_name": alb.dns_name,
        "blue_target_group_arn": blue_tg.arn,
        "blue_target_group_name": blue_tg.name,
        "green_target_group_arn": green_tg.arn,
        "green_target_group_name": green_tg.name
    }
