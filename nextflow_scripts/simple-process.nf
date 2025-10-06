#!/usr/bin/env nextflow

process sayHello {
    debug true

    script:
    """
    echo 'Hello from a raw module!'
    """
}
