echo "$(crontab -l ; echo  '*/1 * * * * bash ~/realesrgan/revive.sh')" | crontab -