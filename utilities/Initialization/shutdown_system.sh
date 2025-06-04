#!/bin/bash

ssh -t admin@192.168.2.1 'sudo shutdown now' ||

sleep 1

ssh -t admin@192.168.2.205 'sudo shutdown now' ||

sleep 1

sudo shutdown now