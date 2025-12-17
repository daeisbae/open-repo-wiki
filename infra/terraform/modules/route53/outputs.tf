# Route53 Module Outputs

output "zone_id" {
  description = "Route53 hosted zone ID"
  value       = local.zone_id
}

output "name_servers" {
  description = "Name servers for the hosted zone (if created)"
  value       = var.create_hosted_zone ? aws_route53_zone.main[0].name_servers : []
}

output "cloudfront_record_fqdn" {
  description = "FQDN of the CloudFront A record"
  value       = var.create_cloudfront_records ? aws_route53_record.cloudfront_a[0].fqdn : ""
}

output "api_record_fqdn" {
  description = "FQDN of the API A record"
  value       = var.api_domain_name != "" ? aws_route53_record.api[0].fqdn : ""
}
