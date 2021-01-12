#!/bin/bash

pgrep 'python3' | awk '{print $1}' | xargs pwdx