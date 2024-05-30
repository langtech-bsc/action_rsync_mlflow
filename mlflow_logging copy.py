import argparse
import sys
from time import sleep
import sysrsync
from os import environ
import traceback
from dotenv import load_dotenv
import mlflow

load_dotenv()


remote_host = environ.get("REMOTE_HOST")
remote_user = environ.get("REMOTE_USER")
repo_name = environ.get("JOB_REPO_NAME")
# job_name = environ.get("JOB_NAME")
job_path = environ.get("JOB_PATH")
mlflow_tranking_server_url = environ.get('MLFLOW_TRACKING_SERVER_URL')
slurm_job_id = environ.get('SLURM_JOB_ID')
exit_code = int(environ.get("ROCKET_EXIT_CODE", 0))

logs_path = f"{job_path}/logs"
destination = './logs'

mlflow_run_id = environ.get("RUN_ID")
mlflow.set_tracking_uri(mlflow_tranking_server_url)
mlflow.set_experiment(repo_name)

def rsync_sync(loop=True):
    
    while True:
        try:
            sysrsync.run(
                    source_ssh=f"{remote_user}@{remote_host}",
                    source=logs_path,
                    destination=destination,
                    strict_host_key_checking=False,
                    options=['-avh'])

            mlflow.log_artifacts(destination)
            
        except:
            traceback.print_exc()
        

        if not loop:
            break

        sleep(15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=['sync', 'start', 'stop', 'artifacts-url'])
    args = parser.parse_args()
    
    if args.task == 'start':

        run = mlflow.start_run(run_name=slurm_job_id)

        filtered_vars = {name: value for name, value in environ.items() if name.startswith(('JOB_', 'SLURM_', 'GPFS_', 'GITHUB_'))}

        env_vars = dict(sorted(filtered_vars.items(), key=lambda item: (
            1 if item[0].startswith('JOB_') else 
            2 if item[0].startswith('SLURM_') else 
            3 if item[0].startswith('GPFS_') else 
            4 if item[0].startswith('GITHUB_') else 5
        )))

        mlflow.log_params(env_vars)
        mlflow.end_run('SCHEDULED')
        print(run.info.run_id)

    elif args.task == 'sync':
        mlflow.start_run(run_id=mlflow_run_id)
        rsync_sync()

    elif args.task == 'artifacts-url':
        
        run = mlflow.get_run(run_id=mlflow_run_id)
        print(f"{mlflow.get_tracking_uri()}/#/experiments/{run.info.experiment_id}/runs/{run.info.run_id}/artifacts")


    elif args.task == 'stop':
     
        mlflow.start_run(run_id=mlflow_run_id)

        rsync_sync(loop=False)

        if exit_code == 0:
            mlflow.end_run()
        else:
            mlflow.end_run('FAILED')

if __name__ == '__main__':
    main()