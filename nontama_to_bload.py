#!/usr/bin/env python3

import os
import sys
import unicodedata
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

IHEX_START=b'\r\n:'
LOAD_NAME_PREFIX=b'Found:'

def nontama_to_bload(b):
    """Extract NONTAMA-loader XOR'ed data from the P6/P6T tape
    image `b` and return it un-XOR'ed and converted to `BLOAD`
    format.

    """
    assert NONTAMA_HEADER_START in b
    import struct

    start_addr, last_addr, exe_addr = struct.unpack(
        "<HHH", b[b.find(NONTAMA_HEADER_START) + len(NONTAMA_HEADER_START) :][:6]
    )
    assert start_addr < last_addr
    stop_addr = last_addr + 1
    payload_start = b.find(NONTAMA_HEADER_START) + len(NONTAMA_HEADER_START) + 6
    load_name = None
    potential_loader = b[:b.find(NONTAMA_HEADER_START)]
    if IHEX_START in potential_loader:
        ihex = potential_loader[potential_loader.find(IHEX_START):]
        ihex = ihex[:ihex.find(b'\0')]
        ihex=ihex.rstrip(b'\x1A')
        loader_payload = b""
        loader_addr = None
        for line in ihex.split(b'\r\n'):
            if line.startswith(b':') and len(line) % 2 == 1:
                try:
                    int(line[1:], 16)
                except:
                    continue
                data_bytes = int(line[1:3], 16)
                if not data_bytes:
                    break
                ihex_addr = int(line[3:7], 16)
                record_type = int(line[7:9], 16)
                if record_type == 0x01:
                    break
                if record_type != 0x00:
                    continue
                if len(line) == 1 + 2 + 4 + 2 + 2 * data_bytes + 2:
                    checksum_zeroing_byte = int(line[-2:], 16)
                    ihex_data = bytes([int(line[1 + 2 + 4 + 2 + 2 * i:][:2], 16) for i in range(data_bytes)])
                    if sum(int(line[i:i + 2], 16) for i in range(1, len(line), 2)) & 0xFF == 0x00:
                        if loader_addr is None:
                            loader_addr = ihex_addr
                            loader_payload = ihex_data
                        else:
                            if ihex_addr < loader_addr:
                                loader_payload = ihex_data + (b"\0" * (loader_addr - ihex_addr) + loader_payload)[len(ihex_data):]
                                loader_addr = ihex_addr
                            else:
                                loader_payload = (loader_payload + (b"\0" * (ihex_addr - loader_addr)))[:(ihex_addr - loader_addr)] + ihex_data
        if LOAD_NAME_PREFIX in loader_payload:
            load_name = loader_payload[loader_payload.find(LOAD_NAME_PREFIX) + len(LOAD_NAME_PREFIX):].split(b'\0')[0].split(b'\n')[0].split(b'\r')[0].strip(b' \t') or None
    print(
        f"NONTAMA start_addr=0x{start_addr:04X}, stop_addr=0x{stop_addr:04X}, exe_addr=0x{exe_addr:04X}, load_name={load_name}"
    )
    ciphertext = b[payload_start:][:stop_addr-start_addr]
    payload = reduce(
        lambda k_p, c: (c, k_p[1] + bytes([k_p[0] ^ c])),
        ciphertext,
        (NONTAMA_INITIAL_VALUE, b""),
    )[1]
    return (
        struct.pack("<HH", start_addr, stop_addr) + payload,
        load_name,
        start_addr,
        stop_addr,
        exe_addr,
        b[payload_start+stop_addr-start_addr:],
    )


NO_CONTROLS = b""
MINIMAL_CONTROLS = b"\0\r\n\x1a\x7f"
ASCII_CONTROLS = bytes(range(0x20)) + b"\x7f"

# i am sure this is not the best way to solve this. this mapping
# should work OK for PC-6001/mkII/SR and PC-6601/SR. it does not
# handle the alternate character set shift sequences well. it also
# does not handle Kanji or PC-6001A charset at all! the mapping is
# intentionally close to the PC-98 one above. the hiragana and kanji
# here should all be half-width ones, but Unicode is missing those so
# we live with fullwidth instead.
PC6001_8BIT_CHARSET = (
    "␀␁␂␃␄␅␆␇␈␉␊␋␌␍␎␏␐␑␒␓␔␕␖␗␘␙␚␛￫￩￪￬"
    " !\"#$%&'()*+,-./0123456789:;<=>?"
    "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[¥]^_"
    "`abcdefghijklmnopqrstuvwxyz{¦}~␡"
    "♠♥♦♣￮•をぁぃぅぇぉゃゅょっーあいうえおかきくけこさしすせそ"
    "\uf8f0｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ"
    "ﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ"
    "たちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん\uf8f2\uf8f3"
)
assert len(PC6001_8BIT_CHARSET) == 256
PC6001_8BIT_ALTCHARSET = "\uf8f1月火水木金土日年円時分秒百千万" "π┴┬┤├┼│─┌┐└┘╳大中小"
assert len(PC6001_8BIT_ALTCHARSET) == 32
PC6001_8BIT_CHARMAP = {PC6001_8BIT_CHARSET[i]: bytes([i]) for i in range(256)} | {
    PC6001_8BIT_ALTCHARSET[i]: bytes([0x14, i + 0x30]) for i in range(32)
}
PC6001_8BIT_CHARMAP_COMPAT = {
    unicodedata.normalize("NFKD", key): value
    for key, value in PC6001_8BIT_CHARMAP.items()
    if unicodedata.normalize("NFKD", key) != key
}


def encode_pc6001_8bit_charset(s, try_harder=True):
    s = "".join(
        [
            (
                unicodedata.normalize("NFKD", s[i : i + 1])
                if (
                    unicodedata.name(s[i : i + 1], "?")
                    .lower()
                    .startswith("hiragana letter")
                    or unicodedata.name(s[i : i + 1], "?")
                    .lower()
                    .startswith("katakana letter")
                )
                else s[i : i + 1]
            )
            for i in range(len(s))
        ]
    )
    byts, chars_consumed, num_chars = b"", 0, len(s)
    while chars_consumed < num_chars:
        ch = s[chars_consumed]
        byt = PC6001_8BIT_CHARMAP.get(ch, PC6001_8BIT_CHARMAP_COMPAT.get(ch)) or (
            bytes([ord(ch)]) if ord(ch) <= 0x7F else None
        )
        if byt is None and try_harder:
            cch = unicodedata.normalize("NFKD", ch)
            byt = PC6001_8BIT_CHARMAP.get(cch, PC6001_8BIT_CHARMAP_COMPAT.get(cch)) or (
                bytes([ord(cch)]) if ord(cch) <= 0x7F else None
            )
        if byt is None:
            raise UnicodeEncodeError(
                "pc6001-8bit",
                s,
                chars_consumed,
                chars_consumed + 1,
                f"no mapping for U+{ord(ch):04X} {unicodedata.name(ch, repr(ch))}",
            )
        byts += byt
        chars_consumed += 1
    return byts


def decode_pc6001_8bit_charset(byts, preserve=MINIMAL_CONTROLS):
    s, bytes_consumed, num_bytes = "", 0, len(byts)
    while bytes_consumed < num_bytes:
        byt = byts[bytes_consumed]
        if (
            bytes_consumed > 0
            and byts[bytes_consumed - 1] == 0x14
            and byt >= 0x30
            and byt <= 0x4F
        ):
            s = (
                s[: -len(PC6001_8BIT_CHARSET[0x14])]
                + PC6001_8BIT_ALTCHARSET[byt - 0x30]
            )
        elif byt in preserve:
            s += chr(byt)
        else:
            s += PC6001_8BIT_CHARSET[byt]
        if (
            len(s) > 1
            and s[-1:]
            in "\N{HALFWIDTH KATAKANA VOICED SOUND MARK}\N{HALFWIDTH KATAKANA SEMI-VOICED SOUND MARK}"
            and unicodedata.name(s[-2:-1], "?").lower().startswith("hiragana letter")
        ):
            s = s[:-2] + unicodedata.normalize("NFKC", s[-2:])
        bytes_consumed += 1
    round_trip_byts = encode_pc6001_8bit_charset(s)
    assert byts == round_trip_byts, UnicodeDecodeError(
        "pc6001-8bit",
        byts,
        0,
        num_bytes,
        f"round-trip failure for {repr(s)} with preserve={repr(preserve)}; result:\n {repr(byts)}, got:\n {repr(round_trip_byts)}",
    )
    return s


def main():
    _, infn = (  # usage: python nontama_to_bload.py INPUT.p6  ## writes OUTPUT[_name][_loadNN]_start_stop_exe.bin
        sys.argv
    )
    assert os.path.exists(infn)
    p6_in = open(infn, "rb").read()
    results = []
    while True:
        bload_out, load_name, start_addr, stop_addr, exe_addr, p6_in = nontama_to_bload(p6_in)
        results.append(dict(bload_out=bload_out, load_name=load_name, start_addr=start_addr, stop_addr=stop_addr, exe_addr=exe_addr))
        if not NONTAMA_HEADER_START in p6_in:
            break
    for i, result in enumerate(results):
        bload_out, load_name, start_addr, stop_addr, exe_addr = result['bload_out'], result['load_name'], result['start_addr'], result['stop_addr'], result['exe_addr']
        load_suffix = '' if len(results) == 1 else f"_load{1 + i:02d}"
        if load_name is not None:
            load_name_unicode = decode_pc6001_8bit_charset(load_name)
            load_name_fs_safe = ''
            for i, ch in enumerate(load_name_unicode):
                if ch in set('"*+,/:;<=>?[\\]|\x7f¥¦') | set(chr(i) for i in range(0x20)):
                    ch = "_"
                load_name_fs_safe += ch
            load_suffix = f"_{load_name_fs_safe}" + load_suffix
        outfn = f"{os.path.splitext(os.path.basename(infn))[0]}{load_suffix}_{start_addr:04x}_{stop_addr:04x}_{exe_addr:04x}.bin"
        if os.path.exists(outfn):
            os.remove(outfn)
            print(f"Removed old {outfn}")
        print(f"Writing {outfn}")
        open(outfn, "wb").write(bload_out)


if __name__ == "__main__":
    main()
