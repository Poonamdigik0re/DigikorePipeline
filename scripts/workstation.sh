#!/bin/bash

CPU=`/bin/lscpu | grep "Model name:" | awk -F: '{print $2}' | awk '{$1=$1};1'`
RAM=`/bin/lsmem | grep "Total online memory:" | awk -F: '{print $2}' | awk '{$1=$1};1'`
HDD=`/bin/lsblk -d -o "TYPE,NAME,SIZE" | grep disk | awk '{print $2"_"$3}'| sed -z  's/\n/ /g'`
IP=`/sbin/ip addr | egrep -o "(10\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+)"`
MAC=`/usr/sbin/ip -f link -o address | grep "state UP" | awk '{print $15}'`
HOST=`/bin/hostname -f`
OS=`/bin/cat /etc/redhat-release | awk '{print $1,$4}'`
GPU=`/usr/sbin/lspci | grep "VGA" | grep "NVIDIA" | cut -d " " -f 8- | rev | cut -d " " -f 3- | rev | sed -z -e 's/\[\|\]//g'`

SYS_VENDOR=`/bin/cat /sys/devices/virtual/dmi/id/sys_vendor`
PRODUCT_NAME=`/bin/cat /sys/devices/virtual/dmi/id/product_name`

if [ "${USER}" != "render" ] && [ "${SYS_VENDOR}" != "VMware, Inc." ]; then
    curl --header "Content-Type: application/json" \
    --data '{"cpu": "'"$CPU"'", "ram": "'"$RAM"'", "hdd": "'"$HDD"'", "ip": "'"$IP"'", "mac": "'"$MAC"'", "hostname": "'"$HOST"'", "os": "'"$OS"'", "gpu": "'"$GPU"'", "status": "'"$1"'", "user": "'"$USER"'", "sys_vendor": "'"$SYS_VENDOR"'", "product_name": "'"$PRODUCT_NAME"'"}' \
    "https://digi-pnq-central.digikore.work/api/save_system_info/";
fi