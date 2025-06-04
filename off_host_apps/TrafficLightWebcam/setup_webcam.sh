#!/bin/bash
# This script is responsible for installing the needed packages to read the webcam.

install_python_packages() {
	echo "Installing Python Packages..."
	# This seems to crash on older Pis	
	#python3 -m pip install -r requirements.txt --break-system-packages
	# This works, FOR NOW
	sudo apt-get install python3-opencv
}

create_webcam_service(){
	sudo cp /home/admin/Documents/Autocross_TimingControl/TrafficLightWebcam/TrafficLightWebcamService.service /lib/systemd/system/
	sudo systemctl enable TrafficLightWebcamService.service
}

create_cronjob(){
	crontab -l > temp_cron_file
	echo "* * * * * /home/admin/Documents/Autocross_TimingControl/TrafficLightWebcam/startline-photo-backup.sh" >> temp_cron_file
	crontab temp_cron_file
	rm temp_cron_file

SCRIPT_LOCATION="$(dirname "$(readlink -f "$0")")"

#install_python_packages
create_webcam_service

echo ""
echo "--------------------------------"
echo "|                              |"
echo "|  Pi Configuration complete.  |"
echo "|                              |"
echo "--------------------------------"
echo ""
