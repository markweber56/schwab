#!/bin/bash
# Source the environment variables
echo "TEST" > /home/mark/projects/scaffold/schwab/logs/output.log
source /home/mark/projects/scaffold/schwab/set_vars.sh /home/mark/projects/scaffold/schwab/.env

# Run the python scraper
/home/mark/projects/scaffold/schwab/venv/bin/python3 /home/mark/projects/scaffold/schwab/scrape.py >> /home/mark/projects/scaffold/schwab/logs/output.log
