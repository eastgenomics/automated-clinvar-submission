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
    - [Example Configuration files](#example-configuration-files)

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

### Example Configuration files
Configuration file for nextflow pipeline

```txt

// nextflow.config
params {
    dnanexusProject = "project-ID"
    indir = "/variant_workbook_parser/tests/test_data/CUH/"
    parsed_file_log = "/test_submission/workbooks_parsed_all_variants.txt"
    clinvar_file_log = "/test_submission/workbooks_parsed_clinvar_variants.txt"
    failed_file_log = "/test_submission/workbooks_fail_to_parse.txt"
    completed_dir = "/test_submission/completed_dir/"
    failed_dir = "/test_submission/failed_dir/"
    outdir = "/test_submission/Output/"
    no_dx_upload = true
    subfolder = "csvs"
    slack_channel = "egg-test"
    }

```

`dnanexusProject`: DNAneuxus project for uploading CSVs and logs. Not currently used.
`indir`: This is the input directory containing all the workbooks.
`parsed_file_log`: Path to the log file where details of parsed workbooks are recorded.
`clinvar_file_log`: Path to the log file where details of ClinVar variants to be submitted are recorded.
`failed_file_log`: Path to the log file where details of workbooks that failed processing are recorded.
`completed_dir`: Directory where successfully processed workbooks are stored.
`failed_dir`: Directory where workbooks that failed processing are stored.
`outdir`: Output directory where the results of the Nextflow pipeline are stored.
`no_dx_upload`: Flag indicating whether to skip uploading files to DNAnexus.
`subfolder`: Subfolder within the output directory for organizing CSVs in DNAnexus.
`slack_channel`: Slack channel where notifications about the pipeline's progress and results are sent.

Environmental variables file for docker.
``` txt
DX_PROJECT="project-ABC"
DX_TOKEN="tk"
SLACK_WEBHOOK_TEST=https://hooks.slack.com/services/T0XXXXX
SLACK_WEBHOOK_ALERTS=https://hooks.slack.com/services/T0XXXXX
```

Configuration ENV variables
`DX_PROJECT`: Define DNAnexus project - not currently used.
`DX_TOKEN`: Provides the API authorisation token for uploading CSVs and logs to DNAnexus project.
`SLACK_WEBHOOK_TEST`: Webhook for sending notifications to slack channel (`egg-test`).
`SLACK_WEBHOOK_ALERTS`: Webhook for sending notifications to slack channel (`egg-alerts`).
