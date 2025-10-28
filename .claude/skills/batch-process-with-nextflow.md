# batch-process-with-nextflow

## Description

Process multiple samples or datasets through Nextflow modules using Python loops, pandas DataFrames, or parallel execution. This skill helps users efficiently run the same Nextflow module on many inputs, collect results, and integrate with data science workflows.

## When to Use

Use this skill when you need to:
- **Process multiple samples** through the same Nextflow module
- **Run batch jobs** from sample sheets or DataFrames
- **Collect results** from many executions
- **Scale workflows** to hundreds or thousands of samples
- **Track progress** and handle failures gracefully
- **Generate summary reports** from batch runs

## Keywords

batch processing, multiple samples, pandas integration, parallel execution, sample sheets, bulk processing

## Instructions

When a user wants to process multiple inputs with Nextflow modules, guide them through these patterns:

### 1. Basic Batch Processing Pattern

The fundamental pattern for batch processing:

```python
from pynf import NextflowEngine

# Sample list
samples = ["sample1", "sample2", "sample3"]

# Create engine once (important for performance!)
engine = NextflowEngine()
script_path = engine.load_script("modules/process.nf")

# Process each sample
results = []
for sample in samples:
    print(f"Processing {sample}...")

    result = engine.execute(
        script_path,
        params={"sample_name": sample},
        input_files=[f"data/{sample}.fastq"]
    )

    outputs = result.get_output_files()
    results.append({
        "sample": sample,
        "outputs": outputs,
        "num_files": len(outputs)
    })

# Summary
print(f"\nProcessed {len(results)} samples")
for r in results:
    print(f"  {r['sample']}: {r['num_files']} files")
```

### 2. Processing from Sample Sheet

Read samples from CSV and process:

```python
import pandas as pd
from pynf import NextflowEngine
from pathlib import Path

# Read sample sheet
samples_df = pd.read_csv("samplesheet.csv")
print(f"Loaded {len(samples_df)} samples")

# Example samplesheet.csv:
# sample_id,fastq_r1,fastq_r2,condition
# sample1,reads_R1.fq,reads_R2.fq,control
# sample2,reads_R1.fq,reads_R2.fq,treated

engine = NextflowEngine()
script_path = engine.load_script("modules/align.nf")

results = []
for idx, row in samples_df.iterrows():
    print(f"Processing {row['sample_id']} ({idx+1}/{len(samples_df)})...")

    result = engine.execute(
        script_path,
        params={
            "sample_name": row["sample_id"],
            "condition": row["condition"]
        },
        input_files=[row["fastq_r1"], row["fastq_r2"]]
    )

    # Collect outputs
    outputs = result.get_output_files()
    report = result.get_execution_report()

    results.append({
        "sample_id": row["sample_id"],
        "condition": row["condition"],
        "output_files": outputs,
        "completed_tasks": report["completed_tasks"],
        "failed_tasks": report["failed_tasks"],
        "status": "success" if report["failed_tasks"] == 0 else "failed"
    })

# Create results DataFrame
results_df = pd.DataFrame(results)
print("\nBatch processing complete:")
print(results_df[["sample_id", "status", "completed_tasks"]])

# Save results
results_df.to_csv("batch_results.csv", index=False)
```

### 3. Progress Tracking

Add progress indicators for long-running batches:

```python
from pynf import NextflowEngine
from tqdm import tqdm
import pandas as pd

def batch_process_with_progress(samples_df, module_path, **common_params):
    """Process samples with progress bar"""

    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    results = []

    # Use tqdm for progress bar
    for _, row in tqdm(samples_df.iterrows(),
                       total=len(samples_df),
                       desc="Processing samples"):

        # Merge row-specific and common params
        params = {**common_params}
        params.update(row.to_dict())

        try:
            result = engine.execute(
                script_path,
                params=params,
                input_files=[row["input_file"]]
            )

            outputs = result.get_output_files()
            status = "success" if outputs else "no_outputs"

        except Exception as e:
            outputs = []
            status = f"error: {str(e)}"

        results.append({
            "sample_id": row["sample_id"],
            "status": status,
            "outputs": outputs
        })

    return pd.DataFrame(results)

# Usage
samples = pd.read_csv("samples.csv")
results = batch_process_with_progress(
    samples,
    "modules/qc.nf",
    threads=4,
    quality_threshold=30
)
```

### 4. Error Handling and Retries

Robust batch processing with error handling:

```python
from pynf import NextflowEngine
import time

def process_sample_with_retry(engine, script_path, sample_info, max_retries=3):
    """Process single sample with retry logic"""

    for attempt in range(max_retries):
        try:
            result = engine.execute(
                script_path,
                params=sample_info["params"],
                input_files=sample_info["input_files"]
            )

            outputs = result.get_output_files()
            report = result.get_execution_report()

            if report["failed_tasks"] == 0:
                return {
                    "status": "success",
                    "outputs": outputs,
                    "attempts": attempt + 1
                }

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  Attempt {attempt + 1} failed, retrying...")
                time.sleep(5)  # Wait before retry
            else:
                return {
                    "status": "failed",
                    "error": str(e),
                    "attempts": attempt + 1
                }

    return {"status": "failed", "error": "Max retries exceeded"}

# Batch process with retries
def batch_process_robust(samples, module_path):
    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    results = []
    for sample in samples:
        print(f"Processing {sample['id']}...")

        result = process_sample_with_retry(
            engine,
            script_path,
            sample,
            max_retries=3
        )

        results.append({
            "sample_id": sample["id"],
            **result
        })

    return results
```

### 5. Collecting and Organizing Outputs

Organize batch outputs systematically:

```python
from pynf import NextflowEngine
from pathlib import Path
import shutil

def batch_process_and_organize(samples, module_path, output_base_dir):
    """Process samples and organize outputs by sample"""

    output_base = Path(output_base_dir)
    output_base.mkdir(exist_ok=True)

    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    results = []

    for sample_id in samples:
        print(f"Processing {sample_id}...")

        result = engine.execute(
            script_path,
            params={"sample_name": sample_id},
            input_files=[f"data/{sample_id}.fastq"]
        )

        # Create sample-specific output directory
        sample_outdir = output_base / sample_id
        sample_outdir.mkdir(exist_ok=True)

        # Copy outputs to organized location
        outputs = result.get_output_files()
        organized_outputs = []

        for output_file in outputs:
            output_path = Path(output_file)
            dest = sample_outdir / output_path.name
            shutil.copy(output_file, dest)
            organized_outputs.append(str(dest))

        results.append({
            "sample_id": sample_id,
            "output_dir": str(sample_outdir),
            "output_files": organized_outputs,
            "num_outputs": len(organized_outputs)
        })

        print(f"  Saved {len(organized_outputs)} files to {sample_outdir}")

    return results

# Usage
samples = ["sample1", "sample2", "sample3"]
results = batch_process_and_organize(
    samples,
    "modules/analysis.nf",
    "organized_results/"
)
```

### 6. Parallel Processing (Future)

Pattern for parallel execution (requires additional implementation):

```python
from pynf import NextflowEngine
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

def process_single_sample(sample_row, module_path, common_params):
    """Process single sample (will run in thread)"""

    # Note: Each thread needs its own engine
    # Current limitation: JVM shared across threads
    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    params = {**common_params}
    params.update({
        "sample_name": sample_row["sample_id"]
    })

    result = engine.execute(
        script_path,
        params=params,
        input_files=[sample_row["input_file"]]
    )

    return {
        "sample_id": sample_row["sample_id"],
        "outputs": result.get_output_files()
    }

def batch_process_parallel(samples_df, module_path, max_workers=4):
    """
    Parallel batch processing
    Note: Currently experimental due to JVM threading limitations
    """

    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_sample = {
            executor.submit(
                process_single_sample,
                row,
                module_path,
                {}
            ): row["sample_id"]
            for _, row in samples_df.iterrows()
        }

        # Collect results as they complete
        for future in as_completed(future_to_sample):
            sample_id = future_to_sample[future]
            try:
                result = future.result()
                results.append(result)
                print(f"✓ {sample_id} completed")
            except Exception as e:
                print(f"✗ {sample_id} failed: {e}")
                results.append({
                    "sample_id": sample_id,
                    "error": str(e)
                })

    return pd.DataFrame(results)

# Note: Use sequential processing for now
# Parallel support coming in future py-nf versions
```

### 7. Aggregating Results

Collect and summarize results from batch processing:

```python
from pynf import NextflowEngine
import pandas as pd
from pathlib import Path

def batch_process_with_aggregation(samples_df, module_path):
    """Process samples and aggregate results"""

    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    all_outputs = []
    summary_stats = {
        "total_samples": len(samples_df),
        "successful": 0,
        "failed": 0,
        "total_output_files": 0
    }

    for _, row in samples_df.iterrows():
        sample_id = row["sample_id"]

        try:
            result = engine.execute(
                script_path,
                params={"sample_name": sample_id},
                input_files=[row["input_file"]]
            )

            outputs = result.get_output_files()
            report = result.get_execution_report()

            if report["failed_tasks"] == 0:
                summary_stats["successful"] += 1
            else:
                summary_stats["failed"] += 1

            summary_stats["total_output_files"] += len(outputs)

            # Store per-sample results
            for output in outputs:
                all_outputs.append({
                    "sample_id": sample_id,
                    "file_path": output,
                    "file_name": Path(output).name,
                    "file_size": Path(output).stat().st_size
                })

        except Exception as e:
            summary_stats["failed"] += 1
            print(f"Error processing {sample_id}: {e}")

    # Create detailed results DataFrame
    results_df = pd.DataFrame(all_outputs)

    return results_df, summary_stats

# Usage
samples = pd.read_csv("samples.csv")
results_df, stats = batch_process_with_aggregation(
    samples,
    "modules/qc.nf"
)

print(f"\nBatch Summary:")
print(f"  Total samples: {stats['total_samples']}")
print(f"  Successful: {stats['successful']}")
print(f"  Failed: {stats['failed']}")
print(f"  Total outputs: {stats['total_output_files']}")

# Analyze results
print(f"\nPer-sample output counts:")
print(results_df.groupby("sample_id").size())
```

### 8. Resumable Batch Processing

Save state to resume interrupted batch jobs:

```python
import json
from pathlib import Path
from pynf import NextflowEngine

def batch_process_resumable(samples, module_path, checkpoint_file="batch_checkpoint.json"):
    """Process samples with checkpoint/resume capability"""

    checkpoint_path = Path(checkpoint_file)

    # Load checkpoint if exists
    if checkpoint_path.exists():
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)
        processed = set(checkpoint.get("processed", []))
        results = checkpoint.get("results", [])
        print(f"Resuming: {len(processed)} samples already processed")
    else:
        processed = set()
        results = []

    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    try:
        for sample_id in samples:
            # Skip if already processed
            if sample_id in processed:
                print(f"Skipping {sample_id} (already processed)")
                continue

            print(f"Processing {sample_id}...")

            result = engine.execute(
                script_path,
                params={"sample_name": sample_id},
                input_files=[f"data/{sample_id}.fastq"]
            )

            outputs = result.get_output_files()
            results.append({
                "sample_id": sample_id,
                "outputs": outputs,
                "status": "success"
            })

            processed.add(sample_id)

            # Save checkpoint after each sample
            with open(checkpoint_path, "w") as f:
                json.dump({
                    "processed": list(processed),
                    "results": results
                }, f)

    except KeyboardInterrupt:
        print(f"\nInterrupted! Progress saved to {checkpoint_file}")
        print(f"Processed: {len(processed)}/{len(samples)} samples")
        return results

    # Clean up checkpoint on completion
    if checkpoint_path.exists():
        checkpoint_path.unlink()

    print(f"\nBatch complete: {len(processed)}/{len(samples)} samples")
    return results
```

## Complete Example Workflows

### Example 1: QC Pipeline for 100 Samples

```python
"""
Run quality control on 100 sequencing samples
"""
import pandas as pd
from pynf import NextflowEngine
from tqdm import tqdm
from pathlib import Path
import shutil

def run_batch_qc(samplesheet_path, output_dir):
    """Run QC module on all samples in samplesheet"""

    # Setup
    samples = pd.read_csv(samplesheet_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"Starting QC for {len(samples)} samples")

    engine = NextflowEngine()
    qc_module = engine.load_script("modules/fastqc.nf")

    results = []

    # Process with progress bar
    for _, row in tqdm(samples.iterrows(), total=len(samples)):
        sample_id = row["sample_id"]
        fastq_file = row["fastq_file"]

        try:
            # Run QC
            result = engine.execute(
                qc_module,
                params={"sample_name": sample_id},
                input_files=[fastq_file]
            )

            # Collect QC outputs
            outputs = result.get_output_files()

            # Organize by sample
            sample_dir = output_dir / sample_id
            sample_dir.mkdir(exist_ok=True)

            organized = []
            for output in outputs:
                dest = sample_dir / Path(output).name
                shutil.copy(output, dest)
                organized.append(str(dest))

            results.append({
                "sample_id": sample_id,
                "status": "success",
                "qc_reports": organized
            })

        except Exception as e:
            results.append({
                "sample_id": sample_id,
                "status": "failed",
                "error": str(e)
            })

    # Generate summary
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_dir / "qc_summary.csv", index=False)

    success_count = (results_df["status"] == "success").sum()
    print(f"\nQC Complete:")
    print(f"  Successful: {success_count}/{len(samples)}")
    print(f"  Results saved to: {output_dir}")

    return results_df

# Run
results = run_batch_qc("samples.csv", "qc_results/")
```

### Example 2: Multi-Step Pipeline for Cohort

```python
"""
Run multi-step analysis on patient cohort
"""
import pandas as pd
from pynf import NextflowEngine
from pathlib import Path

class CohortPipeline:
    def __init__(self, cohort_csv):
        self.cohort = pd.read_csv(cohort_csv)
        self.engine = NextflowEngine()
        self.results = []

    def step1_alignment(self):
        """Align all samples"""
        print("Step 1: Aligning reads...")

        align_module = self.engine.load_script("modules/align.nf")

        for _, row in self.cohort.iterrows():
            result = self.engine.execute(
                align_module,
                params={
                    "sample_id": row["patient_id"],
                    "reference": "genome.fa"
                },
                input_files=[row["fastq_r1"], row["fastq_r2"]]
            )

            bam = next(f for f in result.get_output_files() if f.endswith(".bam"))
            self.cohort.loc[self.cohort["patient_id"] == row["patient_id"], "bam"] = bam

    def step2_variant_calling(self):
        """Call variants on all samples"""
        print("Step 2: Calling variants...")

        caller_module = self.engine.load_script("modules/call_variants.nf")

        for _, row in self.cohort.iterrows():
            result = self.engine.execute(
                caller_module,
                params={"sample_id": row["patient_id"]},
                input_files=[row["bam"]]
            )

            vcf = next(f for f in result.get_output_files() if f.endswith(".vcf"))
            self.cohort.loc[self.cohort["patient_id"] == row["patient_id"], "vcf"] = vcf

    def step3_annotation(self):
        """Annotate variants"""
        print("Step 3: Annotating variants...")

        annotate_module = self.engine.load_script("modules/annotate.nf")

        for _, row in self.cohort.iterrows():
            result = self.engine.execute(
                annotate_module,
                params={"sample_id": row["patient_id"]},
                input_files=[row["vcf"]]
            )

            annotated = result.get_output_files()[0]
            self.results.append({
                "patient_id": row["patient_id"],
                "annotated_vcf": annotated
            })

    def run_pipeline(self):
        """Execute full pipeline"""
        self.step1_alignment()
        self.step2_variant_calling()
        self.step3_annotation()

        results_df = pd.DataFrame(self.results)
        results_df.to_csv("cohort_results.csv", index=False)

        print(f"\nPipeline complete for {len(self.results)} patients")
        return results_df

# Run cohort analysis
pipeline = CohortPipeline("cohort.csv")
results = pipeline.run_pipeline()
```

## Best Practices

1. **Reuse Engine**: Create `NextflowEngine` once, reuse for all samples
2. **Track Progress**: Use tqdm or logging for long batches
3. **Handle Errors**: Wrap execution in try/except, log failures
4. **Save Checkpoints**: Enable resuming for large batches
5. **Organize Outputs**: Create per-sample directories
6. **Generate Reports**: Create summary DataFrames
7. **Clean Up**: Remove work directories after collecting outputs

## Common Issues

**Issue: Running out of disk space**
```python
# Clean work directory between samples
import shutil
for sample in samples:
    result = engine.execute(...)
    outputs = result.get_output_files()
    # Copy outputs to permanent location
    ...
    # Clean temp files
    shutil.rmtree("work/", ignore_errors=True)
```

**Issue: Some samples fail**
```python
# Continue on failure, collect errors
errors = []
for sample in samples:
    try:
        result = engine.execute(...)
    except Exception as e:
        errors.append({"sample": sample, "error": str(e)})
        continue
```

## Related Skills

- **run-nextflow-module**: Basic execution for single samples
- **convert-nextflow-to-python**: Convert batch shell scripts
- **integrate-nextflow-pipeline**: Embed batch processing in larger workflows
