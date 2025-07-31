#!/usr/bin/env python3

import os
import sys
from functools import reduce

NONTAMA_HEADER_START = b"\xffNONTAMA"
NONTAMA_INITIAL_VALUE = 0xA3

"""Hudson Soft released some games on tape for the NEC PC-6001 mkII
which used a special loader that a lot of modern tools have trouble
with. I will call this loader "NONTAMA" since that is the special
string used to mark the start of the game payload. The name likely
refers to Katsuhiro Nozawa / 野沢 勝広, alias "Nontama", who worked on
several of Hudson Soft's games, and who may be the programmer who
designed and/or implemented this loader too.

At least one of the games that uses this loader, Itasundorious, has
signs of data corruption recorded by Hudson Soft on their tape. This
manifests as wrong text displayed on the screen after the intro screen
and just prior to starting to play the game. The corrupted text was
already corrupted in RAM on Hudson's computer before the game was
XOR'ed and written to tape. The cleanly modulated (... 0x52) 0x13
0x13 0x12 0x32 0x67 0x63 0x67 0x6F 0x6F 0x4F 0x00 0x20 sequence
appears on the tape, and after deobfuscation produces (... 0x20) 0x41
0x00 0x01 0x20 0x55 0x04 0x04 0x08 0x00 0x20 0x4F 0x20, i.e. (... ` `)
`A` `\x00` `月` ` ` `U` `木` `木` `年` `\x00` ` ` `O` ` ` after `I`
` ` `T` ` ` `A` instead of the expected (... 0x20) 0x41 0x20 0x53 0x20
0x55 0x20 0x4E 0x20 0x44 0x20 0x4F 0x20, i.e. (... ` `) `A` ` ` `S`
` ` `U` ` ` `N` ` ` `D` ` ` `O`. To produce the expected text in RAM /
on screen the modulated bytes would instead have been (...  0x52) 0x13
0x33 0x60 0x40 0x15 0x35 0x7B 0x5B 0x1F 0x3F 0x70 0x50... but this
would have changed the bytes for the entire remainder of the
tape. Thus, the data was wrong before it was recorded. Also, the
modulated waveforms show no sign of degradation. in other words, the
software was just shipped by Hudson Soft in a slightly broken/buggy
state.

"""


def nontama_to_bload(b):
    """Extract NONTAMA-loader XOR'ed data from the P6/P6T tape
    image `b` and return it un-XOR'ed and converted to `BLOAD`
    format.

    """
    assert NONTAMA_HEADER_START in b
    import struct

    start_addr, stop_addr, exe_addr = struct.unpack(
        "<HHH", b[b.find(NONTAMA_HEADER_START) + len(NONTAMA_HEADER_START) :][:6]
    )
    assert start_addr < stop_addr
    assert start_addr <= exe_addr
    assert exe_addr < stop_addr
    print(
        f"NONTAMA start_addr=0x{start_addr:04X}, stop_addr=0x{stop_addr:04X}, exe_addr=0x{exe_addr:04X}"
    )
    ciphertext = b[b.find(NONTAMA_HEADER_START) + len(NONTAMA_HEADER_START) + 6 :][
        : stop_addr + 1 - start_addr
    ]
    payload = reduce(
        lambda k_p, c: (c, k_p[1] + bytes([k_p[0] ^ c])),
        ciphertext,
        (NONTAMA_INITIAL_VALUE, b""),
    )[1]
    return (
        struct.pack("<HHH", start_addr, stop_addr, exe_addr) + payload,
        start_addr,
        stop_addr,
        exe_addr,
    )


def main():
    _, infn = (  # usage: python nontama_to_bload.py INPUT.p6  ## writes OUTPUT_start_stop_exe.bin
        sys.argv
    )
    assert os.path.exists(infn)
    p6_in = open(infn, "rb").read()
    bload_out, start_addr, stop_addr, exe_addr = nontama_to_bload(p6_in)
    outfn = f"{os.path.splitext(os.path.basename(infn))[0]}_{start_addr:04x}_{stop_addr:04x}_{exe_addr:04x}.bin"
    if os.path.exists(outfn):
        os.remove(outfn)
        print(f"Removed old {outfn}")
    print(f"Writing {outfn}")
    open(outfn, "wb").write(bload_out)


if __name__ == "__main__":
    main()
