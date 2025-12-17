# CloudFront Module Outputs

output "distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.id
}

output "distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.arn
}

output "distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "distribution_hosted_zone_id" {
  description = "Hosted zone ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.hosted_zone_id
}

output "distribution_status" {
  description = "Status of the CloudFront distribution"
  value       = aws_cloudfront_distribution.main.status
}

output "oac_id" {
  description = "ID of the Origin Access Control"
  value       = aws_cloudfront_origin_access_control.main.id
}

output "oac_etag" {
  description = "ETag of the Origin Access Control"
  value       = aws_cloudfront_origin_access_control.main.etag
}

output "website_url" {
  description = "URL of the CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}
