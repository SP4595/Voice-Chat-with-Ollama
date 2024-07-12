#!/bin/bash

# Navigate to the project root directory
cd "$(dirname "$0")"

# Execute the Python script
python3 ./src/main_infer.py

# Keep the terminal open (optional)
read -p "Press any key to continue..."
