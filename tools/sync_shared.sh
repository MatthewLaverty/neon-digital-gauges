#!/bin/sh
# Copy shared gauge code into the Arduino sketch folders (Arduino can't include files outside the sketch folder).
# Run after editing anything in firmware/gauge/. `sh tools/sync_shared.sh --check` fails if a copy is out of date.
cd "$(dirname "$0")/.." || exit 1
status=0
for dst in firmware/tach-demo/tach_demo; do
  for f in needle_render.h; do
    if [ "$1" = "--check" ]; then cmp -s "firmware/gauge/$f" "$dst/$f" || { echo "out of date: $dst/$f"; status=1; }
    else cp "firmware/gauge/$f" "$dst/$f"; echo "copied $f -> $dst"; fi
  done
done
exit $status
