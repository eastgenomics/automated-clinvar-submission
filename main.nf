#!/usr/bin/env nextflow

nextflow.enable.dsl=2

// Define parameters with default values or set to null if not provided
params.indir = '/test_submission'
params.outdir = '/test_submission/Output/'
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
params.slack_channel = 'egg-test'
params.testing = true

process parse_workbooks {
    beforeScript 'echo "Starting the workflow"'
    // afterScript "bash /home/report_success.sh ${params.slack_channel} 'message' 'success'"

    script:
    def cmd = "/pyenv/shims/python3 /variant_workbook_parser/variant_workbook_parser.py"
    cmd += " --indir ${params.indir}"
    cmd += " --outdir ${params.outdir}"
    cmd += " --parsed_file_log ${params.parsed_file_log}"
    cmd += " --clinvar_file_log ${params.clinvar_file_log}"
    cmd += " --failed_file_log ${params.failed_file_log}"
    cmd += " --completed_dir ${params.completed_dir}"
    cmd += " --failed_dir ${params.failed_dir}"
    if (params.testing == true) {
        // This if block is conditional on the success of the script (cmd).
        // Otherwise the else raisies a failure message.
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        if ${cmd} --no_dx_upload; then
            echo "Success"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c 'egg-test' \
             -o "success" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log} -T
        else
            echo "Failure"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c 'egg-test' \
             -o "fail" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log} -T
        fi
        """
    }
    if (params.no_dx_upload == true) {
        // This if block is conditional on the success of the script (cmd).
        // Otherwise the else raisies a failure message.
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        if ${cmd} --no_dx_upload; then
            echo "Success"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c ${params.slack_channel} \
             -o "success" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log}
        else
            echo "Failure"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c ${params.slack_channel} \
             -o "fail" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log}
        fi
        """
    } else if (params.token) {
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        if ${cmd} --tk ${params.token}; then
            echo "Success"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c ${params.slack_channel} \
             -o "success" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log}
        else
            echo "Failure"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c ${params.slack_channel} \
             -o "fail" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log}
        fi
        """
    } else {
        """
        cp /variant_workbook_parser/parser_config.json ./parser_config.json
        if ${cmd}; then
            echo "Success"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c ${params.slack_channel} \
             -o "success" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log}
        else
            echo "Failure"
            /pyenv/shims/python3 /home/utils/slack_notifications.py -c ${params.slack_channel} \
             -o "fail" --fail-log-path ${params.failed_file_log} \
             --pass-log-path ${params.parsed_file_log}
        fi
        """
    }

}

workflow {
    parse_workbooks()
}

workflow.onError {
    println "Error: Pipeline execution stopped with the following message: ${workflow.errorMessage}"
    error = true
}

workflow.onComplete {
    if (error) {
        println "Error: Pipeline execution stopped with the following message: ${workflow.errorMessage}"
    }
    else {
        println "Workflow completed successfully"
    }
}
