#!/usr/bin/env bash

## Upload V1 files
bash v1/cr_zip_upload_to_s3.sh

## Upload V2 files
bash v2/cr_zip_upload_to_s3.sh
