# This command has to be run in the terminal at the (qemu) prompt, after starting qemu with -monitor stdio
# The name of the snapshot here is 'instant'
# savevm instant

# Adding this to vm-spawn.sh will ensure that the saved VM state is loaded.
# -loadvm instant

# This command should be run at (qemu) prompt to view a list of snapshots
# info snapshots

# Delete a snapshot
# delvm instant
