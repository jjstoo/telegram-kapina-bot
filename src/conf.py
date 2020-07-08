"""
Configuration is done here
"""

# Snapshot filename
snapshot_output_file = "snapshot.jpg"

# This is built dynamically later on when the bot is initialized
beer_tap_triggers = []

# Command triggers
triggers = {"image": "/kapina",
            "help": "/help",
            "drink_records": "/kaljat"}

# Triggers for adding drink records
drink_triggers = {"beer": "/kalja",
                  "booze": "/viina",
                  "wine": "/viini"}


# Thread pool size for smooth handling of multiple requests
pool_size = 10
