# ────────────────────────────────────────────────
# S3 — lprnet-bucket
#
# 폴더 구조 (코드로 생성하지 않음 — 업로드 시 prefix로 자동 생성됨):
#   dataset/train/        # 학습용 (6,936장)
#   dataset/val/          # 검증용 (1,485장)
#   dataset/test/         # 평가 자동화 전용 (1,485장)
#   eval-results/         # 평가 결과 JSON 이력
#   models/               # ONNX 모델 가중치
# ────────────────────────────────────────────────
resource "aws_s3_bucket" "lprnet" {
  bucket = "lprnet-bucket"

  tags = {
    Name    = "lprnet-bucket"
    Project = "lprnet"
  }
}

# 퍼블릭 액세스 차단 (4종 모두 활성화)
resource "aws_s3_bucket_public_access_block" "lprnet" {
  bucket                  = aws_s3_bucket.lprnet.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 버저닝 비활성화 — 평가 결과 JSON은 타임스탬프 키로 관리
resource "aws_s3_bucket_versioning" "lprnet" {
  bucket = aws_s3_bucket.lprnet.id
  versioning_configuration {
    status = "Disabled"
  }
}

# ────────────────────────────────────────────────
# GitHub Actions OIDC Role 권한 추가
#   - Step 5(GitHub Actions CI/CD) 설정 후 아래 주석 해제
#   - role(github-actions-eval)을 먼저 생성한 뒤 terraform apply 재실행
# ────────────────────────────────────────────────
# data "aws_iam_role" "github_actions_eval" {
#   name = "github-actions-eval"
# }
#
# resource "aws_iam_role_policy" "github_actions_eval_lprnet" {
#   name = "lprnet-s3-cloudwatch"
#   role = data.aws_iam_role.github_actions_eval.name
#
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid    = "LprnetBucketAccess"
#         Effect = "Allow"
#         Action = [
#           "s3:GetObject",
#           "s3:PutObject",
#           "s3:ListBucket"
#         ]
#         Resource = [
#           aws_s3_bucket.lprnet.arn,
#           "${aws_s3_bucket.lprnet.arn}/*"
#         ]
#       },
#       {
#         Sid      = "LprnetCloudWatchMetrics"
#         Effect   = "Allow"
#         Action   = ["cloudwatch:PutMetricData"]
#         Resource = "*"
#         Condition = {
#           StringLike = {
#             "cloudwatch:namespace" = "LPRNet/*"
#           }
#         }
#       }
#     ]
#   })
# }
