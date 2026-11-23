#!/usr/bin/env bash
##############################################################################
## apply.sh: make the SV06 ACE camera light work from BOTH the touchscreen
## and Mainsail/Obico. Run from this folder on the Mac, only when the printer
## is idle (it refuses during a print). Staged 2026-11-22 09:39 MST.
##
## Steps:
##   1. install gcode_shell_command.py into Klipper (from ~/kiauh/resources)
##   2. install /usr/local/bin/cameralight (root-owned, writes the sysfs pin)
##   3. back up and replace printer_data/config/light.cfg (printer.cfg already
##      has [include light.cfg], so it is not touched)
##   4. stop the screen app, restore the original mksclient from
##      mksclient.backup, restart Klipper (frees the pin), start the screen app
##   5. check the screen app exported gpio67, then test LIGHT_ON
##
## Undo: copy light.cfg.before-both back over light.cfg, re-run
## ~/light_setup.py on the printer (re-patches mksclient), FIRMWARE_RESTART.
##############################################################################
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
ssh_host=${SV06_SSH:-printer}
api="http://$(tr -d '[:space:]' < "$here/../../sv06_host.txt")"

die() { echo "STOP: $*" >&2; exit 1; }
say() { echo "==> $*"; }

state=$(curl -sS -m 10 "$api/printer/objects/query?print_stats=state" \
    | python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["status"]["print_stats"]["state"])') \
    || die "printer not reachable at $api"
[[ $state == printing || $state == paused ]] && die "print state is '$state'; run this after the print"
say "print state: $state"

scp -q "$here/light.cfg" "$here/cameralight" "$ssh_host:/tmp/"

ssh "$ssh_host" 'bash -s' <<'REMOTE'
set -euo pipefail
cfg=~/printer_data/config
bin=~/printer_data/build/mksclient
say() { echo "==> $*"; }

cp ~/kiauh/resources/gcode_shell_command.py ~/klipper/klippy/extras/
grep -qx 'klippy/extras/gcode_shell_command.py' ~/klipper/.git/info/exclude \
    || echo 'klippy/extras/gcode_shell_command.py' >> ~/klipper/.git/info/exclude
say "installed gcode_shell_command.py"

sudo install -o root -g root -m 755 /tmp/cameralight /usr/local/bin/cameralight
say "installed /usr/local/bin/cameralight"

[ -e "$cfg/light.cfg.before-both" ] || cp -p "$cfg/light.cfg" "$cfg/light.cfg.before-both"
cp /tmp/light.cfg "$cfg/light.cfg"
rm -f /tmp/light.cfg /tmp/cameralight
say "replaced light.cfg (old one: light.cfg.before-both)"

sudo systemctl stop makerbase-client.service
cmp -s "$bin" "$bin.backup" || sudo cp "$bin.backup" "$bin"
say "screen app restored to original"

curl -s -X POST http://127.0.0.1:7125/printer/firmware_restart > /dev/null || true
for i in $(seq 40); do
    sleep 3
    st=$(curl -s http://127.0.0.1:7125/printer/info | python3 -c 'import json, sys; print(json.load(sys.stdin)["result"]["state"])' 2>/dev/null || echo down)
    [ "$st" = ready ] && break
    [ "$st" = error ] && { echo "STOP: Klipper error, check Mainsail"; exit 1; }
done
[ "$st" = ready ] || { echo "STOP: Klipper not ready after 2 min"; exit 1; }
say "Klipper ready"

sudo systemctl start makerbase-client.service
sleep 10
[ -e /sys/class/gpio/gpio67 ] && say "screen app owns gpio67" \
    || say "gpio67 not exported yet (cameralight will export it on first use)"

curl -s -X POST "http://127.0.0.1:7125/printer/gcode/script?script=LIGHT_ON" > /dev/null
say "LIGHT_ON sent; gpio67 value = $(cat /sys/class/gpio/gpio67/value)"
REMOTE
say "done: try the touchscreen light button, then LIGHT_OFF / LIGHT_ON in Mainsail"
