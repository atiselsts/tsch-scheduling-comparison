#!/bin/bash

cd iot-lab-firmwares

# duration
export d=61
# network with 4 neighbors per node
export nodes_4='4+11+20+41+51+60+69+73+82+91+105+123+141+159+177+184+193+202+221+239+259+277+294+301+310+319+328+337+346+355+363'
# network with 10 neighbors per node
export nodes_10='119+123+127+131+135+139+143+147+151+156+159+163+167+177+179+181+183+185+188+190+193+195+197+199+201+203+205+207+211+215+219'

for file in `ls *iotlab`
do
    echo $file
    export logfile=${file/iotlab/log}

    #iotlab-experiment submit -n a2941 -d $d -l grenoble,m3,$nodes_4;
    #iotlab-experiment wait;
    #iotlab-node --update node.iotlab
    #serial_aggregator > sparse-${logfile}
    echo sparse-${logfile}
    sleep 1

    #iotlab-experiment submit -n a2941 -d $d -l grenoble,m3,$nodes_10;
    #iotlab-experiment wait;
    #iotlab-node --update node.iotlab
    #serial_aggregator > dense-${logfile}
    echo dense-${logfile}
    sleep 1
done
