#!/bin/bash
# This script is responsible for installing and configuring pre-reqs needed on the Traffic Light Control Pi

# Is needed on a pi?
modify_bashrc(){
	sed -i '/#force_color_prompt=yes/s/^#//g' ~/.bashrc
	source ~/.bashrc
}

# Create method to run raspi-config
update_pi() {
	sudo apt update
	sudo apt full-upgrade
	sudo rpi-eeprom-update
	sudo rpi-eeprom-update -a
}

install_packages() {
	echo "Installing Packages..."
	install_util_pkgs=(build-essential microcom sshpass ssh nmap python3-pip git lm-sensors curl libpq-dev)

	sudo apt-get update
	sudo apt-get upgrade
	sudo apt-get -y --ignore-missing install "${install_util_pkgs[@]}"
	read -p "Press any key to continue: " TMP_CONFIRM
}

install_python_packages() {
	echo "Installing Python Packages..."
	python3 -m pip install -r requirements.txt --break-system-packages
}

#setup_network_interface() {
#	# IP MUST be 192.168.2.205
#}

create_traffic_light_service(){
	sudo cp /home/admin/Documents/Autocross_TimingControl-main/TrafficLightActuator/TrafficLightActuatorService.service /lib/systemd/system/
	sudo systemctl enable TrafficLightActuatorService.service
}


SCRIPT_LOCATION="$(dirname "$(readlink -f "$0")")"

#modify_bashrc
update_pi
install_packages
install_python_packages
#setup_network_interface
create_traffic_light_service

echo ""
echo "--------------------------------"
echo "|                              |"
echo "|  Pi Configuration complete.  |"
echo "|                              |"
echo "|  Reboot the PC.              |"
echo "|                              |"
echo "--------------------------------"
echo ""
