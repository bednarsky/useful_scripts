import os
import glob
import datetime
from pathlib import Path

def process_logfile(logfile):
    current_error = False
    error_rule = ""

    with open(logfile, 'r') as file:
        lines = file.readlines()
        for line in lines:
            # Look for the "Error in rule" line
            if line.startswith("Error in rule"):
                error_rule = line.split(":")[0]
                error_rule = error_rule.replace("Error in rule ", "")
                current_error = True

            # When encountering a log line while in error state, process it
            if current_error and line.startswith("    log:"):
                # Extract the second path on the log line
                parts = line.split()
                if len(parts) > 2:
                    log_file = parts[2]
                    if not '/' in log_file:
                        log_file = parts[1]
                    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
                    formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"{error_rule} {formatted_timestamp} |||||\n  {log_file}")
                current_error = False

# Get the last snakemake logfile
log_files = glob.glob(os.path.expanduser('~/projects/*/results/logs/snake_sbatch/*_conductor*.out'))
last_log = max(log_files, key=os.path.getmtime)

# Process the logfile
process_logfile(last_log)
