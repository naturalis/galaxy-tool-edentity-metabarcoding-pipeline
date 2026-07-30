# Technical Documentation: eDentity Metabarcoding Pipeline Galaxy Tool

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Pipeline Stages](#pipeline-stages)
5. [Input/Output Specifications](#inputoutput-specifications)
6. [Dependencies](#dependencies)
7. [Configuration Parameters](#configuration-parameters)
8. [Development Guidelines](#development-guidelines)

---

## Overview

The eDentity Metabarcoding Pipeline is a Galaxy tool wrapper that integrates the [edentity](https://pypi.org/project/edentity/) metabarcoding pipeline into the Galaxy ecosystem. It provides a user-friendly interface for processing amplicon sequencing data and generating Exact Sequence Variants (ESVs).

**Key Features:**
- Automated quality control and filtering
- Paired-end read merging
- Primer trimming
- ESV generation using UNOISE algorithm
- Comprehensive quality reports

---

## Architecture

### Components

The tool consists of three main layers:

1. **Galaxy Tool Wrapper** (`edentity-metabarcoding-pipeline.xml`)
   - Defines the user interface and parameters
   - Manages input/output data types and formats
   - Specifies Conda package dependencies

2. **Python Client** (`galaxy_client.py`)
   - Extracts and validates FASTQ files from ZIP archive
   - Constructs command for the eDentity pipeline
   - Organizes output files for Galaxy

3. **eDentity Pipeline** (external package)
   - Snakemake-based workflow orchestration
   - Integrates multiple bioinformatics tools
   - Manages the seven-stage analysis process

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Galaxy Interface                        │
│         (edentity-metabarcoding-pipeline.xml)              │
│                                                             │
│  User configures parameters and uploads ZIP file           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Python Client Script                      │
│                    (galaxy_client.py)                       │
│                                                             │
│  • Extract FASTQ files from ZIP                             │
│  • Validate file structure                                  │
│  • Build eDentity command                                   │
│  • Execute pipeline                                         │
│  • Organize outputs                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   eDentity Pipeline                         │
│              (Snakemake workflow engine)                    │
│                                                             │
│  Stage 1: Quality Control (fastp)                           │
│         ↓                                                   │
│  Stage 2: Merging (vsearch)                                 │
│         ↓                                                   │
│  Stage 3: Primer Trimming (cutadapt)                        │
│         ↓                                                   │
│  Stage 4: Quality Filtering (vsearch)                       │
│         ↓                                                   │
│  Stage 5: Dereplication (vsearch)                           │
│         ↓                                                   │
│  Stage 6: Denoising (vsearch)                               │
│         ↓                                                   │
│  Stage 7: ESV Table Generation                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Files                             │
│                                                             │
│  • ESV_table.tsv                                            │
│  • summary_report.tsv                                       │
│  • ESV_sequences.fasta                                      │
│  • multiqc_report.html                                      │
│  • json_reports.zip                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Overall Process

```
Input: ZIP file with paired-end FASTQ files
         ↓
Step 1: Galaxy receives user input
         • Parameters configured through web interface
         • ZIP file uploaded to Galaxy history
         ↓
Step 2: Python client processes input
         • Validates ZIP file structure
         • Extracts FASTQ files
         • Validates file naming conventions
         ↓
Step 3: eDentity command construction
         • Translates Galaxy parameters to CLI arguments
         • Constructs command with all user settings
         ↓
Step 4: Pipeline execution
         • Snakemake manages workflow execution
         • External tools process data sequentially
         • Intermediate files stored temporarily
         ↓
Step 5: Output collection
         • Results moved to Galaxy-specified paths
         • JSON reports aggregated into ZIP
         • Temporary files cleaned up
         ↓
Output: Five files in Galaxy history
         • ESV abundance table
         • Summary statistics report
         • ESV sequences for taxonomic assignment
         • Quality control HTML report
         • Detailed JSON metrics
```

### Key Data Transformations

| Stage | Input | Output | Transformation |
|-------|-------|--------|----------------|
| Extract | ZIP archive | Individual FASTQ files | File extraction and validation |
| QC | Raw FASTQ | Filtered FASTQ | Quality and length filtering |
| Merge | Paired FASTQ (R1/R2) | Single merged FASTQ | Overlap-based merging |
| Trim | Merged FASTQ | Trimmed FASTQ | Primer sequence removal |
| Filter | Trimmed FASTQ | Filtered FASTA | Quality and length filtering |
| Dereplicate | Filtered FASTA | Unique sequences | Collapse identical sequences |
| Denoise | Unique sequences | ESVs | Remove errors, detect chimeras |
| Generate | ESVs + original reads | ESV table | Map reads to ESVs, count abundances |

---

## Pipeline Stages

### Stage 1: Quality Control (fastp)
**Purpose**: Remove low-quality reads and trim low-quality bases

**Key Parameters:**
- Maximum N bases allowed
- Minimum average quality score
- Minimum read length

**Output**: Filtered FASTQ files

---

### Stage 2: Merging (vsearch fastq_mergepairs)
**Purpose**: Combine paired-end reads into single sequences

**Key Parameters:**
- Maximum mismatch percentage in overlap region
- Maximum absolute number of mismatches
- Minimum overlap length

**Output**: Merged FASTQ files

---

### Stage 3: Primer Trimming (cutadapt)
**Purpose**: Remove primer sequences from reads

**Key Parameters:**
- Forward and reverse primer sequences
- Anchored vs. non-anchored trimming
- Discard untrimmed reads option

**Output**: Trimmed FASTQ files

---

### Stage 4: Quality Filtering (vsearch fastq_filter)
**Purpose**: Apply length and quality filters to merged sequences

**Key Parameters:**
- Minimum sequence length
- Maximum sequence length
- Maximum expected errors

**Output**: Filtered FASTA files

---

### Stage 5: Dereplication (vsearch fastx_uniques)
**Purpose**: Collapse identical sequences and track abundances

**Output**: Unique sequences with abundance counts

---

### Stage 6: Denoising (vsearch cluster_unoise)
**Purpose**: Generate ESVs by clustering and removing sequencing errors

**Key Parameters:**
- Alpha (sequence similarity threshold)
- Minimum cluster size

**Algorithm**: UNOISE3 - identifies and removes errors, detects chimeras

**Output**: ESV sequences

---

### Stage 7: ESV Table Generation
**Purpose**: Create abundance matrix of ESVs across samples

**Process**: Maps original reads back to ESVs and counts occurrences

**Output**: TSV table with ESV counts per sample

---

## Input/Output Specifications

### Input Requirements

**Format**: ZIP archive containing paired-end FASTQ files

**Requirements:**
- Files must have `.fastq` or `.fastq.gz` extension
- Paired-end naming convention (e.g., `sample_R1.fastq.gz`, `sample_R2.fastq.gz`)
- All FASTQ files must be in the same directory within the ZIP
- Filenames cannot contain spaces or special characters (*, ', ")

**Example ZIP structure:**
```
sequences.zip
├── sample1_R1.fastq.gz
├── sample1_R2.fastq.gz
├── sample2_R1.fastq.gz
└── sample2_R2.fastq.gz
```

---

### Output Files

#### 1. ESV_table.tsv
**Description**: Abundance matrix of ESVs across samples

**Format**: Tab-separated values

**Structure**:
```
ESV_NO    ESV_ID                                      Sample1  Sample2  sequence
ESV_1     9bc4f41860c78e9560383d55ef9e9681a650c125    324091   353306   GCGGTTAAACG...
ESV_2     062c4dccaa466a10caf68ac0c4ccb5f56d7eebf1    20556    22734    GCGGTTAAACG...
```

**Columns:**
- `ESV_NO`: Sequential identifier
- `ESV_ID`: SHA1 hash of sequence
- Sample columns: Abundance counts
- `sequence`: Nucleotide sequence

---

#### 2. summary_report.tsv
**Description**: Pipeline statistics for each sample

**Format**: Tab-separated values

**Key Metrics:**
- Total reads
- Reads after each filtering step
- Merge success rate
- Number of ESVs per sample
- Chimeric sequences detected

---

#### 3. ESV_sequences.fasta
**Description**: ESV sequences for taxonomic assignment

**Format**: FASTA

**Header**: SHA1 hash (matches ESV_ID in table)

**Use**: Input for taxonomic classification tools (e.g., BLAST, SINTAX)

---

#### 4. Quality_control_report.html
**Description**: Interactive MultiQC report

**Contains:**
- Read count statistics
- Quality score distributions
- Sequence length distributions
- GC content analysis
- Primer trimming statistics

---

#### 5. json_reports.zip
**Description**: Detailed per-sample metrics in JSON format

**Use**: Programmatic access to detailed pipeline metrics

---

## Dependencies

### Conda Packages

| Package | Version | Purpose |
|---------|---------|---------|
| python | 3.12.8 | Runtime environment |
| fastp | 0.24.0 | Quality control |
| cutadapt | 4.9 | Primer trimming |
| vsearch | 2.28.1 | Merging, filtering, denoising |
| biopython | 1.84 | Sequence manipulation |
| multiqc | 1.27.1 | Report aggregation |
| nbitk | 0.5.9 | Naturalis bioinformatics toolkit |
| edentity | 1.5.1 | Core pipeline |
| polars | 1.30.0 | Data processing |

All dependencies are managed through Conda and automatically installed by Galaxy.

---

## Configuration Parameters

### Parameter Sections

#### Data Configuration
- **project_name**: Unique identifier for the analysis
- **data_type**: Sequencer platform (Illumina or AVITI)
- **input_fastqs**: ZIP file containing FASTQ files

#### Quality Control (fastp)
- **n_max**: Maximum N bases (0-5)
- **average_qual**: Minimum Q-score (15-30)
- **length_required**: Minimum length (50-300 bp)

#### Merging (vsearch)
- **fastq_maxdiffpct**: Max mismatch % (80-100%)
- **fastq_maxdiffs**: Max absolute mismatches
- **fastq_minovlen**: Min overlap (5+ bp)

#### Trimming (cutadapt)
- **forward_primer**: Forward primer sequence(s)
- **reverse_primer**: Reverse primer sequence(s)
- **anchored**: Anchor primers at ends (True/False)
- **discard_untrimmed**: Remove reads without primers (True/False)

#### Filtering (vsearch)
- **minlen**: Minimum sequence length (100-1500 bp)
- **maxlen**: Maximum sequence length (200-2000 bp)
- **maxee**: Maximum expected errors (0-2)

#### Dereplication (vsearch)
- **fasta_width**: FASTA line width (0 = unwrapped)

#### Denoising (vsearch)
- **alpha**: Similarity threshold for clustering
- **minsize**: Minimum cluster abundance

---

## Development Guidelines

### Adding New Parameters

To add a new parameter to the tool:

1. **Update Galaxy XML**
   - Add parameter definition in appropriate section
   - Add parameter to command invocation

2. **Update Python Client**
   - Add argument to argument parser
   - Pass parameter to eDentity command

3. **Test Changes**
   - Update test cases if needed
   - Validate with test data

### Code Organization

**Galaxy XML (`edentity-metabarcoding-pipeline.xml`):**
- Parameters organized in logical sections
- Each section groups related parameters
- Help text explains each parameter

**Python Client (`galaxy_client.py`):**
- `get_filenames()`: Validates FASTQ files in ZIP
- `extract_fastq_files()`: Extracts files from ZIP
- `edentityCmd()`: Executes eDentity pipeline
- `outputs()`: Organizes results for Galaxy

### Testing

**Unit Testing:**
```bash
planemo test edentity-metabarcoding-pipeline.xml
```

**Manual Testing:**
```bash
python galaxy_client.py \
  --project_name test \
  --dataType Illumina \
  --input_fastqs test-data/galaxyTestData.zip \
  [additional parameters...]
```

### Version Management

Version is defined in the XML tool tag:
```xml
<tool id="edentity_metabarcoding_pipeline" 
      name="eDentity Metabarcoding Pipeline" 
      version="1.5.1">
```

When updating:
1. Increment version in XML
2. Update `.shed.yml` if publishing to ToolShed
3. Tag release in Git
4. Update documentation

### Error Handling

The tool performs validation at multiple levels:

1. **Galaxy XML**: Type and range validation
2. **Python Client**: File structure and naming validation
3. **eDentity Pipeline**: Parameter and data validation

Error messages are captured and displayed to users through Galaxy's interface.

---

## Performance Considerations

### Resource Requirements

**Memory**: 
- Small datasets (<1M reads): 4-8 GB
- Medium datasets (1-10M reads): 8-16 GB
- Large datasets (>10M reads): 16-32+ GB

**Processing Time**:
- Varies by dataset size and parameters
- Parallel processing via Snakemake when possible
- Bottlenecks: merging and denoising stages

### Optimization Tips

- Use appropriate quality thresholds to reduce data volume early
- Set reasonable length filters for your amplicon
- Adjust minsize parameter based on sequencing depth

---

## References

### Documentation
- [eDentity Package](https://pypi.org/project/edentity/)
- [Galaxy Tool Development](https://docs.galaxyproject.org/en/latest/dev/schema.html)
- [VSEARCH Documentation](https://github.com/torognes/vsearch)
- [fastp Documentation](https://github.com/OpenGene/fastp)
- [cutadapt Documentation](https://cutadapt.readthedocs.io/)

### Scientific Publications
- Rognes et al. (2016). VSEARCH: A versatile open source tool for metagenomics. *PeerJ* 4:e2584
- Buchner et al. (2022). APSCALE: Advanced pipeline for simple yet comprehensive analyses of DNA metabarcoding data. *Bioinformatics*

---

## Glossary

- **ESV (Exact Sequence Variant)**: Unique DNA sequence identified in metabarcoding data
- **Denoising**: Process of removing sequencing errors to identify true biological sequences
- **Dereplication**: Collapsing identical sequences with abundance tracking
- **Chimera**: Artificial sequence formed from multiple biological sequences during PCR
- **Expected Error (EE)**: Sum of error probabilities for all bases in a sequence
- **Merging**: Combining overlapping paired-end reads into single sequences

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-22  
**Tool Version**: 1.5.1  
**Repository**: https://github.com/naturalis/galaxy-tool-edentity-metabarcoding-pipeline
