#!/bin/sh

echo "Installing in bus.monitor"

sudo apt-get update

sudo apt-get install python python-dev
easy_install pip

sudo echo "export ALPIBUS_DIR=\"/home/linuxlite/PycharmProjects/car.dashboard\"" >> /etc/environment

sudo apt-get install mysql-server libmysqlclient-dev
sudo pip install sqlalchemy MySQL-python python-dateutil
mysql -u root -p -e "create database car_dashboard";

for SERVICE in `ls service_*`
do
    echo "Installing service $SERVICE"
    chmod 0755 $SERVICE
    if [ -e "/etc/init.d/$SERVICE" ]; then
        sudo unlink /etc/init.d/$SERVICE
    fi
    sudo ln -s $INSTALL_DIR/$SERVICE /etc/init.d/$SERVICE
done

