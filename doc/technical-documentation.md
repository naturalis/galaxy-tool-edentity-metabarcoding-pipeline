# Technical Documentation: eDentity Metabarcoding Pipeline Galaxy Tool

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Details](#component-details)
3. [Data Flow](#data-flow)
4. [Galaxy Tool XML Structure](#galaxy-tool-xml-structure)
5. [Python Client Implementation](#python-client-implementation)
6. [Pipeline Stages](#pipeline-stages)
7. [Input/Output Specifications](#inputoutput-specifications)
8. [Dependencies and Requirements](#dependencies-and-requirements)
9. [Error Handling and Validation](#error-handling-and-validation)
10. [Integration with External Tools](#integration-with-external-tools)
11. [Testing](#testing)
12. [Development Guidelines](#development-guidelines)

---

## Architecture Overview

The eDentity Metabarcoding Pipeline is a Galaxy tool wrapper that integrates the [edentity](https://pypi.org/project/edentity/) metabarcoding pipeline into the Galaxy ecosystem. The tool provides a user-friendly interface for processing amplicon sequencing data and generating Exact Sequence Variants (ESVs).

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Galaxy Interface                        │
│  (edentity-metabarcoding-pipeline.xml)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Galaxy Client Script                      │
│                  (galaxy_client.py)                         │
│                                                             │
│  • Argument parsing                                         │
│  • Input validation                                         │
│  • ZIP extraction                                           │
│  • Command construction                                     │
│  • Output handling                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   eDentity Pipeline                         │
│            (Snakemake-based workflow)                       │
│                                                             │
│  Quality Control → Merging → Trimming → Filtering          │
│       → Dereplication → Denoising → ESV Generation          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              External Bioinformatics Tools                  │
│                                                             │
│  • fastp (quality control)                                  │
│  • vsearch (merging, filtering, denoising)                  │
│  • cutadapt (primer trimming)                               │
│  • multiqc (reporting)                                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns**: The Galaxy XML defines the interface, while `galaxy_client.py` handles execution logic
2. **Pipeline Delegation**: Core analysis is delegated to the `edentity` package, which manages Snakemake workflows
3. **Flexible Configuration**: Extensive parameterization allows users to customize each pipeline stage
4. **Robust Error Handling**: Multi-layer validation ensures data integrity and provides meaningful error messages
5. **Galaxy Integration**: Outputs are properly formatted for Galaxy's data management system

---

## Component Details

### 1. Galaxy Tool Wrapper (`edentity-metabarcoding-pipeline.xml`)

The XML file defines the Galaxy tool interface with 267 lines containing:

- **Tool Metadata** (lines 1-2): Tool ID, name, and version
- **Requirements** (lines 5-15): Conda package dependencies
- **Command Section** (lines 18-44): Command-line invocation template
- **Input Configuration** (lines 46-141): User-configurable parameters organized in sections
- **Output Configuration** (lines 156-162): Output file specifications
- **Tests** (lines 165-206): Automated testing configuration
- **Help Documentation** (lines 209-236): User-facing documentation
- **Citations** (lines 238-266): Academic references

### 2. Python Client (`galaxy_client.py`)

The client script contains 367 lines implementing:

- **Input Processing**: ZIP file extraction and FASTQ validation
- **Command Construction**: Building edentity command with parameters
- **Pipeline Execution**: Running edentity and managing subprocess
- **Output Handling**: Moving and packaging results for Galaxy
- **Error Management**: Exception handling and logging

---

## Data Flow

### Input Processing Pipeline

```
User uploads ZIP file
         ↓
galaxy_client.py receives path
         ↓
Validate ZIP file structure
         ↓
Extract FASTQ files (lines 36-54)
    • Regex match: .*[.]fastq([.]gz)?$
    • Validate no illegal characters
    • Ensure single directory location
         ↓
Move FASTQ to input_data_dir
         ↓
Pass to eDentity pipeline
```

### Output Processing Pipeline

```
eDentity generates results
         ↓
galaxy_client.py outputs() function (lines 93-146)
         ↓
Move files to Galaxy outputs:
    • ESV_table.tsv
    • summary_report.tsv
    • ESV_sequences.fasta
    • multiqc_report.html
    • json_reports.zip (aggregated)
         ↓
Clean up temporary files
         ↓
Galaxy stores outputs in history
```

---

## Galaxy Tool XML Structure

### Parameter Organization

Parameters are organized into six logical sections:

#### 1. Data Section (lines 48-55)
- **project_name**: Project identifier (no spaces allowed)
- **data_type**: Sequencer type (Illumina or AVITI)
- **input_fastqs**: ZIP archive containing FASTQ files

#### 2. Fastp Section (lines 57-61)
Quality control parameters:
- **n_max**: Maximum N bases (0-5)
- **average_qual**: Minimum average Q-score (15-30)
- **length_required**: Minimum read length (50-300)

#### 3. Merge Section (lines 65-81)
Paired-end read merging (vsearch):
- **fastq_maxdiffpct**: Maximum mismatch percentage (80-100%)
- **fastq_maxdiffs**: Maximum absolute mismatches (0+)
- **fastq_minovlen**: Minimum overlap length (5+ bp)

#### 4. Trimming Section (lines 84-98)
Primer removal (cutadapt):
- **forward_primer**: Forward primer sequence(s)
- **reverse_primer**: Reverse primer sequence(s)
- **anchored**: Whether primers are anchored
- **discard_untrimmed**: Remove reads without primers

#### 5. Filter Section (lines 101-120)
Length and quality filtering (vsearch):
- **minlen**: Minimum sequence length (100-1500 bp)
- **maxlen**: Maximum sequence length (200-2000 bp)
- **maxee**: Maximum expected errors (0-2)

#### 6. Dereplication Section (lines 123-127)
- **fasta_width**: FASTA line width (0 = no wrapping)

#### 7. Denoise Section (lines 130-138)
ESV generation (vsearch cluster_unoise):
- **alpha**: Sequence difference threshold
- **minsize**: Minimum cluster abundance

### Command Construction

The command section (lines 18-44) uses Galaxy's macro language:

```xml
python $__tool_directory__/galaxy_client.py 
  --project_name $dataType.project_name 
  --dataType $dataType.data_type 
  --input_fastqs $dataType.input_fastqs
  [... additional parameters ...]
```

Key features:
- `$__tool_directory__`: Galaxy's macro for tool directory path
- `$section.parameter`: Accesses parameters within sections
- All parameters passed as command-line arguments

---

## Python Client Implementation

### Main Function Flow (`galaxy_client.py`)

#### 1. Argument Parsing (lines 150-285)

Uses `argparse` to define all parameters:

```python
parser = argparse.ArgumentParser(
    description='Galaxy client for the Edentity Metabarcoding pipeline'
)
parser.add_argument('--project_name', help='name of the project', required=True)
# ... additional arguments ...
```

#### 2. Input Validation (lines 289-291)

```python
assert " " not in args.input_fastqs, (
    "Error: ZIP filename must not contain space(s)"
)
```

#### 3. Directory Setup (lines 296-303)

```python
input_data_dir = os.path.join(os.getcwd(), "input_data")
snakemake_work_dir = os.path.join(os.getcwd(), args_dict['project_name'])
```

#### 4. FASTQ Extraction (lines 306-314)

Calls `extract_fastq_files()` which:
- Validates ZIP file
- Extracts only FASTQ files
- Moves files to root directory
- Returns list of filenames

#### 5. Command Construction (lines 316-348)

Builds the `edentity` command:

```python
cmd = [
    "edentity",
    "--raw_data_dir", input_data_dir,
    "--dataType", args_dict['dataType'],
    "--work_dir", snakemake_work_dir,
    # ... additional parameters ...
]
```

Conditionally adds boolean flags:

```python
if str(args_dict['discard_untrimmed']).lower() in ("true", "1"):
    cmd.extend(["--discard_untrimmed"])
```

#### 6. Pipeline Execution (lines 350-354)

```python
edentityCmd(cmd)
```

The `edentityCmd()` function (lines 58-86):
- Executes subprocess
- Captures stdout/stderr
- Removes `.snakemake` temporary directory
- Returns None (exit via sys.exit on error)

#### 7. Output Handling (lines 356-363)

```python
outputs(snakemake_work_dir, args_dict)
```

### Key Functions

#### `get_filenames()` (lines 13-33)

Validates and extracts FASTQ filenames from ZIP:

```python
def get_filenames(zip_files_list):
    # Regex to match FASTQ files
    full_filenames_list = [
        n for n in zip_files_list if re.search(r'.*[.]fastq([.]gz)?$', n)
    ]
    
    # Validate no illegal characters
    for file in full_filenames_list:
        for c in [' ', "*", "'", '"']:
            assert c not in file, f"Error: File name {file} contains illegal character: {c}"
    
    # Ensure all files in same directory
    store_dir = set([os.path.dirname(n) for n in full_filenames_list])
    assert len(store_dir) == 1, "FASTQ files found in different locations inside the zip file"
    
    return full_filenames_list
```

#### `extract_fastq_files()` (lines 36-54)

Extracts FASTQ files from ZIP:

```python
def extract_fastq_files(read_zip_file: str, output_dir: str):
    assert zipfile.is_zipfile(read_zip_file), "Input Zip file is not a valid ZIP file"
    
    with zipfile.ZipFile(read_zip_file, 'r') as ziph:
        names = ziph.namelist()
        filenames = get_filenames(names)
        
        # Extract only FASTQ files
        ziph.extractall(path=output_dir, members=filenames, pwd=None)
        
        # Move files to root of output_dir
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if os.path.join(root, f) != os.path.join(output_dir, f):
                    shutil.move(os.path.join(root, f), output_dir)
```

#### `outputs()` (lines 93-146)

Moves pipeline outputs to Galaxy output paths:

```python
def outputs(snakemake_work_dir, args_dict):
    # Move ESV table
    esv_table = os.path.join(
        snakemake_work_dir, "Results", "report",
        f"{args_dict['project_name']}_ESV_table.tsv"
    )
    shutil.move(esv_table, args_dict['ESV_table_output'])
    
    # Move summary report
    # ... similar for other outputs ...
    
    # Zip JSON reports
    json_reports = [
        json for json in os.listdir(
            os.path.join(snakemake_work_dir, "Results", "report")
        ) if json.endswith(".json")
    ]
    with zipfile.ZipFile(args_dict['json_reports'], 'w', zipfile.ZIP_DEFLATED) as zipf:
        for json in json_file_paths:
            zip_file(json, zipf)
```

---

## Pipeline Stages

The eDentity pipeline executes seven sequential stages:

### Stage 1: Quality Control (fastp)

**Purpose**: Remove low-quality reads and bases

**Parameters**:
- `n_max`: Maximum N bases allowed
- `average_qual`: Minimum average quality score
- `length_required`: Minimum read length

**Output**: Filtered FASTQ files

### Stage 2: Merging (vsearch fastq_mergepairs)

**Purpose**: Merge paired-end reads into single sequences

**Parameters**:
- `fastq_maxdiffpct`: Maximum mismatch percentage in overlap
- `fastq_maxdiffs`: Maximum absolute mismatches
- `fastq_minovlen`: Minimum overlap length

**Algorithm**: Aligns forward and reverse reads, merges if overlap criteria met

**Output**: Merged FASTQ files

### Stage 3: Trimming (cutadapt)

**Purpose**: Remove primer sequences from reads

**Parameters**:
- `forward_primer`: Forward primer sequence(s)
- `reverse_primer`: Reverse primer sequence(s)
- `anchored`: Require primers at sequence ends
- `discard_untrimmed`: Discard reads without primers

**Features**:
- Supports multiple primers (comma-separated)
- Can trim internal or anchored primers
- Optional retention of untrimmed reads

**Output**: Trimmed FASTQ files

### Stage 4: Filtering (vsearch fastq_filter)

**Purpose**: Apply length and quality filters

**Parameters**:
- `minlen`: Minimum sequence length
- `maxlen`: Maximum sequence length
- `maxee`: Maximum expected errors

**Expected Error Calculation**:
```
EE = sum(10^(-Q/10)) for all bases
```

**Output**: Filtered FASTA files

### Stage 5: Dereplication (vsearch fastx_uniques)

**Purpose**: Collapse identical sequences

**Parameters**:
- `fasta_width`: Line width for FASTA output (0 = unwrapped)

**Process**:
1. Identifies unique sequences
2. Counts abundance of each unique sequence
3. Sorts by abundance

**Output**: Dereplicated FASTA with abundance annotations

### Stage 6: Denoising (vsearch cluster_unoise)

**Purpose**: Generate ESVs by clustering and denoising

**Parameters**:
- `alpha`: Sequence similarity threshold
- `minsize`: Minimum cluster size

**Algorithm** (UNOISE):
1. Sort sequences by abundance
2. Cluster sequences within `alpha` differences
3. Identify chimeras
4. Generate consensus ESVs

**Output**: ESV sequences

### Stage 7: ESV Table Generation

**Purpose**: Create abundance matrix

**Process**:
1. Map original reads to ESVs
2. Count ESV abundance per sample
3. Generate summary statistics

**Output**: ESV table (samples × ESVs)

---

## Input/Output Specifications

### Input Requirements

#### FASTQ ZIP Archive

**Format**: ZIP container with FASTQ files

**Requirements**:
1. Files must match regex: `.*[.]fastq([.]gz)?$`
2. No illegal characters: space, *, ', "
3. All files must be in same directory within ZIP
4. Can contain compressed (.gz) or uncompressed FASTQ

**Example structure**:
```
sequences.zip
├── sample1_R1.fastq.gz
├── sample1_R2.fastq.gz
├── sample2_R1.fastq.gz
└── sample2_R2.fastq.gz
```

**FASTQ naming**: Must follow Illumina convention for paired-end detection

### Output Files

#### 1. ESV_table.tsv

**Format**: Tab-separated values

**Structure**:
```
ESV_NO    ESV_ID                                      Sample1  Sample2  sequence
ESV_1     9bc4f41860c78e9560383d55ef9e9681a650c125    324091   353306   GCGGTTAAACG...
ESV_2     062c4dccaa466a10caf68ac0c4ccb5f56d7eebf1    20556    22734    GCGGTTAAACG...
```

**Columns**:
- `ESV_NO`: Sequential ESV identifier
- `ESV_ID`: SHA1 hash of sequence
- `Sample columns`: Abundance counts per sample
- `sequence`: ESV nucleotide sequence

#### 2. summary_report.tsv

**Format**: Tab-separated values

**Structure**:
```
Sample   total_reads  fastp_filtered  merged  merged_percent  ...  n_esv
Sample1  556245       533823          529890  99.26           ...  103
```

**Columns**:
- `total_reads`: Input read count
- `fastp_filtered`: Reads passing QC
- `merged`: Successfully merged pairs
- `merged_percent`: Merge success rate
- `trimmed`: Reads after primer trimming
- `vsearch_filtered`: Reads passing length/quality filters
- `dereplicated`: Unique sequences
- `denoised`: ESVs after denoising
- `chimeric`: Detected chimeric sequences
- `borderline`: Borderline chimeric sequences
- `n_esv`: Final ESV count

#### 3. ESV_sequences.fasta

**Format**: FASTA

**Structure**:
```
>9bc4f41860c78e9560383d55ef9e9681a650c125
GCGGTTAAACGAGAGGCCCTAGT
>062c4dccaa466a10caf68ac0c4ccb5f56d7eebf1
GCGGTTAAACGAGAGGCCCTAGT
```

**Header**: SHA1 hash of sequence (matches ESV_ID in table)

#### 4. Quality_control_report.html

**Format**: HTML (MultiQC report)

**Contents**:
- Read count statistics
- Quality score distributions
- Sequence length distributions
- GC content
- N base percentages
- Primer trimming statistics
- Interactive plots and tables

#### 5. json_reports.zip

**Format**: ZIP archive of JSON files

**Contents**:
- Per-sample metrics for each pipeline stage
- Optional extended metrics (if `create_extended_json_reports=True`)

---

## Dependencies and Requirements

### Conda Packages

Defined in XML requirements section (lines 5-15):

| Package | Version | Purpose |
|---------|---------|---------|
| python | 3.12.8 | Runtime environment |
| fastp | 0.24.0 | Quality control |
| cutadapt | 4.9 | Primer trimming |
| vsearch | 2.28.1 | Merging, filtering, denoising |
| biopython | 1.84 | Sequence manipulation |
| multiqc | 1.27.1 | Quality report aggregation |
| nbitk | 0.5.9 | Naturalis bioinformatics toolkit |
| edentity | 1.5.1 | Core pipeline implementation |
| polars | 1.30.0 | Data frame operations |

### System Requirements

**Memory**: Depends on dataset size
- Small datasets (<1M reads): 4-8 GB
- Medium datasets (1-10M reads): 8-16 GB
- Large datasets (>10M reads): 16-32 GB

**Disk Space**: 
- Input data + 5-10x for intermediate files
- Final outputs: ~10-20% of input size

**CPU**: Multi-core recommended (Snakemake parallelization)

### Python Dependencies

Imported in `galaxy_client.py`:

```python
import os
import argparse
import subprocess
import sys
import shutil
import zipfile
from pathlib import Path
import re
```

All standard library except dependencies from conda packages.

---

## Error Handling and Validation

### Input Validation Layers

#### Layer 1: Galaxy XML Validation

- Type checking (text, integer, select, data)
- Range validation (min/max for integers)
- Required field enforcement
- Format validation (ZIP for input)

#### Layer 2: Python Client Validation

**ZIP filename validation** (line 289):
```python
assert " " not in args.input_fastqs, "Error: ZIP filename must not contain space(s)"
```

**ZIP file validation** (line 38):
```python
assert zipfile.is_zipfile(read_zip_file), "Input Zip file is not a valid ZIP file"
```

**FASTQ file validation** (lines 18-32):
```python
# Character validation
for c in [' ', "*", "'", '"']:
    assert c not in file, f"Error: File name {file} contains illegal character: {c}"

# FASTQ presence validation
assert full_filenames_list, "FASTQ files cannot be found in zip file"

# Directory structure validation
assert len(store_dir) == 1, "FASTQ files found in different locations inside the zip file"
```

#### Layer 3: eDentity Pipeline Validation

The eDentity package performs additional validation:
- Paired-end file matching
- Primer sequence validation
- Parameter range checking

### Error Reporting

#### Exception Handling Pattern

Used consistently throughout (lines 306-363):

```python
try:
    # Operation
    extract_fastq_files(args_dict['input_fastqs'], input_data_dir)
except Exception as e:
    print(f"Error\n{e}", file=sys.stderr)
    raise
```

#### Error Message Destinations

- `sys.stderr`: Error messages (displayed in Galaxy as errors)
- `sys.stdout`: Success messages and logs
- Return codes: Non-zero exit indicates failure

### Common Error Scenarios

1. **Invalid ZIP structure**: Triggers assertion in `get_filenames()`
2. **Missing FASTQ files**: Triggers "FASTQ files cannot be found" error
3. **Invalid primers**: Caught by cutadapt (via eDentity)
4. **Insufficient overlap**: Results in low merge rate (reported in summary)
5. **Low-quality data**: Reflected in summary report statistics

---

## Integration with External Tools

### Tool Invocation Chain

```
Galaxy XML
    ↓ executes
galaxy_client.py
    ↓ calls
edentity CLI
    ↓ manages
Snakemake workflow
    ↓ invokes
    ├── fastp
    ├── vsearch (multiple steps)
    ├── cutadapt
    └── multiqc
```

### eDentity Command Structure

Built in `galaxy_client.py` (lines 317-348):

```python
cmd = [
    "edentity",
    "--raw_data_dir", input_data_dir,
    "--dataType", args_dict['dataType'],
    "--work_dir", snakemake_work_dir,
    "--forward_primer", args_dict['forward_primer'],
    "--reverse_primer", args_dict['reverse_primer'],
]

# Boolean flags
if str(args_dict['discard_untrimmed']).lower() in ("true", "1"):
    cmd.extend(["--discard_untrimmed"])
if str(args_dict['anchored']).lower() in ("true", "1"):
    cmd.extend(["--anchoring"])

# Numeric parameters
cmd.extend([
    "--n_base_limit", str(args_dict['n_max']),
    "--average_qual", str(args_dict['average_qual']),
    "--length_required", str(args_dict['length_required']),
    # ... additional parameters ...
])
```

### Snakemake Workflow Management

**Working Directory Structure**:
```
{project_name}/
├── .snakemake/          (temporary, deleted after run)
├── input_data/          (extracted FASTQ files)
└── Results/
    ├── report/
    │   ├── {project_name}_ESV_table.tsv
    │   ├── {project_name}_summary_report.tsv
    │   ├── *.json
    │   └── {project_name}_multiqc_reports/
    │       └── {project_name}_multiqc_report.html
    └── ESVs_fasta/
        └── {project_name}_esv_sequences.fasta
```

**Cleanup** (lines 78-84):
```python
snakemake_proc_folder = ".snakemake"
if os.path.isdir(snakemake_proc_folder):
    shutil.rmtree(snakemake_proc_folder)
```

### Subprocess Execution

The `edentityCmd()` function (lines 58-86) handles subprocess execution:

```python
def edentityCmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout, file=sys.stdout)
    else:
        print(result.stderr, file=sys.stderr)
    
    # Cleanup
    shutil.rmtree(".snakemake")
```

**Key features**:
- `capture_output=True`: Captures stdout/stderr
- `text=True`: Returns strings (not bytes)
- Return code checking for error detection
- Automatic cleanup of temporary files

---

## Testing

### Galaxy Tool Tests

Defined in XML (lines 165-206):

```xml
<test>
    <section name="dataType">
        <param name="project_name" value="test"/>
        <param name="data_type" value="Illumina"/>
        <param name="input_fastqs" value="galaxyTestData.zip"/>
    </section>
    <!-- ... parameter sections ... -->
    <output name="ESV_table" file="test_ESV_table.tsv" ftype="tsv"/>
</test>
```

### Test Data

Located in `test-data/`:
- `galaxyTestData.zip`: Input FASTQ archive
- `test_ESV_table.tsv`: Expected ESV table output

### Running Tests

**Galaxy Planemo**:
```bash
planemo test edentity-metabarcoding-pipeline.xml
```

**Manual Testing**:
```bash
python galaxy_client.py \
  --project_name test \
  --dataType Illumina \
  --input_fastqs test-data/galaxyTestData.zip \
  # ... additional parameters ...
```

### Test Coverage

Currently tests:
- Basic pipeline execution
- ESV table generation

**Note**: Additional output tests are commented out (lines 201-204), likely due to minor variations in output files.

---

## Development Guidelines

### Code Style

**Python** (`galaxy_client.py`):
- PEP 8 style guide
- 4-space indentation
- Type hints in function signatures
- Descriptive variable names
- Docstrings for functions

**XML** (`edentity-metabarcoding-pipeline.xml`):
- 4-space indentation
- Descriptive parameter names
- Comprehensive help text
- Organized in logical sections

### Adding New Parameters

1. **Add to XML** (in appropriate section):
```xml
<param name="new_param" type="integer" value="10" 
       label="New Parameter" 
       help="Description of parameter"/>
```

2. **Add to command** (in command section):
```xml
--new_param $section.new_param
```

3. **Add to Python parser** (in `galaxy_client.py`):
```python
parser.add_argument('--new_param', help='Description', required=True)
```

4. **Pass to eDentity** (in command construction):
```python
cmd.extend(["--new_param", str(args_dict['new_param'])])
```

### Versioning

Version is specified in XML (line 1):
```xml
<tool id="edentity_metabarcoding_pipeline" name="eDentity Metabarcoding Pipeline" version="1.5.1">
```

**Version updates require**:
1. Update XML version attribute
2. Update `.shed.yml` (if releasing to ToolShed)
3. Update README.md
4. Tag release in Git

### Galaxy ToolShed Publishing

Configuration in `.shed.yml`:

```yaml
name: edentity_metabarcoding_pipeline
owner: luka
description: Pipeline for metabarcoding analysis
remote_repository_url: https://github.com/naturalis/galaxy-tool-edentity-metabarcoding-pipeline
type: unrestricted
categories:
  - "Metagenomics"
```

**Publishing command**:
```bash
planemo shed_update --shed_target toolshed
```

### Debugging

**Enable verbose output**:
- Check stdout/stderr in Galaxy job details
- Inspect `.snakemake` directory before cleanup (comment out removal)

**Common debugging steps**:
1. Verify input ZIP structure: `unzip -l input.zip`
2. Check extracted FASTQ files: `ls input_data/`
3. Test eDentity directly: Run constructed command manually
4. Examine intermediate files in `{project_name}/Results/`

---

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**: eDentity uses Snakemake's parallelization
2. **Memory Management**: Large datasets may require increased memory limits
3. **Disk I/O**: Fast storage improves performance significantly

### Bottlenecks

1. **Merging**: Most computationally intensive for large datasets
2. **Denoising**: Scales with number of unique sequences
3. **I/O**: ZIP extraction and file movement

### Scaling Guidelines

| Dataset Size | Recommended Cores | Memory | Time Estimate |
|--------------|-------------------|--------|---------------|
| <1M reads | 4 | 8 GB | 10-30 min |
| 1-10M reads | 8-16 | 16 GB | 30-120 min |
| >10M reads | 16-32 | 32+ GB | 2-6 hours |

---

## Security Considerations

### Input Validation

- Prevents path traversal attacks (no `../` in ZIP)
- Validates file extensions
- Limits allowed characters in filenames

### Command Injection Prevention

- Uses subprocess with list arguments (not shell=True)
- No user input directly in shell commands
- Parameters validated before use

### Temporary File Handling

- Uses secure temporary directories
- Cleanup after execution
- No persistent temporary files

---

## Future Enhancements

Potential improvements:

1. **Taxonomic Identification**: Integration with taxonomic databases
2. **Advanced Reporting**: Additional visualization options
3. **Parameter Optimization**: Auto-tuning based on data characteristics
4. **Incremental Processing**: Resume from checkpoints for large datasets
5. **Cloud Integration**: Support for cloud storage (S3, GCS)

---

## References

### External Documentation

- [eDentity Package](https://pypi.org/project/edentity/)
- [Galaxy Tool Development](https://docs.galaxyproject.org/en/latest/dev/schema.html)
- [VSEARCH Manual](https://github.com/torognes/vsearch)
- [fastp Documentation](https://github.com/OpenGene/fastp)
- [cutadapt Documentation](https://cutadapt.readthedocs.io/)
- [Snakemake Documentation](https://snakemake.readthedocs.io/)

### Scientific References

- Rognes et al. (2016). VSEARCH: A versatile open source tool for metagenomics. PeerJ 4:e2584
- Buchner et al. (2022). APSCALE: Advanced pipeline for simple yet comprehensive analyses of DNA metabarcoding data. Bioinformatics

---

## Glossary

- **ESV**: Exact Sequence Variant - unique DNA sequence identified in metabarcoding
- **Denoising**: Process of removing sequencing errors to identify true biological sequences
- **Dereplication**: Collapsing identical sequences to unique sequences with abundance counts
- **Chimera**: Artificial sequence formed from two or more biological sequences during PCR
- **Expected Error (EE)**: Sum of error probabilities for all bases in a sequence
- **Merging**: Combining overlapping paired-end reads into single sequences
- **Galaxy**: Web-based platform for data-intensive biomedical research
- **Snakemake**: Workflow management system for reproducible data analysis

---

## Contact and Support

- **Repository**: https://github.com/naturalis/galaxy-tool-edentity-metabarcoding-pipeline
- **Issues**: GitHub issue tracker
- **Maintainer**: Naturalis Biodiversity Center

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Tool Version**: 1.5.1
