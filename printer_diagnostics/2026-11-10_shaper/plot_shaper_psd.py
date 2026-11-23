## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
'''
Plot power spectral density from Klipper SHAPER_CALIBRATE CSVs on one log
axis, with the tested band shaded.

Usage:
    python3 plot_shaper_psd.py --series file.csv:x:"label":#hex [--series ...] [--out shaper_psd.png] [--title "..."]
'''
import argparse
import csv

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

par = {
    'fmin'   :  5.0,        # [Hz] plot start
    'fmax'   : 75.0,        # [Hz] plot end
    'band_lo': 20.0,        # [Hz] resonance_tester min_freq
    'band_hi': 50.0,        # [Hz] resonance_tester max_freq
    'flabel' : 45.0,        # [Hz] where direct labels sit
    'ink'    : '#2b2b2a',   # primary text
    'muted'  : '#6f6e69',   # secondary text and axes
}


def read_psd(path, axis):
    '''
    Read freq and the axis PSD from a SHAPER_CALIBRATE CSV.

    Args:
        path (str): csv written by SHAPER_CALIBRATE
        axis (str): 'x' or 'y'

    Returns:
        tuple: (freq list, psd list) with zero rows dropped
    '''
    rows = [r for r in csv.DictReader(open(path)) if float(r['psd_' + axis]) > 0]
    freq = [float(r['freq']) for r in rows]
    psd  = [float(r['psd_' + axis]) for r in rows]
    return freq, psd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--series', action='append', required=True, help='file:axis:label:color')
    ap.add_argument('--out'   , default='shaper_psd.png')
    ap.add_argument('--title' , default='SV06 ACE resonance test')
    ap.add_argument('--fmax'   , type=float, default=par['fmax'])
    ap.add_argument('--band_hi', type=float, default=par['band_hi'])
    ap.add_argument('--flabel' , type=float, default=par['flabel'])
    ap.add_argument('--ymax'   , type=float, default=6e5)
    args = ap.parse_args()
    par.update(fmax=args.fmax, band_hi=args.band_hi, flabel=args.flabel)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.axvspan(par['band_lo'], par['band_hi'], color='#efeeea', zorder=0)
    ax.text((par['band_lo'] + par['band_hi']) / 2, args.ymax * 0.5,
            'tested band %g-%g Hz' % (par['band_lo'], par['band_hi']),
            ha='center', color=par['muted'], fontsize=9)

    for s in args.series:
        path, axis, rest = s.split(':', 2)
        label, color     = rest.rsplit(':', 1)
        freq, psd = read_psd(path, axis)
        ax.plot(freq, psd, color=color, lw=2, label=label)
        ## direct label just above the line at flabel
        i = min(range(len(freq)), key=lambda j: abs(freq[j] - par['flabel']))
        ax.text(freq[i], psd[i] * 1.35, label, color=par['ink'], fontsize=9, ha='center', va='bottom')

    ax.set_yscale('log')
    ax.set_xlim(par['fmin'], par['fmax'])
    ax.set_ylim(50, args.ymax)
    ax.set_xlabel('Frequency [Hz]', color=par['ink'])
    ax.set_ylabel('Power spectral density [(mm/s$^2$)$^2$/Hz]', color=par['ink'])
    ax.set_title(args.title, color=par['ink'], fontsize=11, loc='left')
    ax.grid(True, which='major', color='#e4e3df', lw=0.6)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)
    for s in ['left', 'bottom']:
        ax.spines[s].set_color(par['muted'])
    ax.tick_params(colors=par['muted'])
    ax.legend(frameon=False, loc='upper left')
    fig.tight_layout()
    fig.savefig(args.out)
    print(args.out)


if __name__ == '__main__':
    main()
