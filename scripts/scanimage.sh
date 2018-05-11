#!/bin/bash

scanimage -d 'brother4:net1;dev0' --format tiff --batch  --batch-start 0 --batch-count 19 -p --resolution 200 --mode '24bit Color'
