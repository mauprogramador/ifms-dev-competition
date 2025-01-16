# e.g. 127.0.0.1, 0.0.0.0
HOST_PATTERN = r"^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$"

# e.g. \033[35;1m, \033[m
ANSI_ESCAPE_PATTERN = r"\x1b\[[0-9\;]*m"

# e.g. GTFS
CODE_PATTERN = r"^[a-zA-Z]{4}$"
