#!/bin/bash

rsync -azPhuvO --no-p --no-o --no-g ~/Documents/Autocross_TimingControl/TrafficLightWebcam/StartLineImages/ nick@track-ops-server:/startline_photo_sync/
