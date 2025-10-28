# download-nfcore-module

## Description

Fetch and run nf-core modules from the community repository using py-nf. This skill helps users discover, download, and execute validated bioinformatics modules from nf-core, handling module structure, meta maps, and common nf-core conventions.

## When to Use

Use this skill when you need to:
- **Use nf-core modules** from Python
- **Download** specific tools from nf-core
- **Run validated** bioinformatics modules
- **Handle** nf-core meta map patterns
- **Avoid** writing custom Nextflow modules
- **Leverage** community-maintained tools

## Keywords

nf-core, module download, community modules, bioinformatics tools, meta maps, nf-core modules

## Instructions

When a user wants to use nf-core modules with py-nf, guide them through this process:

### 1. Understanding nf-core Modules

nf-core modules follow specific conventions:

**Module structure:**
```
modules/nf-core/
  tool/
    main.nf          # Process definition
    meta.yml         # Module metadata
    environment.yml  # Conda environment (optional)
```

**Common patterns:**
- Use `meta` map for sample metadata
- Inputs: `tuple val(meta), path(files)`
- Outputs: `tuple val(meta), path("*.output")`
- Containers specified for tools
- Standardized process naming

### 2. Browsing Available Modules

Help users find modules:

**nf-core modules website:**
- Browse: https://nf-co.re/modules
- Search by tool name (e.g., "fastqc", "samtools", "bwa")
- View module documentation and usage

**Command to list modules:**
```bash
# Install nf-core tools (if not already)
pip install nf-core

# List available modules
nf-core modules list remote
```

### 3. Downloading Modules

Guide module download:

**Option 1: Using nf-core tools CLI**
```bash
# Initialize modules directory
mkdir -p modules

# Download specific module
nf-core modules install fastqc

# This creates: modules/nf-core/fastqc/
```

**Option 2: Manual download from GitHub**
```bash
# Clone modules repository
git clone --depth 1 \
  https://github.com/nf-core/modules.git \
  temp_modules

# Copy specific module
cp -r temp_modules/modules/nf-core/fastqc modules/nf-core/

# Clean up
rm -rf temp_modules
```

**Python helper for download:**
```python
import subprocess
from pathlib import Path

def download_nfcore_module(module_name, dest_dir="modules"):
    """Download nf-core module using nf-core CLI"""

    dest_path = Path(dest_dir)
    dest_path.mkdir(exist_ok=True)

    # Use nf-core tools to download
    result = subprocess.run(
        ["nf-core", "modules", "install", module_name, "--dir", str(dest_path)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"✓ Downloaded {module_name}")
        module_path = dest_path / "nf-core" / module_name / "main.nf"
        return str(module_path)
    else:
        print(f"✗ Failed to download {module_name}")
        print(result.stderr)
        return None

# Usage
module_path = download_nfcore_module("fastqc")
```

### 4. Running nf-core Modules

Basic execution pattern:

```python
from pynf import NextflowEngine
from pathlib import Path

# Download module first (see above)

# Run module
engine = NextflowEngine()
fastqc_module = engine.load_script("modules/nf-core/fastqc/main.nf")

result = engine.execute(
    fastqc_module,
    input_files=["sample.fastq.gz"]
)

# Get QC report
qc_outputs = result.get_output_files()
print(f"QC reports: {qc_outputs}")
```

### 5. Handling Meta Maps

nf-core modules use `meta` maps for metadata:

**Understanding meta maps:**
```groovy
// Typical nf-core input
tuple val(meta), path(reads)

// meta is a map:
meta = [
    id: 'sample1',
    single_end: false,
    condition: 'control'
]
```

**Providing meta in py-nf:**
```python
from pynf import NextflowEngine

engine = NextflowEngine()
module = engine.load_script("modules/nf-core/tool/main.nf")

# Create meta map as params
result = engine.execute(
    module,
    params={
        "meta": {
            "id": "sample1",
            "single_end": False,
            "condition": "control"
        }
    },
    input_files=["sample_R1.fastq.gz", "sample_R2.fastq.gz"]
)

outputs = result.get_output_files()
```

**Helper function for meta maps:**
```python
def create_meta_map(sample_id, single_end=False, **kwargs):
    """Create nf-core compatible meta map"""
    meta = {
        "id": sample_id,
        "single_end": single_end
    }
    meta.update(kwargs)
    return meta

# Usage
meta = create_meta_map(
    "sample1",
    single_end=False,
    condition="treated",
    replicate=1
)
```

### 6. Common nf-core Modules

Provide ready-to-use patterns for popular modules:

#### FASTQC

```python
from pynf import NextflowEngine

def run_fastqc(fastq_file, sample_id):
    """Run FASTQC module from nf-core"""

    engine = NextflowEngine()
    fastqc = engine.load_script("modules/nf-core/fastqc/main.nf")

    result = engine.execute(
        fastqc,
        params={
            "meta": {"id": sample_id}
        },
        input_files=[fastq_file]
    )

    # Get HTML and zip outputs
    outputs = result.get_output_files()
    html_report = next(f for f in outputs if f.endswith(".html"))
    zip_file = next(f for f in outputs if f.endswith(".zip"))

    return {
        "html": html_report,
        "zip": zip_file
    }

# Usage
qc_results = run_fastqc("sample.fastq.gz", "sample1")
print(f"QC report: {qc_results['html']}")
```

#### BWA/MEM

```python
from pynf import NextflowEngine

def run_bwa_mem(fastq_r1, fastq_r2, reference, sample_id):
    """Run BWA MEM alignment from nf-core"""

    engine = NextflowEngine()
    bwa_mem = engine.load_script("modules/nf-core/bwa/mem/main.nf")

    result = engine.execute(
        bwa_mem,
        params={
            "meta": {
                "id": sample_id,
                "single_end": False
            },
            "reference": reference
        },
        input_files=[fastq_r1, fastq_r2]
    )

    # Get BAM output
    outputs = result.get_output_files()
    bam_file = next(f for f in outputs if f.endswith(".bam"))

    return bam_file

# Usage
bam = run_bwa_mem(
    "sample_R1.fastq.gz",
    "sample_R2.fastq.gz",
    "/data/genome.fa",
    "sample1"
)
```

#### Samtools Stats

```python
from pynf import NextflowEngine

def run_samtools_stats(bam_file, sample_id):
    """Run Samtools stats from nf-core"""

    engine = NextflowEngine()
    samtools_stats = engine.load_script("modules/nf-core/samtools/stats/main.nf")

    result = engine.execute(
        samtools_stats,
        params={
            "meta": {"id": sample_id}
        },
        input_files=[bam_file]
    )

    # Get stats file
    outputs = result.get_output_files()
    stats_file = next(f for f in outputs if f.endswith(".stats"))

    return stats_file

# Usage
stats = run_samtools_stats("aligned.bam", "sample1")
```

#### MultiQC

```python
from pynf import NextflowEngine
from pathlib import Path

def run_multiqc(input_dirs, output_name="multiqc_report"):
    """Run MultiQC from nf-core"""

    engine = NextflowEngine()
    multiqc = engine.load_script("modules/nf-core/multiqc/main.nf")

    result = engine.execute(
        multiqc,
        params={
            "meta": {"id": output_name}
        },
        input_files=input_dirs  # List of directories with QC outputs
    )

    # Get MultiQC report
    outputs = result.get_output_files()
    html_report = next(f for f in outputs if "multiqc_report.html" in f)

    return html_report

# Usage
report = run_multiqc(["fastqc_out/", "samtools_out/"])
```

### 7. Building nf-core Module Wrappers

Create reusable wrappers:

```python
from pynf import NextflowEngine
from pathlib import Path
from typing import Dict, List, Optional

class NFCoreModule:
    """Base class for nf-core module wrappers"""

    def __init__(self, module_name: str, module_dir: str = "modules"):
        self.module_name = module_name
        self.module_path = Path(module_dir) / "nf-core" / module_name / "main.nf"
        self.engine = NextflowEngine()

        if not self.module_path.exists():
            raise FileNotFoundError(
                f"Module not found: {self.module_path}\n"
                f"Download with: nf-core modules install {module_name}"
            )

    def run(self, input_files: List[str], meta: Dict, **params):
        """Execute module"""

        all_params = {"meta": meta}
        all_params.update(params)

        result = self.engine.execute(
            self.engine.load_script(str(self.module_path)),
            params=all_params,
            input_files=input_files
        )

        return result.get_output_files()

class FASTQCModule(NFCoreModule):
    """FASTQC module wrapper"""

    def __init__(self):
        super().__init__("fastqc")

    def run(self, fastq_file: str, sample_id: str):
        """Run FASTQC on single file"""

        meta = {"id": sample_id}
        outputs = super().run([fastq_file], meta)

        return {
            "html": next(f for f in outputs if f.endswith(".html")),
            "zip": next(f for f in outputs if f.endswith(".zip"))
        }

class BWAMemModule(NFCoreModule):
    """BWA MEM module wrapper"""

    def __init__(self):
        super().__init__("bwa/mem")

    def run(self, fastq_r1: str, fastq_r2: str, reference: str, sample_id: str):
        """Run BWA MEM alignment"""

        meta = {
            "id": sample_id,
            "single_end": False
        }

        outputs = super().run(
            [fastq_r1, fastq_r2],
            meta,
            reference=reference
        )

        return next(f for f in outputs if f.endswith(".bam"))

# Usage
fastqc = FASTQCModule()
qc_result = fastqc.run("sample.fastq.gz", "sample1")
print(f"QC report: {qc_result['html']}")

bwa = BWAMemModule()
bam = bwa.run("R1.fq.gz", "R2.fq.gz", "genome.fa", "sample1")
print(f"Aligned BAM: {bam}")
```

### 8. Complete nf-core Pipeline Example

Full RNA-seq pipeline using nf-core modules:

```python
from pynf import NextflowEngine
import pandas as pd
from pathlib import Path

class NFCoreRNASeqPipeline:
    """RNA-seq pipeline using nf-core modules"""

    def __init__(self, modules_dir="modules"):
        self.engine = NextflowEngine()
        self.modules_dir = Path(modules_dir)

    def _load_module(self, module_name):
        """Load nf-core module"""
        module_path = self.modules_dir / "nf-core" / module_name / "main.nf"
        return self.engine.load_script(str(module_path))

    def fastqc(self, fastq_file, sample_id):
        """Quality control"""
        print(f"Running FASTQC on {sample_id}...")

        result = self.engine.execute(
            self._load_module("fastqc"),
            params={"meta": {"id": sample_id}},
            input_files=[fastq_file]
        )

        return result.get_output_files()

    def trim_galore(self, fastq_r1, fastq_r2, sample_id):
        """Trim adapters"""
        print(f"Trimming {sample_id}...")

        result = self.engine.execute(
            self._load_module("trimgalore"),
            params={
                "meta": {"id": sample_id, "single_end": False},
                "quality": 20,
                "length": 50
            },
            input_files=[fastq_r1, fastq_r2]
        )

        outputs = result.get_output_files()
        trimmed_r1 = next(f for f in outputs if "R1" in f and f.endswith(".fq.gz"))
        trimmed_r2 = next(f for f in outputs if "R2" in f and f.endswith(".fq.gz"))

        return trimmed_r1, trimmed_r2

    def star_align(self, fastq_r1, fastq_r2, genome_index, sample_id):
        """Align with STAR"""
        print(f"Aligning {sample_id}...")

        result = self.engine.execute(
            self._load_module("star/align"),
            params={
                "meta": {"id": sample_id, "single_end": False},
                "genome_index": genome_index
            },
            input_files=[fastq_r1, fastq_r2]
        )

        outputs = result.get_output_files()
        bam = next(f for f in outputs if f.endswith("Aligned.sortedByCoord.out.bam"))

        return bam

    def featurecounts(self, bam_file, gtf, sample_id):
        """Count features"""
        print(f"Counting features for {sample_id}...")

        result = self.engine.execute(
            self._load_module("subread/featurecounts"),
            params={
                "meta": {"id": sample_id},
                "gtf": gtf
            },
            input_files=[bam_file]
        )

        outputs = result.get_output_files()
        counts = next(f for f in outputs if f.endswith(".counts.txt"))

        return counts

    def run_sample(self, sample_info, genome_index, gtf):
        """Run complete pipeline for one sample"""

        sample_id = sample_info["sample_id"]
        fastq_r1 = sample_info["fastq_r1"]
        fastq_r2 = sample_info["fastq_r2"]

        # QC
        qc_files = self.fastqc(fastq_r1, sample_id)

        # Trim
        trimmed_r1, trimmed_r2 = self.trim_galore(fastq_r1, fastq_r2, sample_id)

        # Align
        bam = self.star_align(trimmed_r1, trimmed_r2, genome_index, sample_id)

        # Count
        counts = self.featurecounts(bam, gtf, sample_id)

        return {
            "sample_id": sample_id,
            "qc_files": qc_files,
            "bam": bam,
            "counts": counts
        }

    def run_cohort(self, samples_csv, genome_index, gtf):
        """Run pipeline on all samples"""

        samples_df = pd.read_csv(samples_csv)
        results = []

        for _, row in samples_df.iterrows():
            result = self.run_sample(row.to_dict(), genome_index, gtf)
            results.append(result)

        return pd.DataFrame(results)

# Usage
pipeline = NFCoreRNASeqPipeline()

results = pipeline.run_cohort(
    "samples.csv",
    genome_index="/data/genomes/hg38_star",
    gtf="/data/annotations/genes.gtf"
)

print(results)
```

## Troubleshooting

### Module Not Found

```python
# Check if module exists
from pathlib import Path

module_path = Path("modules/nf-core/fastqc/main.nf")
if not module_path.exists():
    print(f"Module not found at {module_path}")
    print("Download with: nf-core modules install fastqc")
```

### Container Requirements

Some nf-core modules require containers:

```bash
# Check module requirements
cat modules/nf-core/fastqc/main.nf | grep container

# For now, ensure tools are installed locally
# Container support coming in future py-nf versions
```

### Meta Map Issues

```python
# Ensure meta map has required fields
def validate_meta(meta, required_fields=["id"]):
    """Validate meta map"""
    for field in required_fields:
        if field not in meta:
            raise ValueError(f"Meta map missing required field: {field}")
    return True

meta = {"id": "sample1", "single_end": False}
validate_meta(meta)
```

## Best Practices

1. **Download once**: Cache modules locally, don't re-download
2. **Use wrappers**: Create wrapper classes for frequently used modules
3. **Validate inputs**: Check meta maps and file existence
4. **Handle outputs**: Parse outputs specific to each module
5. **Document meta**: Keep track of required meta fields per module
6. **Version control**: Track which module versions you're using

## Related Skills

- **run-nextflow-module**: Basic module execution
- **batch-process-with-nextflow**: Process multiple samples with nf-core modules
- **integrate-nextflow-pipeline**: Build pipelines with nf-core modules
