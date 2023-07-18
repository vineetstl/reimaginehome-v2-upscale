#!/bin/bash
if pgrep -f "run_denoise_task.py" &>/dev/null; then
    echo "Running"
    exit
else
    echo "Restarting..."
    cd /home/ubuntu/realesrgan
    /home/ubuntu/anaconda3/envs/upscale/bin/python run_denoise_task.py
fi
