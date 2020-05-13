#!/bin/bash
set -euo pipefail
set -x

certs_subject="/C=US/ST=TX/L=Dallas/O=EMR/OU=EMR/CN=*.ec2.internal"

generate_certs() {
  openssl req -x509 -newkey rsa:4096 -keyout privateKey.pem -out certificateChain.pem -days 365 -nodes -subj ${certs_subject}
  cp certificateChain.pem trustedCertificates.pem
  zip -r -X $1-certs.zip certificateChain.pem privateKey.pem trustedCertificates.pem
  rm -rf *.pem
}

generate_certs ranger-server
generate_certs ranger-agents
generate_certs solr-client
generate_certs emr-certs
