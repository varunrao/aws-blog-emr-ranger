#!/bin/bash

#CHECKTHIS
certs_s3_location=$1
#certs_s3_location="s3://MYBUCKET/ranger/certs"

generate_and_push_cert () {
   openssl req -x509 -newkey rsa:4096 -keyout privateKey.pem -out certificateChain.pem -days 365 -nodes -subj '/C=US/ST=TX/L=Dallas/O=EMR/OU=EMR/CN=*.ec2.internal'
   cp certificateChain.pem trustedCertificates.pem
   zip -r -X $1-certs.zip certificateChain.pem privateKey.pem trustedCertificates.pem
   rm -rf *.pem
   aws s3 cp $1-certs.zip ${certs_s3_location}/
}

generate_and_push_cert RangerServer
generate_and_push_cert RangerAgents
generate_and_push_cert Solrr-certs.zip certificateChain.pem privateKey.pem trustedCertificates.pem