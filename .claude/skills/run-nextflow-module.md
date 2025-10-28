# run-nextflow-module

## Description

Execute Nextflow modules and processes directly from Python using py-nf. This skill helps users run bioinformatics tools packaged as Nextflow modules without leaving Python, collecting outputs programmatically for further analysis.

## When to Use

Use this skill when you need to:
- **Run a Nextflow tool** from Python code
- **Execute bioinformatics workflows** in Jupyter notebooks
- **Integrate Nextflow modules** into Python scripts
- **Collect outputs** for downstream analysis
- **Avoid command-line** Nextflow invocation
- **Get programmatic access** to workflow results

## Keywords

nextflow execution, run module, python integration, bioinformatics, workflow execution, output collection

## Instructions

When a user wants to run a Nextflow module from Python, guide them through this process:

### 1. Understand the Module

First, identify what module they want to run:
- Local `.nf` file path
- Process name and parameters
- Required inputs
- Expected outputs

**Ask clarifying questions:**
- "Where is the Nextflow module located?"
- "What parameters does it need?"
- "What input files will you provide?"
- "What outputs do you expect?"

### 2. Basic Execution Pattern

Provide the standard py-nf execution template:

```python
from pynf import NextflowEngine
from pathlib import Path

# Initialize engine (reuse across multiple runs)
engine = NextflowEngine()

# Load the module
script_path = engine.load_script("path/to/module.nf")

# Execute with parameters
result = engine.execute(
    script_path,
    params={"param1": "value1", "param2": "value2"},
    input_files=["input1.fastq", "input2.fastq"]
)

# Collect outputs
output_files = result.get_output_files()
for file_path in output_files:
    print(f"Output: {file_path}")
```

### 3. Parameter Handling

Help users map their data to Nextflow parameters:

**Simple parameters:**
```python
params = {
    "threads": 4,
    "output_name": "results.txt",
    "quality_threshold": 30,
    "enable_trimming": True
}

result = engine.execute(script_path, params=params)
```

**Input files:**
```python
# Single input file
input_files = ["sample.fastq.gz"]

# Multiple input files
input_files = [
    "sample_R1.fastq.gz",
    "sample_R2.fastq.gz"
]

# Paths from variables
input_path = Path("/data/samples/sample.bam")
input_files = [str(input_path)]
```

**Mixed params and inputs:**
```python
result = engine.execute(
    script_path,
    params={
        "threads": 8,
        "min_quality": 20
    },
    input_files=["reads.fastq"]
)
```

### 4. Output Collection

Show users how to access different types of outputs:

**File outputs:**
```python
# Get all output files
output_files = result.get_output_files()

# Find specific output by name
from pathlib import Path
output_bam = next(
    (p for p in output_files if Path(p).name.endswith(".bam")),
    None
)

if output_bam:
    print(f"BAM file: {output_bam}")
    # Use in downstream analysis
    import pysam
    bam = pysam.AlignmentFile(output_bam, "rb")
```

**Workflow outputs (from emit:):**
```python
# Get structured workflow outputs
workflow_outputs = result.get_workflow_outputs()

for output in workflow_outputs:
    name = output["name"]
    value = output["value"]
    print(f"{name}: {value}")
```

**Execution metrics:**
```python
# Get execution report
report = result.get_execution_report()
print(f"Completed tasks: {report['completed_tasks']}")
print(f"Failed tasks: {report['failed_tasks']}")
print(f"Work directory: {report['work_dir']}")
```

**Process stdout:**
```python
# Get stdout from process
stdout = result.get_stdout()
print("Process output:")
print(stdout)
```

### 5. Common Use Cases

Provide examples for typical scenarios:

#### Use Case 1: Quality Control

```python
"""Run FASTQC quality control on a sequencing file"""
from pynf import NextflowEngine

engine = NextflowEngine()
fastqc_module = engine.load_script("modules/fastqc.nf")

# Run quality control
result = engine.execute(
    fastqc_module,
    input_files=["sample.fastq.gz"],
    params={"outdir": "qc_results"}
)

# Get QC report
qc_reports = result.get_output_files()
html_report = next(p for p in qc_reports if p.endswith(".html"))
print(f"QC report: {html_report}")
```

#### Use Case 2: Sequence Alignment

```python
"""Align reads to reference genome"""
from pynf import NextflowEngine
from pathlib import Path

engine = NextflowEngine()
aligner = engine.load_script("modules/bwa_mem.nf")

# Run alignment
result = engine.execute(
    aligner,
    params={
        "reference": "/data/genomes/hg38.fa",
        "threads": 16,
        "sample_name": "patient_001"
    },
    input_files=[
        "patient_001_R1.fastq.gz",
        "patient_001_R2.fastq.gz"
    ]
)

# Get aligned BAM
outputs = result.get_output_files()
bam_file = next(p for p in outputs if Path(p).suffix == ".bam")

# Continue with downstream analysis
import pysam
alignment = pysam.AlignmentFile(bam_file, "rb")
num_reads = alignment.count()
print(f"Aligned {num_reads} reads")
```

#### Use Case 3: Variant Calling

```python
"""Call variants from aligned reads"""
from pynf import NextflowEngine

engine = NextflowEngine()
caller = engine.load_script("modules/bcftools_call.nf")

result = engine.execute(
    caller,
    params={
        "reference": "/data/genomes/hg38.fa",
        "min_base_quality": 20,
        "min_mapping_quality": 30
    },
    input_files=["aligned.bam"]
)

# Get VCF file
outputs = result.get_output_files()
vcf_file = next(p for p in outputs if p.endswith(".vcf.gz"))

# Parse variants
import cyvcf2
vcf = cyvcf2.VCF(vcf_file)
variants = [v for v in vcf if v.FILTER is None]  # Pass filter
print(f"Found {len(variants)} high-quality variants")
```

### 6. Error Handling

Show users how to handle common errors:

```python
from pynf import NextflowEngine

engine = NextflowEngine()

try:
    script_path = engine.load_script("modules/tool.nf")
    result = engine.execute(
        script_path,
        params={"required_param": "value"}
    )

    # Check execution success
    report = result.get_execution_report()
    if report["failed_tasks"] > 0:
        print(f"Warning: {report['failed_tasks']} tasks failed")
        # Inspect logs in work directory
        print(f"Check logs in: {report['work_dir']}")

    outputs = result.get_output_files()
    if not outputs:
        print("Warning: No output files produced")

except FileNotFoundError as e:
    print(f"Error: Module not found - {e}")
    print("Check the path to your .nf file")

except Exception as e:
    print(f"Execution error: {e}")
    # Check Nextflow logs
    print("Review .nextflow.log for details")
```

### 7. Best Practices

Provide guidance on efficient usage:

**Reuse engine instance:**
```python
# GOOD: Create engine once
engine = NextflowEngine()

for sample in samples:
    script_path = engine.load_script("module.nf")
    result = engine.execute(script_path, input_files=[sample])
    process_outputs(result)

# BAD: Creating engine each time (slow)
for sample in samples:
    engine = NextflowEngine()  # Restarts JVM!
    # ...
```

**Clean work directory:**
```python
import shutil

# After collecting outputs
outputs = result.get_output_files()
# Copy outputs to permanent location
for output in outputs:
    shutil.copy(output, "/results/")

# Clean temporary work directory
shutil.rmtree("work/")
shutil.rmtree(".nextflow/")
```

**Handle missing outputs gracefully:**
```python
outputs = result.get_output_files()

# Filter for specific file type
bam_files = [p for p in outputs if p.endswith(".bam")]

if not bam_files:
    print("No BAM files produced - check execution logs")
    report = result.get_execution_report()
    print(f"Work directory: {report['work_dir']}")
else:
    print(f"Generated {len(bam_files)} BAM files")
```

### 8. Integration with Data Science Tools

Show integration with common Python libraries:

**With Pandas:**
```python
import pandas as pd
from pynf import NextflowEngine

# Read sample metadata
samples_df = pd.read_csv("samples.csv")

engine = NextflowEngine()
script_path = engine.load_script("modules/process.nf")

# Run for each sample
results = []
for _, row in samples_df.iterrows():
    result = engine.execute(
        script_path,
        params={"sample_name": row["sample_id"]},
        input_files=[row["file_path"]]
    )

    outputs = result.get_output_files()
    results.append({
        "sample_id": row["sample_id"],
        "output_file": outputs[0] if outputs else None
    })

# Create results DataFrame
results_df = pd.DataFrame(results)
print(results_df)
```

**In Jupyter Notebooks:**
```python
# In Jupyter cell
from pynf import NextflowEngine
from IPython.display import display, HTML

engine = NextflowEngine()
result = engine.execute(
    engine.load_script("modules/analysis.nf"),
    input_files=["data.csv"]
)

# Display execution report
report = result.get_execution_report()
print(f"✓ Completed: {report['completed_tasks']} tasks")

# Show outputs
outputs = result.get_output_files()
for output in outputs:
    if output.endswith(".html"):
        # Display HTML reports inline
        with open(output) as f:
            display(HTML(f.read()))
```

**With scikit-learn pipelines:**
```python
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from pynf import NextflowEngine

class NextflowPreprocessor(BaseEstimator, TransformerMixin):
    """Scikit-learn transformer that runs Nextflow module"""

    def __init__(self, module_path, params=None):
        self.module_path = module_path
        self.params = params or {}
        self.engine = NextflowEngine()

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """X is list of input file paths"""
        results = []
        script_path = self.engine.load_script(self.module_path)

        for input_file in X:
            result = self.engine.execute(
                script_path,
                params=self.params,
                input_files=[input_file]
            )
            outputs = result.get_output_files()
            results.extend(outputs)

        return results

# Use in pipeline
pipeline = Pipeline([
    ("preprocess", NextflowPreprocessor("modules/clean.nf")),
    # ... other steps ...
])
```

## Example Workflows

### Complete Example: RNA-seq Pipeline

```python
"""Complete RNA-seq analysis from FASTQ to counts"""
from pynf import NextflowEngine
from pathlib import Path
import pandas as pd

def run_rnaseq_pipeline(fastq_r1, fastq_r2, sample_name, output_dir):
    """Run complete RNA-seq pipeline"""

    engine = NextflowEngine()
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Step 1: Quality control
    print("Running FASTQC...")
    qc_module = engine.load_script("modules/fastqc.nf")
    qc_result = engine.execute(
        qc_module,
        input_files=[fastq_r1, fastq_r2]
    )
    qc_reports = qc_result.get_output_files()
    print(f"Generated {len(qc_reports)} QC reports")

    # Step 2: Trimming
    print("Trimming adapters...")
    trim_module = engine.load_script("modules/trimgalore.nf")
    trim_result = engine.execute(
        trim_module,
        params={"quality": 20, "length": 50},
        input_files=[fastq_r1, fastq_r2]
    )
    trimmed_files = trim_result.get_output_files()
    trimmed_r1 = next(f for f in trimmed_files if "R1" in f)
    trimmed_r2 = next(f for f in trimmed_files if "R2" in f)

    # Step 3: Alignment
    print("Aligning to genome...")
    align_module = engine.load_script("modules/star_align.nf")
    align_result = engine.execute(
        align_module,
        params={
            "genome_index": "/data/genomes/hg38_star",
            "threads": 16
        },
        input_files=[trimmed_r1, trimmed_r2]
    )
    bam_files = align_result.get_output_files()
    bam_file = next(f for f in bam_files if f.endswith(".bam"))

    # Step 4: Count features
    print("Counting features...")
    count_module = engine.load_script("modules/featurecounts.nf")
    count_result = engine.execute(
        count_module,
        params={
            "gtf": "/data/annotations/genes.gtf",
            "sample_name": sample_name
        },
        input_files=[bam_file]
    )
    count_files = count_result.get_output_files()
    counts_file = next(f for f in count_files if f.endswith(".txt"))

    # Load counts into DataFrame
    counts_df = pd.read_csv(counts_file, sep="\t")

    return {
        "qc_reports": qc_reports,
        "bam": bam_file,
        "counts": counts_df,
        "counts_file": counts_file
    }

# Run on sample
results = run_rnaseq_pipeline(
    "sample_R1.fastq.gz",
    "sample_R2.fastq.gz",
    "sample_001",
    "results/"
)

print(f"Pipeline complete!")
print(f"Counts shape: {results['counts'].shape}")
```

## Common Issues and Solutions

**Issue: Module not found**
```python
# Make sure path is correct
from pathlib import Path
module_path = Path("modules/tool.nf")
if not module_path.exists():
    print(f"Module not found at {module_path.absolute()}")
```

**Issue: No outputs produced**
```python
# Check execution report
report = result.get_execution_report()
if report["failed_tasks"] > 0:
    print("Some tasks failed - check work directory")
    print(f"Work dir: {report['work_dir']}")
```

**Issue: Wrong parameters**
```python
# Read module to understand required params
with open("modules/tool.nf") as f:
    content = f.read()
    if "params.required_param" in content:
        print("Module requires 'required_param'")
```

## Related Skills

- **convert-nextflow-to-python**: Convert `nextflow run` commands to py-nf code
- **batch-process-with-nextflow**: Process multiple samples efficiently
- **integrate-nextflow-pipeline**: Combine Nextflow with Python workflows
- **download-nfcore-module**: Use nf-core modules from registry
