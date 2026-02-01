xdotool search --pid 47182 | while read wid; do
  xdotool windowactivate "$wid" 2>&1
done
