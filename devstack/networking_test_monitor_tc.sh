#!/bin/bash
IF=lo
watch -n1 "tc -p -s -d  qdisc show dev $IF; echo; tc class show dev $IF; echo; tc filter show dev $IF"
