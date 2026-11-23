#!/usr/bin/env bash
##############################################################################
## sv06.sh: run the Sovol SV06 ACE (Klipper + Moonraker) from the terminal.
##
## Called through symlinks; the link name picks the command:
##   3d                    this list (also any command with -h or --help)
##   3dprint  FILE.gcode   upload and start (asks before overwriting)
##   3dupload FILE.gcode   upload only (asks before overwriting)
##   3dstart  NAME.gcode   start a file already on the printer
##   3dlist                list files on the printer
##   3dstatus              state, progress, temperatures, finish time
##   3dpause | 3dresume | 3dcancel (cancel asks first)
##   3dip                  print H=<printer API address>
##   3dsetip IP[:PORT]     save a new printer address (port default 7125)
##
## Make the links once:  sv06.sh --install [DIR]   (default ~/.local/bin)
## Printer address: SV06_HOST if set, else sv06_host.txt next to this
## script, else 192.168.86.229:7125.
##############################################################################
set -euo pipefail

self=$(readlink "$0" || echo "$0")
conf="$(dirname "$self")/sv06_host.txt"
addr=$( [[ -s $conf ]] && tr -d '[:space:]' < "$conf" || echo 192.168.86.229:7125 )
host="http://${SV06_HOST:-$addr}"
cmds=(3d 3dprint 3dupload 3dstart 3dlist 3dstatus 3dpause 3dresume 3dcancel 3dip 3dsetip)

die()     { echo "error: $*" >&2; exit 1; }
confirm() { local ans; read -r -p "$1 [y/N] " ans; [[ $ans == [yY]* ]]; }
urlenc()  { python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "$1"; }

## GET or POST an API path and fail on a Moonraker error reply
api() {
    local meth=$1 path=$2 out
    out=$(curl -sS -m 15 -X "$meth" "$host$path") || die "printer not reachable at $host"
    python3 -c 'import json, sys; e = json.loads(sys.argv[1]).get("error"); sys.exit(e["message"] if e else 0)' "$out" \
        || die "printer refused $path"
    printf '%s' "$out"
}

remote_files() {
    api GET "/server/files/list?root=gcodes" \
        | python3 -c 'import json, sys; [print(f["path"]) for f in json.load(sys.stdin)["result"]]'
}

state() {
    api GET "/printer/objects/query?print_stats" \
        | python3 -c 'import json, sys; s = json.load(sys.stdin)["result"]["status"]["print_stats"]; print(s["state"], s["filename"], sep="\t")'
}

## refuse while a job is running or paused
need_idle() {
    local st file
    IFS=$'\t' read -r st file < <(state)
    [[ $st == printing || $st == paused ]] && die "printer is $st ($file); wait, or 3dcancel first"
    return 0
}

## check the local file and ask before replacing a copy on the printer
check_upload() {
    local path=$1 name
    [[ -f $path ]]              || die "no such file: $path"
    [[ $path == *.gcode ]]      || die "not a .gcode file: $path"
    name=$(basename "$path")
    if remote_files | grep -qxF "$name"; then
        local st file
        IFS=$'\t' read -r st file < <(state)
        [[ ( $st == printing || $st == paused ) && $file == "$name" ]] \
            && die "$name is the file being printed now; rename the new one"
        echo "warning: $name is already on the printer and will be overwritten"
        confirm "overwrite?" || { echo "nothing sent"; exit 1; }
    fi
}

upload() {
    local path=$1 start=$2 out
    out=$(curl -# -S -X POST -F "file=@$path" -F "print=$start" "$host/server/files/upload") \
        || die "upload failed"
    python3 - "$out" <<'EOF2'
import json, sys
r = json.loads(sys.argv[1])
if "error" in r: sys.exit("error: " + r["error"]["message"])
print("uploaded", r["item"]["path"], "and started" if r.get("print_started") else "")
EOF2
}

do_status() {
    local out meta='{}' file
    out=$(api GET "/printer/objects/query?print_stats&display_status&virtual_sdcard&extruder&heater_bed&gcode_move")
    file=$(python3 -c 'import json, sys; print(json.loads(sys.argv[1])["result"]["status"]["print_stats"]["filename"])' "$out")
    [[ -n $file ]] && meta=$(api GET "/server/files/metadata?filename=$(urlenc "$file")")
    python3 - "$out" "$meta" <<'EOF2'
import json, sys, time
s    = json.loads(sys.argv[1])["result"]["status"]
meta = json.loads(sys.argv[2]).get("result", {})
ps   = s["print_stats"]
frac = s["display_status"]["progress"] or s["virtual_sdcard"]["progress"]
dur  = ps["print_duration"]
cur  = ps["info"]["current_layer"]
tot  = ps["info"]["total_layer"] or meta.get("layer_count")

## no layer markers in the g-code: infer the layer from nozzle height (reads high during a z-hop)
if cur is None and meta.get("layer_height"):
    z0  = meta.get("first_layer_height", meta["layer_height"])
    cur = max(1, round((s["gcode_move"]["gcode_position"][2] - z0) / meta["layer_height"]) + 1)
    cur = min(cur, tot) if tot else cur
print(f"state   : {ps['state']}  {ps['filename']}")
if ps["state"] in ("printing", "paused"):
    print(f"progress: {100 * frac:.1f}%   layer {cur if cur is not None else '?'} of {tot or '?'}")
    print(f"elapsed : {dur / 3600:.2f} h printing, {ps['total_duration'] / 3600:.2f} h total")
    if frac > 0.02:
        rem = dur * (1 / frac - 1)
        print(f"finish  : about {time.strftime('%H:%M %Z', time.localtime(time.time() + rem))} ({rem / 3600:.1f} h left)")
print(f"nozzle  : {s['extruder']['temperature']:.0f} / {s['extruder']['target']:.0f} C")
print(f"bed     : {s['heater_bed']['temperature']:.0f} / {s['heater_bed']['target']:.0f} C")
EOF2
}

install_links() {
    local dir=${1:-$HOME/.local/bin} self
    self=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")
    mkdir -p "$dir"
    for c in "${cmds[@]}"; do ln -sf "$self" "$dir/$c"; done
    echo "linked ${cmds[*]} in $dir"
}

## the header block above, without the comment markers
usage() { sed -n '3,/^####/{/^####/d;p;}' "$self" | sed 's/^## \{0,1\}//'; }

cmd=$(basename "$0")
[[ ${1:-} == -h || ${1:-} == --help ]] && { usage; exit 0; }
case $cmd in
    3d)
        usage ;;
    3dprint)
        [[ $# -eq 1 ]] || die "usage: 3dprint FILE.gcode"
        check_upload "$1"; need_idle; upload "$1" true ;;
    3dupload)
        [[ $# -eq 1 ]] || die "usage: 3dupload FILE.gcode"
        check_upload "$1"; upload "$1" false ;;
    3dstart)
        [[ $# -eq 1 ]] || die "usage: 3dstart NAME.gcode"
        name=$(basename "$1")
        remote_files | grep -qxF "$name" || die "$name is not on the printer (see 3dlist)"
        need_idle
        api POST "/printer/print/start?filename=$(urlenc "$name")" > /dev/null
        echo "started $name" ;;
    3dlist)
        remote_files ;;
    3dip)
        echo "H=$host" ;;
    3dsetip)
        [[ $# -eq 1 ]] || die "usage: 3dsetip IP[:PORT]   (now $host)"
        new=${1#http://}; new=${new%/}
        [[ $new == *:* ]] || new=$new:7125
        if curl -sS -m 5 "http://$new/server/info" > /dev/null 2>&1; then
            echo "printer answers at http://$new"
        else
            echo "warning: no printer answers at http://$new"
            confirm "save it anyway?" || { echo "kept $host"; exit 1; }
        fi
        echo "$new" > "$conf"
        echo "saved $new to $conf"
        [[ -n ${SV06_HOST:-} ]] && echo "note: SV06_HOST=$SV06_HOST is set in this shell and overrides the file"
        exit 0 ;;
    3dstatus)
        do_status ;;
    3dpause)
        api POST /printer/print/pause  > /dev/null; echo "paused" ;;
    3dresume)
        api POST /printer/print/resume > /dev/null; echo "resumed" ;;
    3dcancel)
        IFS=$'\t' read -r st file < <(state)
        [[ $st == printing || $st == paused ]] || die "nothing to cancel (printer is $st)"
        confirm "cancel $file?" || { echo "still printing"; exit 1; }
        api POST /printer/print/cancel > /dev/null; echo "cancelled" ;;
    *)
        [[ ${1:-} == --install ]] && { install_links "${2:-}"; exit 0; }
        usage ;;
esac
