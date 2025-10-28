# convert-nextflow-to-python

## Description

Convert existing Nextflow command-line invocations to equivalent py-nf Python code. This skill helps users migrate from `nextflow run` commands to programmatic Python execution, enabling integration with data science workflows.

## When to Use

Use this skill when you need to:
- **Migrate** from command-line Nextflow to Python
- **Convert** existing `nextflow run` commands
- **Integrate** Nextflow pipelines into Python scripts
- **Understand** how CLI arguments map to py-nf API
- **Automate** workflows currently run manually
- **Document** Nextflow execution in Python

## Keywords

nextflow conversion, cli to python, command translation, migration, automation, python api

## Instructions

When a user provides a `nextflow run` command and wants the Python equivalent, follow this conversion process:

### 1. Analyze the Command

Parse the Nextflow command structure:

```bash
nextflow run <script> [options] [--param value ...]
```

**Common components:**
- Script path or pipeline name
- `-params-file` for parameter files
- `--param value` for individual parameters
- `-profile` for execution profiles
- `-resume` for continuing previous runs
- `-with-docker` / `-with-singularity` for containers

### 2. Basic Command Conversion

**Nextflow CLI:**
```bash
nextflow run script.nf
```

**Equivalent Python:**
```python
from pynf import NextflowEngine

engine = NextflowEngine()
script_path = engine.load_script("script.nf")
result = engine.execute(script_path)

outputs = result.get_output_files()
print(f"Outputs: {outputs}")
```

### 3. Parameter Conversion

**Nextflow CLI with parameters:**
```bash
nextflow run script.nf \
  --input sample.fastq \
  --output results/ \
  --threads 8 \
  --quality_threshold 30
```

**Equivalent Python:**
```python
from pynf import NextflowEngine

engine = NextflowEngine()
script_path = engine.load_script("script.nf")

result = engine.execute(
    script_path,
    params={
        "input": "sample.fastq",
        "output": "results/",
        "threads": 8,
        "quality_threshold": 30
    }
)

outputs = result.get_output_files()
print(f"Generated {len(outputs)} output files")
```

### 4. Parameters File Conversion

**Nextflow CLI with params file:**
```bash
nextflow run script.nf -params-file params.json
```

Where `params.json` contains:
```json
{
  "input": "sample.fastq",
  "threads": 8,
  "reference": "/data/genome.fa"
}
```

**Equivalent Python:**
```python
import json
from pynf import NextflowEngine

# Load parameters from file
with open("params.json") as f:
    params = json.load(f)

engine = NextflowEngine()
script_path = engine.load_script("script.nf")

result = engine.execute(script_path, params=params)
outputs = result.get_output_files()
```

**Or with YAML params:**
```python
import yaml
from pynf import NextflowEngine

with open("params.yaml") as f:
    params = yaml.safe_load(f)

engine = NextflowEngine()
result = engine.execute(
    engine.load_script("script.nf"),
    params=params
)
```

### 5. Input Files Conversion

**Nextflow CLI:**
```bash
nextflow run script.nf --reads "data/*.fastq.gz"
```

**Equivalent Python:**
```python
from pathlib import Path
from pynf import NextflowEngine

# Glob for input files
input_files = list(Path("data").glob("*.fastq.gz"))
input_file_paths = [str(f) for f in input_files]

engine = NextflowEngine()
result = engine.execute(
    engine.load_script("script.nf"),
    params={"reads": "data/*.fastq.gz"},  # Pattern passed to Nextflow
    # Or provide resolved files:
    # input_files=input_file_paths
)
```

### 6. Multiple Run Conversion

**Nextflow CLI (running multiple times):**
```bash
for sample in sample1 sample2 sample3; do
  nextflow run script.nf --input ${sample}.fastq --output ${sample}_results/
done
```

**Equivalent Python:**
```python
from pynf import NextflowEngine

samples = ["sample1", "sample2", "sample3"]

# Create engine once (reuse JVM)
engine = NextflowEngine()
script_path = engine.load_script("script.nf")

results = {}
for sample in samples:
    print(f"Processing {sample}...")

    result = engine.execute(
        script_path,
        params={
            "input": f"{sample}.fastq",
            "output": f"{sample}_results/"
        }
    )

    outputs = result.get_output_files()
    results[sample] = outputs
    print(f"  Generated {len(outputs)} files")

# Summary
for sample, outputs in results.items():
    print(f"{sample}: {len(outputs)} outputs")
```

### 7. Complex Command Conversion

**Complex Nextflow CLI:**
```bash
nextflow run nf-core/rnaseq \
  --input samplesheet.csv \
  --outdir results \
  --genome GRCh38 \
  --aligner star \
  --skip_trimming false \
  --save_align_intermeds \
  -profile docker \
  -resume
```

**Equivalent Python:**
```python
from pynf import NextflowEngine
import shutil

engine = NextflowEngine()

# Note: nf-core pipelines require local download first
# See download-nfcore-module skill for details
script_path = engine.load_script("nf-core-rnaseq/main.nf")

result = engine.execute(
    script_path,
    params={
        "input": "samplesheet.csv",
        "outdir": "results",
        "genome": "GRCh38",
        "aligner": "star",
        "skip_trimming": False,
        "save_align_intermeds": True,
    }
    # Note: -profile and -resume are execution options
    # Container support coming in future py-nf versions
)

# Check execution
report = result.get_execution_report()
if report["failed_tasks"] == 0:
    print("Pipeline completed successfully")
    outputs = result.get_output_files()
    print(f"Generated {len(outputs)} output files in results/")
else:
    print(f"Warning: {report['failed_tasks']} tasks failed")
```

### 8. Conversion Templates

Provide ready-to-use templates for common patterns:

#### Template 1: Simple Module Execution

```python
"""
Convert: nextflow run module.nf --param value --input file.txt

To this Python template:
"""
from pynf import NextflowEngine

def run_module(input_file, param_value):
    engine = NextflowEngine()
    script_path = engine.load_script("module.nf")

    result = engine.execute(
        script_path,
        params={"param": param_value},
        input_files=[input_file]
    )

    outputs = result.get_output_files()
    return outputs

# Usage
outputs = run_module("file.txt", "value")
print(outputs)
```

#### Template 2: Batch Processing

```python
"""
Convert: Multiple nextflow run commands with different inputs

To this Python template:
"""
from pynf import NextflowEngine
from pathlib import Path
import pandas as pd

def batch_process(sample_list, module_path, **common_params):
    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    results = []
    for sample in sample_list:
        print(f"Processing {sample}...")

        # Merge sample-specific params
        params = {**common_params, "sample_name": sample}

        result = engine.execute(
            script_path,
            params=params,
            input_files=[f"{sample}.fastq"]
        )

        outputs = result.get_output_files()
        results.append({
            "sample": sample,
            "outputs": outputs,
            "status": "success" if outputs else "failed"
        })

    return pd.DataFrame(results)

# Usage
samples = ["sample1", "sample2", "sample3"]
results_df = batch_process(
    samples,
    "modules/qc.nf",
    threads=4,
    quality_threshold=30
)
print(results_df)
```

#### Template 3: Pipeline with Intermediate Outputs

```python
"""
Convert: Multi-step nextflow pipeline

To this Python template:
"""
from pynf import NextflowEngine
from pathlib import Path

class NextflowPipeline:
    def __init__(self):
        self.engine = NextflowEngine()

    def step1_preprocess(self, input_file):
        script = self.engine.load_script("modules/preprocess.nf")
        result = self.engine.execute(
            script,
            input_files=[input_file]
        )
        outputs = result.get_output_files()
        return outputs[0]  # Return first output for next step

    def step2_analyze(self, preprocessed_file):
        script = self.engine.load_script("modules/analyze.nf")
        result = self.engine.execute(
            script,
            input_files=[preprocessed_file]
        )
        return result.get_output_files()

    def run_pipeline(self, input_file):
        print("Step 1: Preprocessing...")
        preprocessed = self.step1_preprocess(input_file)
        print(f"Preprocessed: {preprocessed}")

        print("Step 2: Analysis...")
        outputs = self.step2_analyze(preprocessed)
        print(f"Final outputs: {outputs}")

        return outputs

# Usage
pipeline = NextflowPipeline()
results = pipeline.run_pipeline("input.txt")
```

### 9. Handling Special Cases

**Resume functionality:**
```python
# Nextflow: -resume
# Python: Work directory persists by default
# To clear state:
import shutil
shutil.rmtree("work/", ignore_errors=True)
shutil.rmtree(".nextflow/", ignore_errors=True)

result = engine.execute(script_path, params=params)
```

**Container execution:**
```python
# Nextflow: -with-docker image:tag
# Python: Container support coming in future versions
# Current workaround: Ensure tools installed locally
# Or use Docker-enabled Nextflow config
```

**Profile selection:**
```python
# Nextflow: -profile docker,cluster
# Python: Not directly supported yet
# Workaround: Create config file and set NXF_CONFIG env var
import os
os.environ["NXF_CONFIG"] = "nextflow.config"
result = engine.execute(script_path, params=params)
```

### 10. Interactive Conversion Tool

Provide an interactive conversion helper:

```python
"""
Interactive CLI to Python converter
"""

def convert_nextflow_command(command: str) -> str:
    """Convert nextflow run command to Python code"""

    # Parse command
    parts = command.split()
    if "nextflow" not in parts[0]:
        return "Error: Not a nextflow command"

    # Extract script
    run_idx = parts.index("run")
    script = parts[run_idx + 1]

    # Extract parameters
    params = {}
    i = run_idx + 2
    while i < len(parts):
        if parts[i].startswith("--"):
            param_name = parts[i][2:]  # Remove --
            param_value = parts[i + 1] if i + 1 < len(parts) else None
            params[param_name] = param_value
            i += 2
        else:
            i += 1

    # Generate Python code
    code = f'''from pynf import NextflowEngine

engine = NextflowEngine()
script_path = engine.load_script("{script}")

result = engine.execute(
    script_path,
    params={params}
)

outputs = result.get_output_files()
print(f"Generated {{len(outputs)}} output files")
'''

    return code

# Usage
command = "nextflow run script.nf --input data.txt --threads 4"
python_code = convert_nextflow_command(command)
print(python_code)
```

## Example Conversions

### Example 1: RNA-seq Command

**Original Nextflow:**
```bash
nextflow run rnaseq.nf \
  --reads "data/*_{1,2}.fastq.gz" \
  --genome hg38 \
  --outdir results \
  --threads 16
```

**Converted Python:**
```python
from pynf import NextflowEngine
from pathlib import Path

engine = NextflowEngine()
script_path = engine.load_script("rnaseq.nf")

result = engine.execute(
    script_path,
    params={
        "reads": "data/*_{1,2}.fastq.gz",
        "genome": "hg38",
        "outdir": "results",
        "threads": 16
    }
)

# Check results
report = result.get_execution_report()
print(f"Completed: {report['completed_tasks']} tasks")
print(f"Results in: results/")
```

### Example 2: Variant Calling

**Original Nextflow:**
```bash
nextflow run variant_calling.nf \
  --bam aligned.bam \
  --reference genome.fa \
  --output variants.vcf \
  --min_qual 30 \
  --caller gatk
```

**Converted Python:**
```python
from pynf import NextflowEngine

engine = NextflowEngine()

result = engine.execute(
    engine.load_script("variant_calling.nf"),
    params={
        "bam": "aligned.bam",
        "reference": "genome.fa",
        "output": "variants.vcf",
        "min_qual": 30,
        "caller": "gatk"
    }
)

# Get VCF output
outputs = result.get_output_files()
vcf_file = next(f for f in outputs if f.endswith(".vcf"))
print(f"Variants called: {vcf_file}")

# Continue analysis in Python
import cyvcf2
vcf = cyvcf2.VCF(vcf_file)
print(f"Total variants: {sum(1 for _ in vcf)}")
```

### Example 3: Sample Sheet Processing

**Original Nextflow:**
```bash
nextflow run pipeline.nf --samplesheet samples.csv
```

Where `samples.csv`:
```csv
sample_id,fastq_1,fastq_2
sample1,reads_1.fq,reads_2.fq
sample2,reads_1.fq,reads_2.fq
```

**Converted Python:**
```python
from pynf import NextflowEngine
import pandas as pd

# Read sample sheet
samples = pd.read_csv("samples.csv")

engine = NextflowEngine()
script_path = engine.load_script("pipeline.nf")

# Process each sample
results = []
for _, row in samples.iterrows():
    result = engine.execute(
        script_path,
        params={
            "sample_id": row["sample_id"],
            "fastq_1": row["fastq_1"],
            "fastq_2": row["fastq_2"]
        }
    )

    outputs = result.get_output_files()
    results.append({
        "sample_id": row["sample_id"],
        "num_outputs": len(outputs),
        "output_files": outputs
    })

# Create results DataFrame
results_df = pd.DataFrame(results)
print(results_df)
```

## Conversion Checklist

When converting, verify:
- [ ] Script path is correct
- [ ] All `--param` converted to `params={}` dict
- [ ] Input files handled correctly
- [ ] Output collection implemented
- [ ] Error handling added
- [ ] Engine reused for multiple runs
- [ ] Results saved or processed

## Common Conversion Mistakes

**Mistake 1: Creating engine in loop**
```python
# BAD
for sample in samples:
    engine = NextflowEngine()  # Restarts JVM each time!
    result = engine.execute(...)

# GOOD
engine = NextflowEngine()  # Create once
for sample in samples:
    result = engine.execute(...)
```

**Mistake 2: Forgetting output collection**
```python
# BAD
result = engine.execute(script_path, params=params)
# ... nothing done with result

# GOOD
result = engine.execute(script_path, params=params)
outputs = result.get_output_files()
for output in outputs:
    process_file(output)
```

**Mistake 3: Not handling errors**
```python
# BAD
result = engine.execute(script_path, params=params)
outputs = result.get_output_files()
use_first_output(outputs[0])  # Crashes if no outputs!

# GOOD
result = engine.execute(script_path, params=params)
outputs = result.get_output_files()
if outputs:
    use_first_output(outputs[0])
else:
    print("No outputs produced - check logs")
```

## Related Skills

- **run-nextflow-module**: Learn the basic py-nf execution API
- **batch-process-with-nextflow**: Convert batch scripts efficiently
- **integrate-nextflow-pipeline**: Combine converted code with Python workflows
