#!/usr/bin/env nextflow

process sayHello {
    debug true

    script:
    """
    echo 'Hello world from Python!'
    """
}

workflow {
    sayHello()
}
