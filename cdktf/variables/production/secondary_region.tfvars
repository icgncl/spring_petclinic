region                          = "eu-west-2"
availability_zones              = ["eu-west-2a", "eu-west-2b"]
vpc_cidr                        = "10.0.0.0/16"
public_subnet_cidrs             = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs            = ["10.0.101.0/24", "10.0.102.0/24"]
alb_sg_ingress_cidrs            = ["0.0.0.0/0"]
db_name                         = "gorilla_db"
db_username                     = "gorilla_user"
db_port                         = 5432
db_cidr_allow                   = ["10.0.0.0/16"]
db_instance_class_aurora        = "db.t4g.medium"
db_instance_class_rds           = "db.t3.medium"
db_allocated_storage            = 20
db_engine_version               = "17.5"
db_engine_aurora_version        = "15.3"
db_multi_az                     = true
cpu                             = 1024
memory                          = 2048
autoscaling_min_capacity        = 0
autoscaling_max_capacity        = 1
autoscaling_cpu_target          = 60
autoscaling_memory_target       = 75
autoscaling_scale_out_cooldown  = 60
autoscaling_scale_in_cooldown   = 120
ecr_lifecycle_policy_enabled    = true
ecr_lifecycle_policy_rules      = <<EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Expire untagged images older than 14 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 14
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF