#!/bin/bash
set -e

echo "Running create_projects.sh..."
./create_projects.sh

echo "Activating virtual environment..."
source my-env/bin/activate

echo "Running sort.py..."
python3 sort.py

echo "Deactivating virtual environment..."
deactivate

echo "Running run_pipeline.py..."
python3 run_pipeline.py

echo "All tasks completed successfully!"
