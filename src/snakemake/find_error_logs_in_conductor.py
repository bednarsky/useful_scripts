import os
import glob
import datetime
from pathlib import Path


def process_logfile(logfile):
    current_error = False
    error_rule = ""
    categorized = {"Out Of Memory (OOM)": [], "Killed (not OOM)": [], "Other": []}
    file_cache = {}

    with open(logfile, 'r') as file:
        for line in file:
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
                    if ".snakemake" in log_file:
                        # Use cache to avoid re-reading the same log file multiple times
                        if log_file in file_cache:
                            category, formatted_timestamp = file_cache[log_file]
                        else:
                            try:
                                timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))
                                formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                            except FileNotFoundError:
                                formatted_timestamp = "N/A"

                            # Fast classification by scanning bytes once and using lowercase checks
                            category = "Other"
                            try:
                                with open(log_file, 'rb') as lf:
                                    data_lower = lf.read().lower()
                                    # Prioritize OOM detection
                                    if (b"out of memory" in data_lower) or (b"oom" in data_lower):
                                        category = "Out Of Memory (OOM)"
                                    elif b"killed" in data_lower:
                                        category = "Killed (not OOM)"
                            except Exception:
                                category = "Other"

                            file_cache[log_file] = (category, formatted_timestamp)

                        entry = (error_rule, formatted_timestamp, log_file)
                        categorized[category].append(entry)
                current_error = False

    return categorized


def print_summary_and_sections(categorized):
    oom_count = len(categorized["Out Of Memory (OOM)"])
    killed_count = len(categorized["Killed (not OOM)"])
    other_count = len(categorized["Other"])

    category_col_width = max(len("Category"), len("Out Of Memory (OOM)"), len("Killed (not OOM)"), len("Other"))
    count_col_width = max(len("Count"), len(str(oom_count)), len(str(killed_count)), len(str(other_count)))
    separator = "+" + "-" * (category_col_width + 2) + "+" + "-" * (count_col_width + 2) + "+"

    print(separator)
    print("| " + "Category".ljust(category_col_width) + " | " + "Count".rjust(count_col_width) + " |")
    print(separator)
    print("| " + "Out Of Memory (OOM)".ljust(category_col_width) + " | " + str(oom_count).rjust(count_col_width) + " |")
    print("| " + "Killed (not OOM)".ljust(category_col_width) + " | " + str(killed_count).rjust(count_col_width) + " |")
    print("| " + "Other".ljust(category_col_width) + " | " + str(other_count).rjust(count_col_width) + " |")
    print(separator)
    print()

    def print_section(title, entries):
        print(title)
        print("-" * len(title))
        for error_rule, formatted_timestamp, log_file in entries:
            print(f"{error_rule} {formatted_timestamp} |||||")
            print(f"  {log_file}")

    print_section("Out Of Memory (OOM)", categorized["Out Of Memory (OOM)"])
    print()
    print_section("Killed (not OOM)", categorized["Killed (not OOM)"])
    print()
    print_section("Other", categorized["Other"])


# Get the last snakemake logfile
log_files = glob.glob(os.path.expanduser('~/projects/*/results/logs/snake_sbatch/*conductor*.out'))
log_files.extend(glob.glob(os.path.expanduser('~/projects/*/results/logs/snake_sbatch/*conductor*.log')))
last_log = max(log_files, key=os.path.getmtime)

# Process the logfile and print summary/sections
categorized_errors = process_logfile(last_log)
print_summary_and_sections(categorized_errors)
