#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Define parameters with default values or set to null if not provided
params.indir = '/test_submission'
params.outdir = '/test_submission/Output/'
params.file = null
params.parsed_file_log = '/test_submission/workbooks_parsed_all_variants.txt'
params.clinvar_file_log = '/test_submission/workbooks_parsed_clinvar_variants.txt'
params.failed_file_log = '/test_submission/workbooks_fail_to_parse.txt'
params.completed_dir = '/test_submission/completed_dir/'
params.failed_dir = '/test_submission/failed_dir/'
params.unusual_sample_name = false
params.no_dx_upload = true
params.subfolder = 'csvs'
// Retrieve the token from the environment variable DX_TOKEN
params.token = System.getenv('DX_TOKEN') ?: null

process parse_workbooks {

    script:
    def cmd = "python3 /variant_workbook_parser/variant_workbook_parser.py"
    cmd += " --indir ${params.indir}"
    cmd += " --outdir ${params.outdir}"
    cmd += " --parsed_file_log ${params.parsed_file_log}"
    cmd += " --clinvar_file_log ${params.clinvar_file_log}"
    cmd += " --failed_file_log ${params.failed_file_log}"
    cmd += " --completed_dir ${params.completed_dir}"
    cmd += " --failed_dir ${params.failed_dir}"
    if (params.no_dx_upload == true) {
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        ${cmd} --no_dx_upload"
        """
    } else if (params.token) {
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        ${cmd} --tk ${params.token}
        """
    } else {
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        ${cmd}
        """
    }
}

workflow {
    parse_workbooks()
}
