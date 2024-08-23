# automated-clinvar-submission

## Table of Contents

- [automated-clinvar-submission](#automated-clinvar-submission)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
    - [Future features](#future-features)
  - [Installation](#installation)
  - [Pre-requirements](#pre-requirements)
  - [Usage](#usage)
      - [Locally](#locally)
      - [In Docker env](#in-docker-env)
- [Developed by East Genomics](#developed-by-east-genomics)

## Introduction

This repository contains a Nextflow workflow designed to parse variant workbooks.
The workflow is configured to run both locally and in a production environment.
The production environment runs in a docker container ().


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
`docker run automated_clinvar_submission:latest`

## Pre-requirements
List the necessary pre-requirements for the project, including environment tokens:
- `DNANEXUS_TOKEN`: Your API token for accessing the DNANEXUS API.
- `SLACK_TOKEN`: API token to access SLACK and send messages to relevant channel.

## Usage

#### Locally

`docker run automated_clinvar_submission`

#### In Docker env
`docker run -it automated_clinvar_submission`
`nextflow run main.nf -c configuration_file.txt`


# Developed by East Genomics