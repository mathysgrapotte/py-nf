# integrate-nextflow-pipeline

## Description

Embed Nextflow modules into larger Python data science workflows, combining bioinformatics tools with pandas, scikit-learn, visualization libraries, and custom Python code. This skill helps users build hybrid pipelines that leverage both Nextflow's workflow management and Python's data analysis ecosystem.

## When to Use

Use this skill when you need to:
- **Mix Nextflow and Python** processing steps
- **Integrate** bioinformatics tools into data science pipelines
- **Chain** Nextflow modules with Python analysis
- **Combine** workflow management with interactive analysis
- **Build** end-to-end pipelines in Jupyter notebooks
- **Leverage** both ecosystems in production workflows

## Keywords

pipeline integration, hybrid workflows, data science, pandas, scikit-learn, jupyter, mixed pipelines

## Instructions

When a user wants to integrate Nextflow modules into Python workflows, guide them through these patterns:

### 1. Basic Integration Pattern

Nextflow as one step in Python pipeline:

```python
from pynf import NextflowEngine
import pandas as pd

def my_python_pipeline(input_data):
    """Hybrid pipeline mixing Python and Nextflow"""

    # Step 1: Python data preprocessing
    print("Step 1: Python preprocessing...")
    df = pd.read_csv(input_data)
    clean_df = df.dropna()
    clean_df.to_csv("clean_data.csv", index=False)

    # Step 2: Nextflow bioinformatics processing
    print("Step 2: Nextflow tool execution...")
    engine = NextflowEngine()
    result = engine.execute(
        engine.load_script("modules/analysis.nf"),
        input_files=["clean_data.csv"]
    )
    analysis_output = result.get_output_files()[0]

    # Step 3: Python post-processing
    print("Step 3: Python analysis...")
    results_df = pd.read_csv(analysis_output)
    summary = results_df.describe()

    return summary

# Run pipeline
summary = my_python_pipeline("raw_data.csv")
print(summary)
```

### 2. Chaining Multiple Nextflow Modules

Connect Nextflow modules with Python glue code:

```python
from pynf import NextflowEngine
from pathlib import Path

class MultiStepPipeline:
    def __init__(self):
        self.engine = NextflowEngine()
        self.intermediate_files = {}

    def step1_quality_control(self, input_fastq):
        """QC with Nextflow, return QC metrics"""
        print("Running quality control...")

        result = self.engine.execute(
            self.engine.load_script("modules/fastqc.nf"),
            input_files=[input_fastq]
        )

        qc_files = result.get_output_files()
        self.intermediate_files["qc"] = qc_files

        # Parse QC metrics in Python
        qc_report = next(f for f in qc_files if f.endswith("_data.txt"))
        metrics = self._parse_qc_report(qc_report)

        return metrics

    def step2_trimming(self, input_fastq, qc_metrics):
        """Trim based on QC metrics"""
        print("Trimming adapters...")

        # Use QC metrics to set trimming params
        min_length = 50 if qc_metrics["mean_length"] > 100 else 30

        result = self.engine.execute(
            self.engine.load_script("modules/trim.nf"),
            params={"min_length": min_length},
            input_files=[input_fastq]
        )

        trimmed_fastq = result.get_output_files()[0]
        self.intermediate_files["trimmed"] = trimmed_fastq

        return trimmed_fastq

    def step3_alignment(self, trimmed_fastq, reference):
        """Align trimmed reads"""
        print("Aligning reads...")

        result = self.engine.execute(
            self.engine.load_script("modules/bwa_align.nf"),
            params={"reference": reference},
            input_files=[trimmed_fastq]
        )

        bam_file = next(f for f in result.get_output_files() if f.endswith(".bam"))
        return bam_file

    def _parse_qc_report(self, report_file):
        """Parse FASTQC report (Python)"""
        # Implementation...
        return {"mean_length": 150, "quality_score": 35}

    def run_pipeline(self, input_fastq, reference):
        """Execute complete pipeline"""
        qc_metrics = self.step1_quality_control(input_fastq)
        trimmed = self.step2_trimming(input_fastq, qc_metrics)
        bam = self.step3_alignment(trimmed, reference)

        return {
            "qc_metrics": qc_metrics,
            "aligned_bam": bam,
            "intermediates": self.intermediate_files
        }

# Usage
pipeline = MultiStepPipeline()
results = pipeline.run_pipeline(
    "sample.fastq.gz",
    "/data/genome.fa"
)
```

### 3. Integrating with Pandas DataFrames

Use DataFrame rows to drive Nextflow execution:

```python
import pandas as pd
from pynf import NextflowEngine

def process_dataframe_with_nextflow(df, module_path, input_col, output_col):
    """
    Apply Nextflow module to DataFrame rows

    Args:
        df: DataFrame with input file paths
        module_path: Path to Nextflow module
        input_col: Column containing input file paths
        output_col: Column name for outputs
    """

    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    outputs = []

    for idx, row in df.iterrows():
        input_file = row[input_col]

        result = engine.execute(
            script_path,
            params={"sample_id": row.get("sample_id", f"sample_{idx}")},
            input_files=[input_file]
        )

        output_files = result.get_output_files()
        outputs.append(output_files[0] if output_files else None)

    # Add outputs as new column
    df[output_col] = outputs

    return df

# Example usage
samples_df = pd.read_csv("samples.csv")
# Columns: sample_id, fastq_file, condition

# Add QC results column
samples_df = process_dataframe_with_nextflow(
    samples_df,
    "modules/fastqc.nf",
    input_col="fastq_file",
    output_col="qc_report"
)

# Now analyze with pandas
summary = samples_df.groupby("condition")["qc_report"].count()
print(summary)
```

### 4. Integration with Scikit-learn Pipelines

Create sklearn-compatible transformer wrapping Nextflow:

```python
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from pynf import NextflowEngine
import numpy as np

class NextflowFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    Scikit-learn transformer that runs Nextflow module
    for feature extraction
    """

    def __init__(self, module_path, feature_parser=None):
        self.module_path = module_path
        self.feature_parser = feature_parser
        self.engine = NextflowEngine()

    def fit(self, X, y=None):
        """Fit does nothing - Nextflow module is pre-defined"""
        return self

    def transform(self, X):
        """
        X is array-like of input file paths
        Returns: feature matrix
        """
        script_path = self.engine.load_script(self.module_path)

        features = []

        for input_file in X:
            # Run Nextflow module
            result = self.engine.execute(
                script_path,
                input_files=[input_file]
            )

            # Extract features from outputs
            output_file = result.get_output_files()[0]

            if self.feature_parser:
                feature_vec = self.feature_parser(output_file)
            else:
                feature_vec = self._default_parser(output_file)

            features.append(feature_vec)

        return np.array(features)

    def _default_parser(self, output_file):
        """Default feature extraction"""
        import pandas as pd
        df = pd.read_csv(output_file)
        return df.iloc[0].values  # Use first row as features

# Create ML pipeline with Nextflow step
def custom_feature_parser(output_file):
    """Parse Nextflow output into feature vector"""
    import pandas as pd
    df = pd.read_csv(output_file)
    return df["feature_col"].values

pipeline = Pipeline([
    ("extract_features", NextflowFeatureExtractor(
        "modules/extract_features.nf",
        feature_parser=custom_feature_parser
    )),
    ("classifier", RandomForestClassifier())
])

# Train on file paths
input_files = ["sample1.bam", "sample2.bam", "sample3.bam"]
labels = [0, 1, 0]

pipeline.fit(input_files, labels)

# Predict on new files
predictions = pipeline.predict(["new_sample.bam"])
```

### 5. Jupyter Notebook Integration

Use Nextflow in interactive notebooks:

```python
# Jupyter Notebook Cell 1: Setup
from pynf import NextflowEngine
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML, display

engine = NextflowEngine()

# Jupyter Notebook Cell 2: Load Data
samples_df = pd.read_csv("samples.csv")
display(samples_df.head())

# Jupyter Notebook Cell 3: Run Nextflow Analysis
print("Running analysis on all samples...")

results = []
for _, row in samples_df.iterrows():
    result = engine.execute(
        engine.load_script("modules/analysis.nf"),
        params={"sample_id": row["sample_id"]},
        input_files=[row["input_file"]]
    )

    outputs = result.get_output_files()
    results.append({
        "sample_id": row["sample_id"],
        "output": outputs[0]
    })

results_df = pd.DataFrame(results)

# Jupyter Notebook Cell 4: Parse Results
def parse_analysis_output(output_file):
    """Parse Nextflow output"""
    df = pd.read_csv(output_file)
    return df["metric"].mean()

results_df["metric"] = results_df["output"].apply(parse_analysis_output)

# Jupyter Notebook Cell 5: Visualize
plt.figure(figsize=(10, 6))
plt.bar(results_df["sample_id"], results_df["metric"])
plt.xlabel("Sample")
plt.ylabel("Metric")
plt.title("Analysis Results")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Jupyter Notebook Cell 6: Generate Report
for _, row in results_df.iterrows():
    print(f"\nSample: {row['sample_id']}")
    print(f"Metric: {row['metric']:.2f}")
```

### 6. Integration with Visualization

Combine Nextflow outputs with plotting libraries:

```python
from pynf import NextflowEngine
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def run_analysis_and_visualize(samples, module_path):
    """Run Nextflow analysis and generate plots"""

    # Run Nextflow processing
    engine = NextflowEngine()
    script_path = engine.load_script(module_path)

    results = []
    for sample in samples:
        result = engine.execute(
            script_path,
            params={"sample_name": sample["name"]},
            input_files=[sample["input"]]
        )

        # Parse output
        output_file = result.get_output_files()[0]
        df = pd.read_csv(output_file)

        results.append({
            "sample": sample["name"],
            "condition": sample["condition"],
            "mean_value": df["value"].mean(),
            "std_value": df["value"].std()
        })

    results_df = pd.DataFrame(results)

    # Create visualizations
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))

    # Plot 1: Bar plot by sample
    sns.barplot(
        data=results_df,
        x="sample",
        y="mean_value",
        hue="condition",
        ax=axes[0]
    )
    axes[0].set_title("Mean Values by Sample")
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=45)

    # Plot 2: Box plot by condition
    sns.boxplot(
        data=results_df,
        x="condition",
        y="mean_value",
        ax=axes[1]
    )
    axes[1].set_title("Distribution by Condition")

    plt.tight_layout()
    plt.savefig("analysis_results.png")
    plt.show()

    return results_df

# Usage
samples = [
    {"name": "sample1", "input": "data1.txt", "condition": "control"},
    {"name": "sample2", "input": "data2.txt", "condition": "treated"},
]

results = run_analysis_and_visualize(samples, "modules/analyze.nf")
```

### 7. Building Production Pipelines

Production-ready hybrid pipeline:

```python
from pynf import NextflowEngine
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionPipeline:
    """Production pipeline integrating Nextflow and Python"""

    def __init__(self, config_file: str):
        with open(config_file) as f:
            self.config = json.load(f)

        self.engine = NextflowEngine()
        self.results = []

    def validate_inputs(self, input_df: pd.DataFrame) -> bool:
        """Validate input DataFrame"""
        required_cols = ["sample_id", "input_file", "condition"]

        for col in required_cols:
            if col not in input_df.columns:
                logger.error(f"Missing required column: {col}")
                return False

        # Check files exist
        for _, row in input_df.iterrows():
            if not Path(row["input_file"]).exists():
                logger.error(f"Input file not found: {row['input_file']}")
                return False

        return True

    def preprocessing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Python preprocessing step"""
        logger.info("Running preprocessing...")

        # Quality filters
        df = df[df["quality_score"] >= self.config["min_quality"]]

        # Normalization
        df["normalized_value"] = df["raw_value"] / df["raw_value"].max()

        logger.info(f"Preprocessing complete: {len(df)} samples passed filters")
        return df

    def nextflow_processing(self, df: pd.DataFrame, module: str) -> pd.DataFrame:
        """Nextflow processing step"""
        logger.info(f"Running Nextflow module: {module}")

        script_path = self.engine.load_script(f"modules/{module}.nf")

        outputs = []

        for idx, row in df.iterrows():
            try:
                result = self.engine.execute(
                    script_path,
                    params={
                        "sample_id": row["sample_id"],
                        **self.config.get("nextflow_params", {})
                    },
                    input_files=[row["input_file"]]
                )

                output_files = result.get_output_files()
                outputs.append(output_files[0] if output_files else None)

                logger.info(f"Processed {row['sample_id']}")

            except Exception as e:
                logger.error(f"Failed to process {row['sample_id']}: {e}")
                outputs.append(None)

        df["nextflow_output"] = outputs
        return df

    def postprocessing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Python postprocessing step"""
        logger.info("Running postprocessing...")

        # Parse Nextflow outputs
        parsed_results = []

        for _, row in df.iterrows():
            if row["nextflow_output"] is None:
                continue

            output_df = pd.read_csv(row["nextflow_output"])
            parsed_results.append({
                "sample_id": row["sample_id"],
                "condition": row["condition"],
                "result_metric": output_df["metric"].mean()
            })

        results_df = pd.DataFrame(parsed_results)

        # Statistical analysis
        summary = results_df.groupby("condition")["result_metric"].agg([
            "mean", "std", "count"
        ])

        logger.info("Postprocessing complete")
        return results_df, summary

    def run(self, input_csv: str, output_dir: str) -> Dict:
        """Execute complete pipeline"""
        logger.info(f"Starting pipeline: {input_csv}")

        # Load inputs
        input_df = pd.read_csv(input_csv)

        # Validate
        if not self.validate_inputs(input_df):
            raise ValueError("Input validation failed")

        # Run pipeline steps
        preprocessed_df = self.preprocessing(input_df)

        processed_df = self.nextflow_processing(
            preprocessed_df,
            self.config["nextflow_module"]
        )

        results_df, summary = self.postprocessing(processed_df)

        # Save outputs
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        results_df.to_csv(output_path / "results.csv", index=False)
        summary.to_csv(output_path / "summary.csv")

        logger.info(f"Pipeline complete. Results in {output_dir}")

        return {
            "results": results_df,
            "summary": summary,
            "output_dir": str(output_path)
        }

# Configuration file (pipeline_config.json):
# {
#   "min_quality": 30,
#   "nextflow_module": "analysis",
#   "nextflow_params": {
#     "threads": 8,
#     "threshold": 0.05
#   }
# }

# Usage
pipeline = ProductionPipeline("pipeline_config.json")
results = pipeline.run("samples.csv", "results/")
```

## Complete Example Workflows

### Example 1: Variant Analysis Pipeline

```python
"""
Complete variant analysis combining Nextflow tools and Python analysis
"""
from pynf import NextflowEngine
import pandas as pd
import matplotlib.pyplot as plt

class VariantPipeline:
    def __init__(self):
        self.engine = NextflowEngine()

    def align_reads(self, sample_df):
        """Align with Nextflow"""
        align_module = self.engine.load_script("modules/bwa_align.nf")

        bams = []
        for _, row in sample_df.iterrows():
            result = self.engine.execute(
                align_module,
                params={"sample_id": row["sample_id"]},
                input_files=[row["fastq_r1"], row["fastq_r2"]]
            )
            bam = next(f for f in result.get_output_files() if f.endswith(".bam"))
            bams.append(bam)

        sample_df["bam"] = bams
        return sample_df

    def call_variants(self, sample_df):
        """Call variants with Nextflow"""
        caller = self.engine.load_script("modules/call_variants.nf")

        vcfs = []
        for _, row in sample_df.iterrows():
            result = self.engine.execute(
                caller,
                input_files=[row["bam"]]
            )
            vcf = next(f for f in result.get_output_files() if f.endswith(".vcf"))
            vcfs.append(vcf)

        sample_df["vcf"] = vcfs
        return sample_df

    def analyze_variants(self, sample_df):
        """Analyze with Python"""
        import cyvcf2

        analysis = []
        for _, row in sample_df.iterrows():
            vcf = cyvcf2.VCF(row["vcf"])

            # Count variants
            num_snps = sum(1 for v in vcf if v.is_snp)
            num_indels = sum(1 for v in vcf if v.is_indel)

            analysis.append({
                "sample_id": row["sample_id"],
                "num_snps": num_snps,
                "num_indels": num_indels,
                "total_variants": num_snps + num_indels
            })

        return pd.DataFrame(analysis)

    def visualize_results(self, analysis_df):
        """Create plots"""
        fig, ax = plt.subplots(figsize=(10, 6))

        analysis_df.plot(
            x="sample_id",
            y=["num_snps", "num_indels"],
            kind="bar",
            stacked=True,
            ax=ax
        )

        ax.set_title("Variant Counts by Sample")
        ax.set_ylabel("Count")
        plt.tight_layout()
        plt.savefig("variant_analysis.png")

    def run(self, samples_csv):
        """Run complete pipeline"""
        samples_df = pd.read_csv(samples_csv)

        print("Step 1: Aligning reads...")
        samples_df = self.align_reads(samples_df)

        print("Step 2: Calling variants...")
        samples_df = self.call_variants(samples_df)

        print("Step 3: Analyzing variants...")
        analysis_df = self.analyze_variants(samples_df)

        print("Step 4: Visualizing results...")
        self.visualize_results(analysis_df)

        return analysis_df

# Run pipeline
pipeline = VariantPipeline()
results = pipeline.run("samples.csv")
print(results)
```

## Best Practices

1. **Keep Nextflow modules focused**: Small, single-purpose modules
2. **Use Python for glue logic**: Connect modules with Python code
3. **Validate at boundaries**: Check inputs/outputs between stages
4. **Handle errors gracefully**: Try/except around Nextflow execution
5. **Log extensively**: Track progress through hybrid pipeline
6. **Structure as classes**: Organize multi-step pipelines as classes
7. **Make it configurable**: Use config files for parameters

## Related Skills

- **run-nextflow-module**: Basic Nextflow execution
- **batch-process-with-nextflow**: Process multiple samples
- **convert-nextflow-to-python**: Convert existing workflows
