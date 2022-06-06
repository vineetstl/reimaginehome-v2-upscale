#!/bin/bash
exec >logfile.txt 2>&1
if pgrep -f "run_denoise_task.py" &>/dev/null; then
    echo "Running"
    exit
else
    echo "Restarting..."
    cd ~/realesrgan
    eval "$(conda shell.bash hook)"
    conda activate venv
    /usr/bin/nohup python run_denoise_task.py
fi
