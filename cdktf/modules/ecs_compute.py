from constructs import Construct
from cdktf_cdktf_provider_aws import (
    ecs_cluster, ecs_task_definition, ecs_service,
    ecr_repository, ecr_lifecycle_policy,
    cloudwatch_log_group,
    codedeploy_app,
    appautoscaling_target, appautoscaling_policy,
    ecs_service as ecs_service_mod
)
from cdktf import Fn, TerraformProvider, TerraformResourceLifecycle
from cdktf_cdktf_provider_aws.codedeploy_deployment_group import (
    CodedeployDeploymentGroup,
    CodedeployDeploymentGroupLoadBalancerInfoTargetGroupPairInfoTargetGroup,
    CodedeployDeploymentGroupLoadBalancerInfoTargetGroupPairInfo,
    CodedeployDeploymentGroupLoadBalancerInfo,
)


def create_compute(scope: Construct, id: str, tfvars: dict, net: dict, sg: dict, alb_info: dict,
                   shared_roles:dict, provider: TerraformProvider, is_primary:bool, db_info: dict = None):
    
    cluster = ecs_cluster.EcsCluster(scope, f"{id}-cluster", provider=provider, name=f"{tfvars['name']}-cluster",
        setting = [
            ecs_cluster.EcsClusterSetting(
                name="containerInsights",
                value="enabled"
            )
        ]   
    )

    ecs_role = shared_roles["ecs_task_execution_role"]
    codedeploy_role = shared_roles["codedeploy_role"]

    repo = ecr_repository.EcrRepository(scope, f"{id}-repo", 
            name=f"{tfvars['name']}-ecr", 
            provider=provider, 
            force_delete=True)
    if tfvars["ecr_lifecycle_policy_enabled"]:
        ecr_lifecycle_policy.EcrLifecyclePolicy(scope, f"{id}-policy",
            provider=provider,
            repository=repo.name,
            policy=tfvars["ecr_lifecycle_policy_rules"])

    log_group = cloudwatch_log_group.CloudwatchLogGroup(scope, f"{id}-logs",
        provider=provider,
        name=f"/ecs/{tfvars['name']}",
        retention_in_days=7)

    environment = []
    secrets = []

    if db_info and is_primary:
        environment = [
            {"name": "SPRING_DATASOURCE_URL", 
                "value": f"jdbc:postgresql://{db_info['db_endpoint']}:{db_info['db_port']}/{db_info['db_name']}"},
            {"name": "SPRING_DATASOURCE_USERNAME", "value": db_info["db_username"]},
            {"name": "SPRING_PROFILES_ACTIVE", "value": "postgres"},
        ]
        secrets = [{"name": "SPRING_DATASOURCE_PASSWORD", "valueFrom": db_info["db_password_arn"]}]


    task = ecs_task_definition.EcsTaskDefinition(scope, f"{id}-task",
        provider=provider,
        family=f"{tfvars['name']}-task",
        requires_compatibilities=["FARGATE"],
        cpu=str(tfvars["cpu"]),
        memory=str(tfvars["memory"]),
        network_mode="awsvpc",
        execution_role_arn=ecs_role.arn,
        container_definitions=Fn.jsonencode([{
            "name": "app",
            "image": f"{repo.repository_url}:latest",
            "portMappings": [{"containerPort": tfvars["container_port"]}],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": f"/ecs/{tfvars['name']}",
                    "awslogs-region": tfvars["region"],
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "environment": environment,
            "secrets": secrets,
            "healthCheck": {
                "command": ["CMD-SHELL", f"curl -f http://localhost:{tfvars['container_port']}{tfvars['health_check_path']} || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }]),
        depends_on=[repo, log_group]
    )

    service = ecs_service.EcsService(scope, f"{id}-svc",
        provider=provider,
        name=f"{tfvars['name']}-svc",
        cluster=cluster.id,
        task_definition=task.arn,
        launch_type="FARGATE",
        network_configuration={
            "subnets": [s.id for s in net["private_subnets"]],
            "security_groups": [sg["ecs_sg"].id],
            "assign_public_ip": False
        },
        deployment_controller={"type": "CODE_DEPLOY"},
        load_balancer=[ecs_service_mod.EcsServiceLoadBalancer(
            container_name="app",
            container_port=tfvars["container_port"],
            target_group_arn=alb_info["blue_target_group_arn"]
        )],
        lifecycle=TerraformResourceLifecycle(
            ignore_changes=["task_definition", "load_balancer"]
        ),
        depends_on=[alb_info["alb_listener"], alb_info["alb_test_listener"], log_group, repo, task],
    )

    cd_app = codedeploy_app.CodedeployApp(scope, f"{id}-cdapp", provider=provider, name=f"{tfvars['name']}-cdapp", compute_platform="ECS")

    CodedeployDeploymentGroup(scope, f"{id}-cdgroup",
        provider=provider,
        app_name=cd_app.name,
        deployment_group_name=f"{tfvars['name']}-dg",
        service_role_arn=codedeploy_role.arn,
        deployment_config_name="CodeDeployDefault.ECSAllAtOnce",
        deployment_style={
            "deployment_type": "BLUE_GREEN",
            "deployment_option": "WITH_TRAFFIC_CONTROL"
        },
        ecs_service={
            "cluster_name": cluster.name,
            "service_name": service.name
        },
        blue_green_deployment_config={
            "terminate_blue_instances_on_deployment_success": {
                "action": "TERMINATE",
                "termination_wait_time_in_minutes": 1
            },
            "deployment_ready_option": {
                "action_on_timeout": "CONTINUE_DEPLOYMENT"
            }
        },
        load_balancer_info=CodedeployDeploymentGroupLoadBalancerInfo(
            target_group_pair_info=CodedeployDeploymentGroupLoadBalancerInfoTargetGroupPairInfo(
                target_group=[
                    CodedeployDeploymentGroupLoadBalancerInfoTargetGroupPairInfoTargetGroup(
                        name=alb_info["blue_target_group_name"]
                    ),
                    CodedeployDeploymentGroupLoadBalancerInfoTargetGroupPairInfoTargetGroup(
                        name=alb_info["green_target_group_name"]
                    )
                ],
                prod_traffic_route={
                    "listener_arns": [alb_info["alb_listener"].arn]
                },
                test_traffic_route={
                    "listener_arns": [alb_info["alb_test_listener"].arn]
                }
            )
        ),
        depends_on=[log_group, alb_info["alb_listener"], alb_info["alb_test_listener"]],
    )

    # Auto Scaling Target
    scaling_target = appautoscaling_target.AppautoscalingTarget(scope, f"{id}-asg-target",
        provider=provider,
        max_capacity=tfvars["autoscaling_max_capacity"],
        min_capacity=tfvars["autoscaling_min_capacity"],
        resource_id=f"service/{cluster.name}/{service.name}",
        scalable_dimension="ecs:service:DesiredCount",
        service_namespace="ecs"
    )

    # Auto Scaling Policy - CPU
    appautoscaling_policy.AppautoscalingPolicy(scope, f"{id}-asg-policy-cpu",
        provider=provider,
        name=f"{tfvars['name']}-cpu-scaling-policy",
        policy_type="TargetTrackingScaling",
        resource_id=scaling_target.resource_id,
        scalable_dimension=scaling_target.scalable_dimension,
        service_namespace=scaling_target.service_namespace,
        target_tracking_scaling_policy_configuration={
            "target_value": tfvars["cpu_target_value"],
            "predefined_metric_specification": {
                "predefined_metric_type": "ECSServiceAverageCPUUtilization"
            },
            "scale_in_cooldown": 60,
            "scale_out_cooldown": 60
        }
    )

    appautoscaling_policy.AppautoscalingPolicy(scope, f"{id}-asg-policy-memory",
        provider=provider,
        name=f"{tfvars['name']}-memory-scaling-policy",
        policy_type="TargetTrackingScaling",
        resource_id=scaling_target.resource_id,
        scalable_dimension=scaling_target.scalable_dimension,
        service_namespace=scaling_target.service_namespace,
        target_tracking_scaling_policy_configuration={
            "target_value": tfvars["memory_target_value"],
            "predefined_metric_specification": {
                "predefined_metric_type": "ECSServiceAverageMemoryUtilization"
            },
            "scale_in_cooldown": 60,
            "scale_out_cooldown": 60
        }
    )

    # Auto scaling - for response time
    appautoscaling_policy.AppautoscalingPolicy(scope, f"{id}-asg-policy-response-time",
        provider=provider,
        name=f"{tfvars['name']}-response-scaling-policy",
        policy_type="TargetTrackingScaling",
        resource_id=scaling_target.resource_id,
        scalable_dimension=scaling_target.scalable_dimension,
        service_namespace=scaling_target.service_namespace,
        target_tracking_scaling_policy_configuration={
            "target_value": 0.3,
            "customized_metric_specification": {
                "metric_name": "TargetResponseTime",
                "namespace": "AWS/ApplicationELB",
                "statistic": "Average",
                "unit": "Seconds",
                "dimensions": [
                    {
                        "name": "LoadBalancer",
                        "value": Fn.join("/", [
                            "app",
                            Fn.element(Fn.split("/", alb_info["alb_listener"].arn), 1),
                            Fn.element(Fn.split("/", alb_info["alb_listener"].arn), 2)
                        ])
                    },
                    {
                        "name": "TargetGroup",
                        "value": Fn.join("/", [
                            "targetgroup",
                            Fn.element(Fn.split("/", alb_info["blue_target_group_arn"]), 1),
                            Fn.element(Fn.split("/", alb_info["blue_target_group_arn"]), 2)
                        ])
                    }
                ]
            },
            "scale_in_cooldown": 60,
            "scale_out_cooldown": 10
        }
    )


    return {
        "repo_url": repo.repository_url,
        "ecs_cluster": cluster.name,
        "ecs_service": service.name
    }
