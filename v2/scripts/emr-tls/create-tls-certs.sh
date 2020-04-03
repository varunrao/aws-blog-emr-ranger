#openssl req -x509 -newkey rsa:4096 -keyout inter-nodes.key -out inter-nodes.crt -days 365 -subj "/C=US/ST=TX/L=Dallas/O=EMR/OU=EMR/CN=*.ec2.internal" -nodes
#aws ssm put-parameter --name /emr/certificate --value fileb://inter-nodes.crt --type SecureString --key-id arn:aws:kms:us-east-1:762525141659:key/7386e23d-a610-4158-9d56-db2263ec2cc0 --overwrite --region us-east-1
#
#aws ssm put-parameter --name /emr/private-key --value fileb://inter-nodes.key --type SecureString --key-id arn:aws:kms:us-east-1:762525141659:key/7386e23d-a610-4158-9d56-db2263ec2cc0 --overwrite --region us-east-1
#
#aws ssm put-parameter --name /emr/inter-nodes-certificate --value fileb://inter-nodes.crt --type SecureString --key-id arn:aws:kms:us-east-1:762525141659:key/7386e23d-a610-4158-9d56-db2263ec2cc0 --overwrite --region us-east-1
#
#aws ssm put-parameter --name /emr/inter-nodes-private-key --value fileb://inter-nodes.key --type SecureString --key-id arn:aws:kms:us-east-1:762525141659:key/7386e23d-a610-4158-9d56-db2263ec2cc0 --overwrite --region us-east-1

openssl req -x509 -newkey rsa:1024 -keyout privateKey.pem -out certificateChain.pem -days 365 -nodes -subj '/C=US/ST=TX/L=Dallas/O=EMR/OU=EMR/CN=*.ec2.internal'
cp certificateChain.pem trustedCertificates.pem
zip -r -X emr-certs.zip certificateChain.pem privateKey.pem trustedCertificates.pem