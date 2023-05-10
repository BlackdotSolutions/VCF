#!/bin/bash

# Enter root mode first:
# sudo -i
#
# Update permissions first by running:
# chmod +x install_vcf.sh
#
# Then run the installer by running (specifying the connectors you want to install):
# ./install_vcf.sh Chainalysis,Gravatar,LittleSis,Cribis,VCF_Router

# Parse folders parameter
if [ -z "$1" ]; then
    echo "Error: Folders parameter is empty. Please provide a comma-separated list of folders to loop through."
    echo "Example: ./install.sh Chainalysis,Gravatar,LittleSis,Cribis,VCF_Router"
    exit 1
fi

folders=$1
IFS=',' read -ra folders_array <<< "$folders"

for folder in "${folders_array[@]}"
do
  case $folder in
    Chainalysis|Gravatar|LittleSis|VCF_Router)
            # pass
            ;;
        Cribis)
        # Set environment variables
            read -p "Please enter your Cribis Username: " cribis_username
            read -p "Please enter your Cribis Password: " -s cribis_password
            export CRIBIS_USERNAME=$cribis_username
            export CRIBIS_PASSWORD=$cribis_password
            # pass
            ;;
        Sayari)
        # Set environment variables
            read -p "Please enter your Sayari Client ID: " sayari_username
            read -p "Please enter your Sayari Password: " -s sayari_password
            export SAYARI_CLIENT_ID=$sayari_username
            export SAYARI_CLIENT_SECRET=$sayari_password
            # pass
            ;;
        *)
            echo "Error: Invalid folder name '$folder'. Valid folder names are Chainalysis, Sayari, Gravatar, LittleSis, Cribis and VCF_Router."
            exit 1
            ;;
    esac
done

#Change to videris directory
 cd /home/videris/

# Check if Python 3.10 is installed, if not install it
if ! command -v python3.10 &> /dev/null; then
    echo "Python 3.10 not found, installing..."
    apt update
    apt install software-properties-common -y
    add-apt-repository ppa:deadsnakes/ppa
    echo -ne '\n'
    apt install python3.10-venv -y
fi

# Clone or pull the VCF repository
if [ -d "VCF" ]; then
    echo "VCF repository found, pulling latest changes..."
    cd VCF
    for folder in "${folders_array[@]}"; do
        cd "$folder"       
        # Stash any changes to config.yml
        git stash push config.yml
        git pull origin main
        # Apply stashed changes to config.yml
        git stash apply stash@{0}
        cd ..
    done
    cd ..

else
    echo "VCF repository not found, cloning..."
    git clone https://github.com/BlackdotSolutions/VCF.git
fi

cd VCF
ip=$(hostname -I | awk '{print $1}')

for folder in "${folders_array[@]}"; do
    # Create and activate new virtual environment
    cd "$folder"
    python3.10 -m venv venv
    source venv/bin/activate

    # Install Python requirements from VCF/VCF_Router/requirements.txt
    pip install -r requirements.txt

    # Find an unused network port and the machine's IPv4 address
    port=$(python -c "import socket; s=socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()")

    # Start the uvicorn server with the host being the IPv4 address and the port being the unused network port
    uvicorn main:app --host $ip --port $port &

    # Check if cron job already exists
    if crontab -l | grep -q "$(pwd)"; then
        # crontab job exists. update it:
        (crontab -l | sed "s|.*$(pwd).*|@reboot cd $(pwd) \&\& source venv/bin/activate \&\& uvicorn main:app --host $ip --port $port \&|g") | crontab -
    else
        # Add a cron job to start the server on machine restart
        (crontab -l 2>/dev/null; echo "@reboot cd $(pwd) && source venv/bin/activate && uvicorn main:app --host $ip --port $port &") | crontab -
        echo "Uvicorn server started at $ip:$port, added to cron job to start on machine restart, and virtual environment activated."
    fi
done
