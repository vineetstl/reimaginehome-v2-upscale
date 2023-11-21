#!/bin/bash
if pgrep -f "run_denoise_task.py" &>/dev/null; then
    echo $(date -u) "Running"
    exit
else
    echo $(date -u) "Restarting..."
    cd /home/ubuntu/realesrgan
    /home/ubuntu/anaconda3/envs/upscale/bin/python run_denoise_task.py
fi

# MAILTO=""
# */1 * * * * bash ~/realesrgan/revive.sh >> /home/ubuntu/realesrgan/cron.log
