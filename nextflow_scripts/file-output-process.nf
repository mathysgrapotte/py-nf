#!/usr/bin/env nextflow

process writeFile {
    output:
    path "output.txt"

    script:
    """
    echo "Hello from file output!" > output.txt
    """
}
