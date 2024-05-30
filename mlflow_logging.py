import argparse
from time import sleep
# import sysrsync
from os import environ
import traceback
import mlflow
from dotenv import load_dotenv

destination_dir = './logs'

class MlflowLogging():
    def __init__(self, tracking_uri, experiment_name) -> None:
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)

    def schedule(self, run_name):
        run = mlflow.start_run(run_name=run_name)
        load_dotenv()
        filtered_vars = {name: value for name, value in environ.items() if name.startswith(('JOB_', 'SLURM_', 'GPFS_', 'GITHUB_'))}

        env_vars = dict(sorted(filtered_vars.items(), key=lambda item: (
            1 if item[0].startswith('JOB_') else 
            2 if item[0].startswith('SLURM_') else 
            3 if item[0].startswith('GPFS_') else 
            4 if item[0].startswith('GITHUB_') else 5
        )))

        mlflow.log_params(env_vars)
        mlflow.end_run('SCHEDULED')
        return run.info.run_id

    def sync(self, remote_user, remote_host, source, destination):
        try:
            # sysrsync.run(
            #         source_ssh=f"{remote_user}@{remote_host}",
            #         source=source,
            #         destination=destination,
            #         strict_host_key_checking=False,
            #         options=['-avh'])

            mlflow.log_artifacts(destination)
            
        except:
            traceback.print_exc()

    
    def syncloop(self, remote_user, remote_host, source, destination, run_id):
        mlflow.start_run(run_id=run_id)
        while True:
            self._sync(remote_user, remote_host, source, destination)
            sleep(15)

    def get_artifact_url(self, run_id):
        run = mlflow.get_run(run_id=run_id)
        print(f"{mlflow.get_tracking_uri()}/#/experiments/{run.info.experiment_id}/runs/{run.info.run_id}/artifacts")

    def stop(self, remote_user, remote_host, source, destination, run_id, failed=False):
        mlflow.start_run(run_id=run_id)
        self.sync(remote_user, remote_host, source, destination)
        if failed:
            mlflow.end_run('FAILED')
        else:
            mlflow.end_run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mlflow logging')
    parser.add_argument('-t', '--task', required=True ,help='Permited tasks: [schedule, sync, stop]')
    parser.add_argument('--url', required=True ,help='Traking url')
    parser.add_argument('-e', '--experiment', required=True ,help='Experiment Name')
    parser.add_argument('-n', '--run_name', required=False ,help='Experiment Name')
    parser.add_argument('-i', '--run_id', required=False ,help='Experiment Name')
    parser.add_argument('-u', '--user', required=False ,help='Remote user')
    parser.add_argument('--host', required=False ,help='Remote host')
    parser.add_argument('-s', '--src', required=False ,help='Source files directory')
    parser.add_argument('-f', '--failed', required=False, default=False, action='store_true' ,help='Experiment Name')
    args = parser.parse_args()
    
    client = MlflowLogging(args.url, args.experiment)
    if args.task == 'schedule':
        run_id = client.schedule(args.run_name)
        print(run_id)
    if args.task == 'sync':
        client.syncloop(args.user, args.host, args.src, destination_dir, args.run_id)
    if args.task == 'stop':
        client.stop(args.user, args.host, args.src, destination_dir, args.run_id)


