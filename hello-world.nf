#!/usr/bin/env nextflow

process sayHello {
    debug true

    output:
    stdout

    script:
    """
    echo 'Hello world from Python!'
    """
}

workflow {
    sayHello()
}