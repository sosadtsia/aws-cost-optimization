
# SES Email Identity verification
resource "aws_ses_email_identity" "sender" {
  email = var.sender_email
}
