#!/bin/bash
sudo find /var/lib/docker/volumes/jenkins_jenkins_data/_data/workspace -mindepth 1 -type d -exec rm -rf {} +

