xdotool search --pid 47182 | while read wid; do
  echo "testing $wid"
  xdotool windowactivate "$wid" 2>&1
done
