# ────────────────────────────────────────────────
# 1. VPC
# ────────────────────────────────────────────────
resource "aws_vpc" "eks" {
  cidr_block           = "10.10.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "eks-vpc" }
}

# ────────────────────────────────────────────────
# 2. Internet Gateway
# ────────────────────────────────────────────────
resource "aws_internet_gateway" "eks" {
  vpc_id = aws_vpc.eks.id
  tags   = { Name = "eks-vpc-igw" }
}

# ────────────────────────────────────────────────
# 3. 서브넷
#    pub-sub1  10.10.1.0/24  ap-northeast-2a
#    pri-sub1  10.10.2.0/24  ap-northeast-2a
#    pub-sub2  10.10.11.0/24 ap-northeast-2c
#    pri-sub2  10.10.12.0/24 ap-northeast-2c
# ────────────────────────────────────────────────
resource "aws_subnet" "pub_sub1" {
  vpc_id                  = aws_vpc.eks.id
  cidr_block              = "10.10.1.0/24"
  availability_zone       = "ap-northeast-2a"
  map_public_ip_on_launch = true
  tags = {
    Name                                        = "eks-vpc-pub-sub1"
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

resource "aws_subnet" "pub_sub2" {
  vpc_id                  = aws_vpc.eks.id
  cidr_block              = "10.10.11.0/24"
  availability_zone       = "ap-northeast-2c"
  map_public_ip_on_launch = true
  tags = {
    Name                                        = "eks-vpc-pub-sub2"
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

resource "aws_subnet" "pri_sub1" {
  vpc_id            = aws_vpc.eks.id
  cidr_block        = "10.10.2.0/24"
  availability_zone = "ap-northeast-2a"
  tags = {
    Name                                        = "eks-vpc-pri-sub1"
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

resource "aws_subnet" "pri_sub2" {
  vpc_id            = aws_vpc.eks.id
  cidr_block        = "10.10.12.0/24"
  availability_zone = "ap-northeast-2c"
  tags = {
    Name                                        = "eks-vpc-pri-sub2"
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
  }
}

# ────────────────────────────────────────────────
# 4. 라우팅 테이블
# ────────────────────────────────────────────────
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.eks.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.eks.id
  }
  tags = { Name = "eks-vpc-pub-rt" }
}

resource "aws_route_table_association" "pub_sub1" {
  subnet_id      = aws_subnet.pub_sub1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "pub_sub2" {
  subnet_id      = aws_subnet.pub_sub2.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.eks.id
  tags   = { Name = "eks-vpc-pri-rt" }
}

resource "aws_route_table_association" "pri_sub1" {
  subnet_id      = aws_subnet.pri_sub1.id
  route_table_id = aws_route_table.private.id
}

resource "aws_route_table_association" "pri_sub2" {
  subnet_id      = aws_subnet.pri_sub2.id
  route_table_id = aws_route_table.private.id
}

# ────────────────────────────────────────────────
# 5. NAT Gateway (private 서브넷 아웃바운드용)
# ────────────────────────────────────────────────
resource "aws_eip" "nat" {
  domain     = "vpc"
  depends_on = [aws_internet_gateway.eks]
  tags       = { Name = "${var.cluster_name}-nat-eip" }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.pub_sub1.id
  depends_on    = [aws_internet_gateway.eks]
  tags          = { Name = "${var.cluster_name}-nat-gw" }
}

resource "aws_route" "private_nat" {
  route_table_id         = aws_route_table.private.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main.id
}

# ────────────────────────────────────────────────
# 6. EKS 클러스터
# ────────────────────────────────────────────────
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.35"

  vpc_id     = aws_vpc.eks.id
  subnet_ids = [aws_subnet.pri_sub1.id, aws_subnet.pri_sub2.id]

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    spot = {
      instance_types = ["t3.medium"]
      capacity_type  = "SPOT"

      min_size     = 1
      max_size     = 3
      desired_size = 2

      iam_role_additional_policies = {
        AmazonEC2ContainerRegistryReadOnly = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
      }
    }
  }

  enable_cluster_creator_admin_permissions = true
}

# ────────────────────────────────────────────────
# 7. AWS Load Balancer Controller
#    service.yaml의 type: LoadBalancer → NLB 생성에 필요
# ────────────────────────────────────────────────
data "aws_caller_identity" "current" {}

module "lb_controller_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name                              = "${var.cluster_name}-lb-controller"
  attach_load_balancer_controller_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }
}

resource "kubernetes_service_account" "lb_controller" {
  metadata {
    name      = "aws-load-balancer-controller"
    namespace = "kube-system"
    annotations = {
      "eks.amazonaws.com/role-arn" = module.lb_controller_irsa.iam_role_arn
    }
  }

  depends_on = [module.eks]
}

resource "helm_release" "lb_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = "1.14.0"

  set {
    name  = "clusterName"
    value = module.eks.cluster_name
  }
  set {
    name  = "serviceAccount.create"
    value = "false"
  }
  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }
  set {
    name  = "region"
    value = var.aws_region
  }
  set {
    name  = "vpcId"
    value = aws_vpc.eks.id
  }

  depends_on = [kubernetes_service_account.lb_controller]
}
