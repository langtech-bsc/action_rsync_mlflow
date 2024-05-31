#!/bin/bash

# Check if at least one argument is passed
if [ $# -eq 0 ]; then
    echo "No arguments provided. Please use one of the following arguments: schedule, sync, stop, artifact_url"
    exit 1
fi

# Get the first argument
ARGUMENT=$1

case $ARGUMENT in
    "schedule")
        echo "Scheduling mlflow."
        python ml_flow.py -t schedule -e .env_mlflow
        ;;
    "sync")
        echo "Synchronizing remote with mlflow "
        nohup python ml_flow.py -t sync -e .env_mlflow --sync_dir mlflow_dir > mlflow_dir/mlflow.log
        ;;
    "stop_failed")
        echo "Stoping with failed"
        python ml_flow.py -t stop -e .env_mlflow --sync_dir mlflow_dir --failed
        ;;
    "stop_succeed")
        echo "Stoping with succeed"
        python ml_flow.py -t stop -e --sync_dir mlflow_dir .env_mlflow
        ;;
    "artifact_url")
        python ml_flow.py -t artifact_url -e .env_mlflow
        ;;
    *)
        echo "Invalid argument. Please use one of the following arguments: schedule, sync, stop, artifact_url"
        exit 1
        ;;
esac