output "vpc_id" {
  description = "사용 중인 VPC ID"
  value       = aws_vpc.eks.id
}

output "cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS API 서버 엔드포인트"
  value       = module.eks.cluster_endpoint
}

output "kubeconfig_command" {
  description = "kubectl 연결 명령어 (apply 완료 후 실행)"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "lb_controller_role_arn" {
  description = "AWS Load Balancer Controller IAM 역할 ARN"
  value       = module.lb_controller_irsa.iam_role_arn
}
