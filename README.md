# eDentity-metabarcoding-pipeline
This repository provides a Galaxy tool wrapper for executing the [edentity](https://pypi.org/project/edentity/) metabarcoding pipeline within the Galaxy environment. It enables reproducible and scalable analysis of amplicon sequencing data using [Snakemake](https://snakemake.readthedocs.io/) and `vsearch`, generating Exact Sequence Variants (ESVs) for downstream analysis.

> **Note:**  
> Taxonomic identification is not included. The ESVs can be used as input for other taxonomic assignment tools.

## Installation
This tool can be installed directly from the Galaxy ToolShed. You must be an administrator of your Galaxy instance to install new tools, or you can request your Galaxy admin to install it for you.

1. Log in to your Galaxy instance as an admin.
2. Navigate to **Admin > Tool Management > Install and Uninstall**.
3. Search for `eDentity Metabarcoding Pipeline`.
4. Follow the prompts to install the tool.

For more details, see the [Galaxy ToolShed documentation](https://galaxyproject.org/toolshed/).

## Input 
zip folder with fastq sequence files.
## Outputs

- **ESV_table.tsv**: Abundance of each ESV per sample.
- **summary_report.tsv**: Summary of reads at each analysis step.
- **ESV_sequences.fasta**: ESV sequences for taxonomic identification.
- **Quality_control_report.html**: Interactive visualization of quality metrics and read statistics.

These outputs support further analysis and interpretation.

## citations
```
- Naturalis Biodiversity Center. (2025). *eDentity metabarcoding Pipeline* [Computer software]. https://github.com/naturalis/galaxy-tool-edentity-metabarcoding-pipeline.git

- Rognes, T., Flouri, T., Nichols, B., Quince, C., & Mahé, F. (2016). VSEARCH: A versatile open source tool for metagenomics. *PeerJ*, *4*, e2584. https://doi.org/10.7717/peerj.2584

- Buchner, D., Macher, T.-H., & Leese, F. (2022). APSCALE: Advanced pipeline for simple yet comprehensive analyses of DNA metabarcoding data. *Bioinformatics*. https://doi.org/10.1093/bioinformatics/btac588
```
