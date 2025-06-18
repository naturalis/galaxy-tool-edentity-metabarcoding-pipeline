import os
import argparse
import subprocess
import sys
import shutil
import zipfile
from pathlib import Path
import os
import re


# prepars the fastq files for the pipeline
def get_filenames(zip_files_list):
    """
    :param zip_files_list: list of files in the zip file
    :return: the list of filenames (without paths) + filenames with path in the zip file
    """
    full_filenames_list = [n for n in zip_files_list if re.search(r'.*[.]fastq([.]gz)?$', n)]
    for file in full_filenames_list:
        for c in [' ', "*", "'", '"']:
            assert c not in file, f"Error: File name {file} contains illegal character: {c}"
    
    assert full_filenames_list, "FASTQ files cannot be found in zip file"
    # check that all files are located same directory or at the root
    store_dir = set([os.path.dirname(n) for n in full_filenames_list])
    assert len(store_dir) == 1, "FASTQ  files found in different locations inside the zip file"
    return full_filenames_list


def extract_fastq_files(read_zip_file: str,
                        output_dir: str):
    assert zipfile.is_zipfile(read_zip_file), "Input Zip file is not a valid ZIP file"
    with zipfile.ZipFile(read_zip_file, 'r') as ziph:
        names = ziph.namelist()
        print("Names in zip file:", len(names))
        filenames = get_filenames(names)
        print("FASTQ Filenames:", len(filenames))
        # only extract the fastq found
        ziph.extractall(path=output_dir, members=filenames, pwd=None)
        # move the fastq files at the root of the output_dir
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                if os.path.join(root, f) != os.path.join(output_dir, f):
                    shutil.move(os.path.join(root, f), output_dir)

    return filenames


# prepares the snakemake command
def edentityCmd(cmd):
    """
    Executes edentity tool.
    Parameters:
    cmd (list): The edentity command to be executed as a list of strings.
    Returns:
    None
    """

    result = subprocess.run(cmd, capture_output=True, text=True)
    
    
    if result.returncode == 0:
        print(result.stdout, file=sys.stdout)
        # print(result.stderr, file=sys.stdout) 
    else: # error
        print(result.stderr, file=sys.stderr)
        # print(result.stdout, file=sys.stderr) 

    
    # remove the .snakemake folder (do we also remove results that are not needed for galaxy?)
    snakemake_proc_folder = ".snakemake"
    if not os.path.isdir(snakemake_proc_folder):
        print("Warning: Snakemake processing folder not found (%s)" % snakemake_proc_folder)
    else:
        print("Removing .snakemake processing dir")
        shutil.rmtree(snakemake_proc_folder)

    return None

def zip_file(file, zipf):
    basename = os.path.basename(file)
    zipf.write(file, basename)


def outputs(snakemake_work_dir, args_dict):
    """
    Returns the output files of the pipeline
    """
    
    # Move the ESV table to the current galaxy working directory
    esv_table = os.path.join(snakemake_work_dir, "Results", "report", f"{args_dict['project_name']}_ESV_table.tsv")
    shutil.move(esv_table, args_dict['ESV_table_output'])

    # Move the summary report to the current  galaxy working directory
    summary_report = os.path.join(snakemake_work_dir, "Results", "report", f"{args_dict['project_name']}_summary_report.tsv")  
    shutil.move(summary_report, args_dict['summary_report'])

    # Move the multiqc report to the current galaxy working directory
    fastp_multiqc_report_path = os.path.join(
        snakemake_work_dir, "Results", "report",
        f"{args_dict['project_name']}_multiqc_reports", f"{args_dict['project_name']}_multiqc_report.html")
    shutil.move(fastp_multiqc_report_path, args_dict['multiqc_report'])

    # zip ESV fasta to the ESV_fastas zip file
    ESV_fasta = os.path.join(snakemake_work_dir, "Results",
            "ESVs_fasta", f'{args_dict['project_name']}_esv_sequences.fasta')
    shutil.move(ESV_fasta, args_dict['ESV_sequences'])

    # with zipfile.ZipFile(args_dict['ESV_fasta_zip'], 'w', zipfile.ZIP_DEFLATED) as zipf:
    #     fasta_seqs = [os.path.join(ESV_fasta, file) for file in os.listdir(ESV_fasta)]
    #     for fasta in fasta_seqs:
    #         zip_file(fasta, zipf)

    # zip json reports
    json_reports = [json for json in os.listdir(os.path.join(snakemake_work_dir, "Results", "report")) if json.endswith(".json")]
    with zipfile.ZipFile(args_dict['json_reports'], 'w', zipfile.ZIP_DEFLATED) as zipf:
        json_file_paths = [os.path.join(snakemake_work_dir, "Results", "report", json) for json in json_reports]
        for json in json_file_paths:
            zip_file(json, zipf)




def main():
    parser = argparse.ArgumentParser(description='Galaxy client for the Edentity Metabarcoding pipeline')
    parser.add_argument('--project_name', help='name of the project', required=True)
    parser.add_argument('--dataType', help='Illumina or AVITI', required=True)
    parser.add_argument('--input_fastqs', help='zip containing the fastq files', required=True)
    parser.add_argument('--n_max', help='Maximum number of N bases allowed in read', required=True)
    parser.add_argument('--average_qual', help='Minimum average quality score required', required=True)
    parser.add_argument('--length_required', help='Minimum read length required after trimming', required=True)
    parser.add_argument('--fastq_maxdiffpct', help='Maximum percentage of mismatches allowed in overlap region', required=True)
    parser.add_argument('--fastq_maxdiff', help='Maximum number of mismatches allowed in overlap region', required=True)
    parser.add_argument('--fastq_minovlen', help='Minimum length of overlap between read pairs', required=True)
    parser.add_argument('--forward_primer', help='Forward primer sequence', required=True)
    parser.add_argument('--reverse_primer', help='Reverse primer sequence', required=True)
    parser.add_argument('--discard_untrimmed', help='Discard untrimmed reads', required=True)
    parser.add_argument('--anchored', help='Use anchoring for primer trimming', required=False, default=False)
    parser.add_argument('--minlen', help='Minimum length filter for reads', required=True)
    parser.add_argument('--maxlen', help='Maximum length filter for reads', required=True)
    parser.add_argument('--maxee', help='Maximum expected error rate allowed per read', required=True)
    parser.add_argument('--fasta_width', help='Line width for FASTA output files', required=True)
    parser.add_argument('--alpha', help='Alpha parameter for denoising algorithm', required=True)
    parser.add_argument('--minsize', help='Minimum abundance for ESV clusters', required=True)
    parser.add_argument('--create_extended_json_reports', help='Create extended JSON reports', required=False, default=False)
    parser.add_argument('--ESV_table_output', help='Output file path for ESV abundance table', required=True)
    parser.add_argument('--ESV_sequences', help='Output file path for ESV FASTA file', required=True)
    parser.add_argument('--summary_report', help='Output file path for summary report', required=True)
    parser.add_argument('--multiqc_report', help='Output file path for MultiQC report', required=True)
    parser.add_argument('--conda_prefix', help='Path to conda environment prefix', required=False)
    parser.add_argument('--json_reports', help='Output file for zipped json reports', required=True)



    args = parser.parse_args()
    assert " " not in args.input_fastqs, "Error: the ZIP filename must not contain space character(s)"
    args_dict = vars(args)    
    
    # unzip the fastq file
    
    input_data_dir = os.path.join(os.getcwd(), "input_data")
    snakemake_work_dir = os.path.join(os.getcwd(), args_dict['project_name']) # this is not where galaxy work dir is
    galaxy_work_dir = os.getcwd()
    
    print("input directory:", input_data_dir)
    print("snakemake work directory:", snakemake_work_dir)
    print("galaxy work directory:", galaxy_work_dir)
    
    # extract the fastq files
    extract_fastq_files(args_dict['input_fastqs'], input_data_dir)
   
    
    
    # run snakemake pipeline 
    
    # set the snakemake command   
    cmd = [
        "edentity",
        "--raw_data_dir", input_data_dir,
        "--dataType", args_dict['dataType'],
        "--work_dir", snakemake_work_dir,
        "--forward_primer", args_dict['forward_primer'],
        "--reverse_primer", args_dict['reverse_primer'],
    ]

    # Only add if True
    if str(args_dict['create_extended_json_reports']).lower() in ("true", "1"):
        cmd.append("--make_json_reports")
    if str(args_dict['discard_untrimmed']).lower() in ("true", "1"):
        cmd.extend(["--discard_untrimmed"])
    if str(args_dict['anchored']).lower() in ("true", "1"):
        cmd.extend(["--anchoring"])

    cmd.extend([
        "--n_base_limit", str(args_dict['n_max']),
        "--average_qual", str(args_dict['average_qual']),
        "--length_required", str(args_dict['length_required']),
        "--maxdiffpct", str(args_dict['fastq_maxdiffpct']),
        "--minovlen", str(args_dict['fastq_minovlen']),
        "--maxdiffs", str(args_dict['fastq_maxdiff']),
        "--min_length", str(args_dict['minlen']),
        "--max_length", str(args_dict['maxlen']),
        "--maxEE", str(args_dict['maxee']),
        "--fasta_width", str(args_dict['fasta_width']),
        "--alpha", str(args_dict['alpha']),
        "--minsize", str(args_dict['minsize']),
        
    ])

    # run the snakemake command
    edentityCmd(cmd)

    # get the output files: NB smakemake_work_dir is project_name.
    outputs(snakemake_work_dir, args_dict)


if __name__ == '__main__':
    main()
