#!/bin/bash
magick montage stats_RCM.png stats_IS.png stats_I.png stats_II.png stats_III.png -mode Concatenate -tile 1x stats.png
