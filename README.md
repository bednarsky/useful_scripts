# ✨ Miscellanous useful things ✨

## 🐍 Snakemake 🐍 
### 📝 Log/progress parsing setup 📝
I am really happy with my log parsing setup for running snakemake jobs. You might have your own setup, but I wanted to share it anyways, maybe something useful for someone - maybe I get nice feedback how to make it even better . This works well if you
- use [conductor jobs](https://github.com/epigen/cemm.slurm.sm) (i.e., don't run snakemake interactively but via sbatch - not supposed to be like this but really useful imo)
- always have the same structure, in my case, all conductor logs are named `~/projects/*/results/logs/snake_sbatch/*conductor*.out`

Here, my useful aliases: 
- find and show the errors in an easily parseable manner (this is my favourite) 
  ```bash
  alias finderr='python ~/projects/useful_scripts/src/snakemake/find_error_logs_in_conductor.py > ~/tmp/finderr.txt; less ~/tmp/finderr.txt'
  ```
  - optimized for Snakemake 9 (the log structures sometimes change between versions)
  - counts the types of errors & sorts the file paths by them in an easily copy-pasteable way &rarr; no more guessing if the 300 error files are all the same error or 20 different errors
  ```bash
  | Category                                                                   | Count |
  +----------------------------------------------------------------------------+-------+
  | Out Of Memory (OOM)                                                        |     0 |
  | Killed (not OOM)                                                           |     0 |
  | KeyError: 'cell_type'                                                      |     3 |
  | Error in .subset(x, j) : invalid subscript type 'list'                     |     5 |
  | AssertionError: This script only works for groups being cell types for now |     2 |
  +----------------------------------------------------------------------------+-------+
  
  Out Of Memory (OOM)
  -------------------
  
  Killed (not OOM)
  ----------------
  
  KeyError: 'cell_type'
  ---------------------
  fig1_marker_plot_selected_genes 2025-10-06 22:30:36 |||||
    /path/to/repo/.snakemake/slurm_logs/rule_fig1_marker_plot_selected_genes/ATAC_TSS_1000_500/10552392.log
  fig1_marker_plot_selected_genes 2025-10-06 22:30:36 |||||
    /path/to/repo/.snakemake/slurm_logs/rule_fig1_marker_plot_selected_genes/ATAC_TSS_500_100/10552394.log
  fig1_marker_plot_selected_genes 2025-10-06 22:30:36 |||||
    /path/to/repo/.snakemake/slurm_logs/rule_fig1_marker_plot_selected_genes/ATAC_TSS_100_100/10552396.log
  
  Error in .subset(x, j) : invalid subscript type 'list'
  ------------------------------------------------------
  confounding_factor_quantification_stat_test 2025-10-06 22:29:46 |||||
    /path/to/repo/.snakemake/slurm_logs/rule_confounding_factor_quantification_stat_test/a
  ll_L4_RNA/10552408.log
  confounding_factor_quantification_stat_test 2025-10-06 22:29:45 |||||
    /path/to/repo/.snakemake/slurm_logs/rule_confounding_factor_quantification_stat_test/s
  ample_type__not_all_metadata__False_L4_RNA/10552409.log
  ```
  
- print my queue including job names 
  ```bash
  alias myq="squeue -u rbednarsky -o '%.12i %.4P %.5j %.80k %.8M %.4C %.9m %.6D %R'"
  ```
- give me the most recent log across projects
  ```bash
  alias log_cond='LASTLOG=$(ls -Atd ~/projects/*/results/logs/snake_sbatch/*conductor*.{out,log} | head -1); echo $LASTLOG; tail -100 $LASTLOG; echo $LASTLOG; echo "----------------------------------------"'
  ```
- continuously print how many errors there are in your pipeline (this is useful to notice early if something doesn't work)
  ```bash
  alias ccounterr='while true; do LASTLOG=$(ls -Atd ~/projects/*/results/logs/snake_sbatch/*conductor*.{out,log} | head -1); echo ........................................................; ls -l "$LASTLOG" | awk '\''{print $6, $7, $8, $9}'\''; grep "Error" "$LASTLOG" | sort | uniq -c; sleep 5; done'
  ```

### 🧑‍💻 🤝 🐍 Interactive coding with Snakemake 🧑‍💻 🤝 🐍
This relates to code in `src/snakemake/interactive_snakemake_object.py`

My aim here is to work interactively, while developing a workflow, in two ways: 
1. When writing a script for the first time, I want to already write it in a way that makes it easy to adapt the script to be run in the snakemake workflow. 
2. Once I think the script is working, and it is run by the workflow already once, but I find out I want to change something, I want to be able to start a session that looks as if the script is just now being run by snakemake, i.e., there is a object in memory that is called `snakemake` that contains the input, output, wildcards, etc.

Here is how I do it: 
- During development, I use the `SnakelikeObject` class to work interactively with the snakemake object. It takes a nested dictionary, where first keys are `input`, `output`, `wildcards`, etc., and second keys are the names of the input/output files/directories with values being the paths to the files/directories.
```python
snakemake = SnakelikeObject({
  "input": {
    "adata_superset": "/path/to/adata_superset.h5ad",
    "marker_genes": "/path/to/marker_genes.csv"
  },
  "output": {
    "fig1_marker_plot_selected_genes": "/path/to/fig1_marker_plot_selected_genes.png"
  },
  "wildcards": {
    "cell_type": "L4_RNA",
    "tss_distance": "1000_500"
  },
})
```

- You can then use this object just as snakemake would use it, accessing attributes like this `snakemake.input['adata_superset']` etc. 
- Once you are ready to run via snakemake, this structure is easy to transfer into a rule. 
- At the top of your script, save the object that snakemake injects into your environment as a json file, so you can load it for interactive coding later.
```python
# save snakemake object content as json
snakemake_object_to_json(snakemake)
```

- Once snakemake was run, if you want to code interactively, you can load the snakemake object from the json file.
```python
snakemake = read_json_into_smk_obj(PROJECT_ROOT / 'results/smk_objects/rule_name/wildcards.json')
```