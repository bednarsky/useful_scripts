job_name_prefix=$1

squeue -u rbednarsky | grep $job_name_prefix | awk '{print $1}' | while read job_id; do
   scancel $job_id
done
