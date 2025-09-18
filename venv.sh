#!/bin/bash

trap "echo -e '\033[35;1m!\033[m \033[91mGot an interruption ✘\033[m'; exit 1" SIGINT
echo -e "\033[35;1m>\033[m Checking Prerequisites..."

if command -v python3 &>/dev/null; then

    version="12"
    if command -v python3."$version" &>/dev/null; then
        echo -e "-\033[92m $(python3."$version" -V) installed ✔\033[m"
    else
        echo -e "-\033[91m Python3.$version not installed ✘\033[m"
        echo -e "\033[93mWARNING:\033[m This application was built on \033[37;1mPython3.12.11\033[m, so some unexpected errors may occur when using a different version."

        version=$(ls -1 /usr/bin/python3* | grep -Eo 'python3\.[0-9]*$' | sort -V | uniq | tail -n 1 | grep -oP '\d+\.\K\d+')
        echo -ne "\033[35;1m?\033[m Would you like to continue with \033[37;1m$(python3."$version" -V)\033[m? [\033[32my\033[m/\033[31mn\033[m]: "
        read answer

        if [ "$answer" = "Y" ] || [ "$answer" = "y" ]; then
            echo -e "-\033[92m Running with $(python3."$version" -V) ✔\033[m"
        else
            echo -e "Please install \033[37;1mPython3.12\033[m"
            exit 1
        fi
    fi
else
    echo -e "-\033[91m Python3 not installed ✘\033[m"
    echo -e "Please install \033[37;1mPython3.12\033[m"
    exit 1
fi

# Checking if Pip is installed
if command -v pip &>/dev/null; then
    echo -e "-\033[92m Pip $(pip --version | awk '{print $2}') installed ✔\033[m"
else
    echo -e "-\033[91m Pip not installed ✘\033[m"
    exit 1
fi

# Checking if Venv is installed
if python3 -c 'import venv' &>/dev/null; then
    echo -e "-\033[92m Venv Module installed ✔\033[m"
else
    echo -e "-\033[91m Venv Module not installed ✘\033[m"
    exit 1
fi

echo -e "\033[35;1m>\033[m Creating \033[37;1mPython Virtual Environment\033[m..."

if [ ! -d ".venv" ]; then
    python3."$version" -m venv .venv
fi

# Check the exit status of the venv creation
if [ $? -ne 0 ]; then
    echo -e "-\033[91m Failed to create Python Venv ✘ \033[m"
    echo -e "\033[35;1m>\033[m Removing directory..."
    if [ -d ".venv" ]; then
        rm -rf ".venv"
    fi
    exit 1
fi

source .venv/bin/activate

echo -e "\033[35;1m>\033[m Upgrading \033[37;1mPip\033[m and installing \033[37;1mWheel\033[m...\033[m"

pip install --upgrade pip

pip3 install wheel

echo -e "-\033[92m Wheel package installed ✔\033[m"

deactivate

echo -e "\033[35;1m>\033[92m Virtual Environment \033[m(\033[34;1m.venv\033[m\033[m)\033[92m created ✔\033[m"
