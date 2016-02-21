#!/bin/bash

CLEAR=clear

#SOLO_IP=10.1.1.10
#CONTROLLER_IP=10.1.1.1

SCPARGS="-o StrictHostKeyChecking=no -i ./updater_id_rsa"

system=`uname -a | awk '{print $1}'`

getVersions() {
    address="10.1.1.1" 
    #Wait for the target to come up
    echo -n "Waiting to connect to $address"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"

    echo "Starting pixhawk update on $address"
    ssh-keygen -R $address &> /dev/null

    ssh $SCPARGS root@$address "sololink_config --get-version all" 
}


md5() {
    address="10.1.1.1" 
    #Wait for the target to come up
    echo -n "Waiting to connect to $address"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"

    echo "updateing Controller MD5"
    ssh-keygen -R $address &> /dev/null

    ssh $SCPARGS root@$address "md5sum /etc/hostapd.conf > /etc/hostapd.conf.md5" 

    echo "Done\n"
}

calSticks() {
    address="10.1.1.1" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Controller"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"

    echo "Running Stick Cal"
    ssh-keygen -R $address &> /dev/null

    ssh $SCPARGS root@$address "runStickCal.sh" 
}


grabLogs() {
    address="10.1.1.10" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Solo"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"

    echo "Grabbing Pixhawk log $1"
    ssh-keygen -R $address &> /dev/null

    ssh $SCPARGS root@$address "init 2; loadLog.py $1" 
    scp $SCPARGS root@$address:/log/log$1.bin ~
}

resetSolo() {
    address="10.1.1.10" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Solo"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"
    echo "resetting Sololink"
    ssh-keygen -R $address &> /dev/null
    ssh $SCPARGS root@$address "sololink_config --settings-reset" 
}

installPano() {
    address="10.1.1.10" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Solo"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"
    echo "Install Pano"
    ssh-keygen -R $address &> /dev/null
    scp $SCPARGS ./Pano/*.py root@$address:/usr/bin
    ssh $SCPARGS root@$address "rm /usr/bin/*.pyc; reboot" 
}
    
installZipline() {
    address="10.1.1.10" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Solo"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"
    echo "Install Zipline"
    ssh-keygen -R $address &> /dev/null
    scp $SCPARGS ./Zipline/*.py root@$address:/usr/bin
    ssh $SCPARGS root@$address "rm /usr/bin/*.pyc; reboot" 
}
    
installSection() {
    address="10.1.1.10" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Solo"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"
    echo "Install Section"
    ssh-keygen -R $address &> /dev/null
    scp $SCPARGS ./Section/*.py root@$address:/usr/bin
    ssh $SCPARGS root@$address "rm /usr/bin/*.pyc; reboot" 
}
    
uninstall() {
    address="10.1.1.10" 
    #Wait for the target to come up
    echo -n "Waiting to connect to Solo"
    while ! ping -c1 -W1 $address &> /dev/null; do sleep 1; echo -n "."; done
    echo "Connected to $address"
    echo "Removing Experimental Shots"
    ssh-keygen -R $address &> /dev/null
    scp $SCPARGS ./uninstall/*.py root@$address:/usr/bin
    ssh $SCPARGS root@$address "rm /usr/bin/pano.py /usr/bin/zipline.py /usr/bin/section.py /usr/bin/*.pyc; reboot" 
}


menu() {
    echo ""
    echo "  Jason's Solo tools:"
    echo ""
    echo ""
    echo "    version   (grabs SW versions from Controller)"
    echo "    sticks    (cals Controller Sticks)"
    echo "    log       <N> or latest"
    echo "    md5       updates hostapd MD5"
    echo "    resetsolo Sololink Settings reset"
    echo "    pano      Install Pano Shot"
#   echo "    zipline   Install Zipline Shot"
#   echo "    section   Install Section Shot"
    echo "    uninstall Remove experimental shots"
    echo ""
    echo ""
    echo "Type any command followed by \"help\" for more information"
    while true; do
        read -p "Please enter a command (q to exit):" cmd
        args=`echo $cmd | awk '{$1=""; print $0}'`
        case $cmd in
            v|versions* ) getVersions $args; exit;;
            s|stick* ) calSticks $args; exit;;
            l|log* ) grabLogs $args; exit;;
            m|md5* ) md5 $args; exit;;
            pano ) installPano $args; exit;;
            zipline ) installZipline $args; exit;;
            section ) installSection $args; exit;;
            uninstall ) uninstall $args; exit;;
            q|quit|exit ) exit;;
            r|resetsolo* ) resetSolo $args; exit;;
            * ) echo "Please enter a valid command."; sleep 1; menu;;
        esac
    done
}



$CLEAR
menu
