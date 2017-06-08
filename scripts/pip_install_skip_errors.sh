#!/bin/sh
 
if [ -z "$1" ]; then echo NEED PATH TO requirements.txt; exit; fi
 
while read dependency; do
    dependency_stripped="$(echo "${dependency}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    # Skip comments
    if [[ $dependency_stripped == \#* ]]; then
        continue
    # Skip blank lines
    elif [ -z "$dependency_stripped" ]; then
        continue
    else
         echo "################### Installing $dependency_stripped ###################"
        if pip install "$dependency_stripped"; then
            echo "$dependency_stripped is installed"
        else
            echo "Could not install $dependency_stripped, skipping"
        fi
    fi
done < $1
