# Decisions

## Boot time (2026-10-27)

Goal: from flipping the power switch to the startup slip as fast as possible, while keeping
WiFi and SSH working. Times are seconds from kernel start, measured on warm reboots
(firmware adds a few seconds before that on a cold power-on).

| | Startup slip | Ready line | SSH |
| --- | --- | --- | --- |
| Before | ~52 | ~52 | ~110 |
| After | ~18 | ~22 | ~85 |

Changes on the Pi (Raspberry Pi OS Lite 32-bit, Trixie, Pi Zero W):

- `main.py` prints the startup slip before loading the catalog. The last line
  ("... creatures lurk in the vat") prints once the catalog is loaded, as the cue that the
  button is ready.
- The catalog loads from `data/catalog.pkl`, a trimmed pickle of `catalog.json`
  (about 2 s instead of 11 s). It is rebuilt automatically when `catalog.json` is newer.
- python-escpos 3.1 caches its printer database in a new temp dir on every start, so it
  re-parsed the YAML each boot (8.5 s). The service sets `ESCPOS_CAPABILITIES_PICKLE_DIR`
  to a persistent folder.
- [`system/momir.service`](../system/momir.service): starts as soon as `/` is mounted
  (still read-only), in parallel with fsck and the read-write remount. Its working
  directory is `/run/momir`, because lgpio creates its notify pipe there.
- `/boot/firmware/config.txt`: `auto_initramfs=0` (kernel stage 11 s to 4 s; the SD card
  and ext4 drivers are built into the kernel), `dtoverlay=disable-bt`, and the
  `vc4-kms-v3d` display overlay commented out.
- Swap off (`/etc/rpi/swap.conf.d/90-no-swap.conf`: `Mechanism=none`).
- Disabled: keyboard-setup, console-setup, rpi-eeprom-update, sshswitch, getty@tty1,
  NetworkManager-wait-online.

Kept on purpose: the root filesystem check (the power switch cuts power hard), WiFi,
NetworkManager, SSH, avahi and Raspberry Pi Connect.

Undo: if the Pi stops booting, put the SD card in any computer and set
`auto_initramfs=1` in `config.txt` on the boot partition. To use Bluetooth again, remove
`dtoverlay=disable-bt`.

Open: Python imports take about 3 s on an idle Pi and about 8 s during boot, while the
rest of the system starts up.
