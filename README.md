# automated-clinvar-submission

## Table of Contents

- [automated-clinvar-submission](#automated-clinvar-submission)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
    - [Future features](#future-features)
  - [Installation](#installation)
      - [To run nextflow interactively](#to-run-nextflow-interactively)
  - [Pre-requirements](#pre-requirements)

## Introduction

This repository contains a Nextflow workflow designed to parse variant workbooks.
The workflow is configured to run both locally and in a production environment.
The production environment runs in a docker container.

## Features

- Runs `variant_workbook_parser` from [variant_workbook_parser GitHub repo](https://github.com/eastgenomics/variant_workbook_parser)
- Raises Slack notifications for logging and alerts

### Future features

- Automated submission to clinvar and local database
- Slack notifications for logging clinvar submission and any errors or re-running
- Re-running for any accesssion ids which require waiting.


## Installation
Step-by-step instructions on how to install the project.

Build Docker image
`cd automated-clinvar-submission`
`docker build . -t automated_clinvar_submission`

To deploy to server
`docker save automated_clinvar_submission -o automated_clinvar_submission.tar`
`gzip automated_clinvar_submission.tar`
Then upload to server via DNAnexus
`docker load -i automated_clinvar_submission.tar.gz`

Run docker with:
`docker run automated_clinvar_submission:latest nextflow run /home/main.nf -c /path/to/config.txt`

#### To run nextflow interactively
`docker run -it automated_clinvar_submission`
`nextflow run main.nf -c /path/to/config.txt`


## Pre-requirements
List the necessary pre-requirements for the project, including environment tokens:
- `DNANEXUS_TOKEN`: Your API token for accessing the DNANEXUS API.
- `SLACK_WEBHOOK_TEST`: webhook url for sending SLACK messages.
- `SLACK_WEBHOOK_LOGS`: webhook url for sending SLACK messages.
- `SLACK_WEBHOOK_ALERTS`: webhook url for sending SLACK messages.

Configuration file for nextflow pipeline

```json

// nextflow.config
params {
    dnanexusProject = "project-ID"
    indir = '/variant_workbook_parser/tests/test_data/CUH/'
    parsed_file_log = '/test_submission/workbooks_parsed_all_variants.txt'
    clinvar_file_log = '/test_submission/workbooks_parsed_clinvar_variants.txt'
    failed_file_log = '/test_submission/workbooks_fail_to_parse.txt'
    completed_dir = '/test_submission/completed_dir/'
    failed_dir = '/test_submission/failed_dir/'
    outdir = '/test_submission/Output/'
    unusual_sample_name = false
    no_dx_upload = true
    subfolder = 'csvs'
    }

```
