#!/bin/bash

# Check if the user has provided a file path argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file_path>"
    # exit 0
fi

# Extract the file path from the command line argument
file_path=$1

# Check if the file exists
if [ ! -f "$file_path" ]; then
    echo "Error: File '$file_path' does not exist."
    # exit 0
fi

# read file line by line
echo "Contents of file $file_path:"
while IFS= read -r line; do
    if [[ $line =~ .*=.* ]]; then
        # Split the line on '='
        IFS='=' read -r key value <<< "$line"
        # Check if key and value are not empty
        if [ -n "$key" ] && [ -n "$value" ]; then
            echo "Exporting variable: $key"
            export $key=$value
        fi
    fi
done < "$file_path"

# Check if the opening was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to open the file."
    # exit 0
fi

# exit 0