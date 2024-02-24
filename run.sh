#!/bin/bash

cd "~/jerry-bot" || exit

git fetch origin

if git rev-list --count --left-only "@{u}"...HEAD > /dev/null; then

    echo "New changes detected. Pulling the latest changes..."

    pip_install_needed=false

    file_to_check="requirements.txt"
    if git diff --quiet origin/master..HEAD -- "$file_to_check"; then
        echo "File $file_to_check is already up-to-date. No dependencies to install."
    else
        pip_install_needed=true
    fi

    git pull origin master
    echo "Successfully pulled the latest changes."

    if [ "$pip_install_needed" = true ]; then
        pip install -r requirements.txt
        echo "Successfully installed the latest dependencies."
    fi
else
    echo "Already up-to-date. No new changes to pull."
fi

echo "Launching bot..."
python3 src/runner.py
