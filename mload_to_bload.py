#!/usr/bin/env python3

import os
import os.path
import sys
import unicodedata

"""
This converts the "M" loader (my name, I don't know what they called it) used in many Hudson Soft / Honeybee Soft MSX tape games to normal MSX BLOAD.
"""

MSX_CAS_HEADER = b"\x1f\xa6\xde\xba\xcc\x13\x7d\x74"

MSX_BLOAD_MAGIC = b"\xfe"  # Used by MSX Disk BASIC to mark BLOAD data

MSX_CAS_BLOAD_HEADER_MAGIC = 10 * b"\xd0"
MSX_CAS_BLOAD_FOOTER_MAGIC = 10 * b"\x00"
MSX_CAS_ASCII_BASIC_HEADER_MAGIC = 10 * b"\xea"


def mload_to_bload(mload_cas_data):
    assert mload_cas_data.startswith(
        MSX_CAS_HEADER
    ), f"This does not appear to be an MSX CAS file (missing header {MSX_CAS_HEADER})"
    mload_data_blocks = mload_cas_data.split(MSX_CAS_HEADER)
    if (
        len(mload_data_blocks) >= 6
        and MSX_CAS_ASCII_BASIC_HEADER_MAGIC in mload_data_blocks[1]
    ):
        # elide ASCII BASIC pre-loader
        mload_data_blocks = mload_data_blocks[:1] + mload_data_blocks[3:]
    assert len(mload_data_blocks) >= 4, f"Not enough tape blocks to hold a mload loader"
    header_block = mload_data_blocks[1]
    assert (
        len(header_block) >= 16
    ), f"First or second CAS block must contain the mload loader's BLOAD header"
    assert (
        MSX_CAS_BLOAD_HEADER_MAGIC in header_block
    ), f"First or second CAS block must contain the mload loader's BLOAD header"
    load_name = (
        header_block.split(MSX_CAS_BLOAD_HEADER_MAGIC)[1]
        .lstrip(b"\xd0")[:6]
        .rstrip(b" ")
    )
    mload_data = mload_data_blocks[3]
    assert len(mload_data) > 4
    payload_sz = int.from_bytes(mload_data[:2], "little")
    load_addr = int.from_bytes(mload_data[2:4], "little")
    mload_data = mload_data[4:]
    assert payload_sz <= len(
        mload_data
    ), f"Not enough bytes in block for payload (remaining block size {len(mload_data)}, payload size {payload_sz})"
    decoded = b""
    bitsum = 0x00
    while len(decoded) < payload_sz:
        byt, mload_data = mload_data[0], mload_data[1:]
        byt ^= (load_addr + len(decoded)) & 0xFF
        decoded = decoded + bytes([byt])
        for bitpos in range(8):
            if byt & (1 << bitpos):
                bitsum = (bitsum + 1) & 0xFF
        if (payload_sz - len(decoded)) & 0xFF == 0x00:
            check_byt, mload_data = mload_data[0], mload_data[1:]
            assert (
                bitsum == check_byt
            ), f"Wrong check byte after decoding {len(decoded)} data bytes; expected 0x{check_byt:02X} but computed 0x{bitsum:02X}, {decoded}"
            bitsum = 0x00
    assert len(mload_data) >= 2
    exe_addr, mload_data = int.from_bytes(mload_data[:2], "little"), mload_data[2:]
    stop_addr = load_addr + payload_sz
    bload_out = (
        MSX_BLOAD_MAGIC
        + load_addr.to_bytes(2, "little")
        + stop_addr.to_bytes(2, "little")
        + exe_addr.to_bytes(2, "little")
        + decoded
    )
    cas_bload_out = (
        MSX_CAS_HEADER
        + MSX_CAS_BLOAD_HEADER_MAGIC
        + load_name
        + (b" " * (6 - len(load_name)))
        + MSX_CAS_HEADER
        + load_addr.to_bytes(2, "little")
        + stop_addr.to_bytes(2, "little")
        + exe_addr.to_bytes(2, "little")
        + decoded
        + MSX_CAS_BLOAD_FOOTER_MAGIC
    )
    return load_name, load_addr, stop_addr, exe_addr, bload_out, cas_bload_out


NO_CONTROLS = b""
MINIMAL_CONTROLS = b"\0\r\n\x1a\x7f"
ASCII_CONTROLS = bytes(range(0x20)) + b"\x7f"

# i am sure this is not the best way to solve this. this mapping
# should work OK for 8-bit character data from Japanese MSX's. it does
# not handle the alternate character set shift sequences well. it also
# does not handle Kanji or overseas charsets at all! the hiragana and
# kanji here should all be half-width ones, but Unicode is missing
# those so we live with fullwidth instead. the arrows and control
# pictures shown here in the first row are actually control characters
# and are not graphically displayable on an MSX.
MSX_8BIT_CHARSET = (
    "␀␁␂␃␄␅␆␇␈␉␊␋␌␍␎␏␐␑␒␓␔␕␖␗␘␙␚␛￫￩￪￬"
    " !\"#$%&'()*+,-./0123456789:;<=>?"
    "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[¥]^_"
    "`abcdefghijklmnopqrstuvwxyz{¦}~␡"
    "♠♥♦♣￮•をぁぃぅぇぉゃゅょっ\uf8f4あいうえおかきくけこさしすせそ"
    "\uf8f0｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿ"
    "ﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ"
    "たちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん\uf8f2\uf8f3"
)
assert len(MSX_8BIT_CHARSET) == 256
MSX_8BIT_ALTCHARSET = "\uf8f1月火水木金土日年円時分秒百千万" "π┴┬┤├┼│─┌┐└┘╳大中小"
assert len(MSX_8BIT_ALTCHARSET) == 32
MSX_8BIT_CHARMAP = {MSX_8BIT_CHARSET[i]: bytes([i]) for i in range(256)} | {
    MSX_8BIT_ALTCHARSET[i]: bytes([0x01, i + 0x40]) for i in range(32)
}
MSX_8BIT_CHARMAP_COMPAT = {
    unicodedata.normalize("NFKD", key): value
    for key, value in MSX_8BIT_CHARMAP.items()
    if unicodedata.normalize("NFKD", key) != key
} | {
    "\N{KATAKANA-HIRAGANA VOICED SOUND MARK}": MSX_8BIT_CHARMAP[
        "\N{HALFWIDTH KATAKANA VOICED SOUND MARK}"
    ],
    "\N{KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK}": MSX_8BIT_CHARMAP[
        "\N{HALFWIDTH KATAKANA SEMI-VOICED SOUND MARK}"
    ],
    "\N{KATAKANA-HIRAGANA PROLONGED SOUND MARK}": MSX_8BIT_CHARMAP[
        "\N{HALFWIDTH KATAKANA-HIRAGANA PROLONGED SOUND MARK}"
    ],
}


def encode_msx_8bit_charset(s, try_harder=True):
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
                else (
                    "~"
                    if s[i : i + 1] == "\N{WAVE DASH}"
                    else "-" if s[i : i + 1] == "\N{HYPHEN}" else s[i : i + 1]
                )
            )
            for i in range(len(s))
        ]
    )
    byts, chars_consumed, num_chars = b"", 0, len(s)
    while chars_consumed < num_chars:
        ch = s[chars_consumed]
        byt = MSX_8BIT_CHARMAP.get(ch, MSX_8BIT_CHARMAP_COMPAT.get(ch)) or (
            bytes([ord(ch)]) if ord(ch) <= 0x7F else None
        )
        if byt is None and try_harder:
            cch = unicodedata.normalize("NFKD", ch)
            byt = MSX_8BIT_CHARMAP.get(cch, MSX_8BIT_CHARMAP_COMPAT.get(cch)) or (
                bytes([ord(cch)]) if len(cch) == 1 and ord(cch) <= 0x7F else None
            )
        if byt is None:
            raise UnicodeEncodeError(
                "msx-8bit",
                s,
                chars_consumed,
                chars_consumed + 1,
                f"no mapping for U+{ord(ch):04X} {unicodedata.name(ch, repr(ch))}",
            )
        byts += byt
        chars_consumed += 1
    return byts


def decode_msx_8bit_charset(byts, preserve=MINIMAL_CONTROLS):
    s, bytes_consumed, num_bytes = "", 0, len(byts)
    while bytes_consumed < num_bytes:
        byt = byts[bytes_consumed]
        if (
            bytes_consumed > 0
            and byts[bytes_consumed - 1] == 0x01
            and byt >= 0x40
            and byt <= 0x5F
        ):
            s = s[: -len(MSX_8BIT_CHARSET[0x01])] + MSX_8BIT_ALTCHARSET[byt - 0x40]
        elif byt in preserve:
            s += chr(byt)
        else:
            s += MSX_8BIT_CHARSET[byt]
        if (
            len(s) > 1
            and s[-1:]
            in "\N{HALFWIDTH KATAKANA VOICED SOUND MARK}\N{HALFWIDTH KATAKANA SEMI-VOICED SOUND MARK}"
            and unicodedata.name(s[-2:-1], "?").lower().startswith("hiragana letter")
        ):
            s = s[:-2] + unicodedata.normalize("NFKC", s[-2:])
        bytes_consumed += 1
    round_trip_byts = encode_msx_8bit_charset(s)
    assert byts == round_trip_byts, UnicodeDecodeError(
        "msx-8bit",
        byts,
        0,
        num_bytes,
        f"round-trip failure for {repr(s)} with preserve={repr(preserve)}; result:\n {repr(byts)}, got:\n {repr(round_trip_byts)}",
    )
    return s


def main():
    _, infn = (
        sys.argv
    )  # usage: python3 mload_to_bload.py [/PATH/TO/]TAPE.cas  ## generates MSX Disk BASIC BLOAD data file ./TAPE_LOAD_XXXX_YYYY_ZZZZ.bin where LOAD is loader name, XXXX is hexadecimal load start address, YYYY is hexadecimal load stop address, and ZZZZ is hexadecimal entry point; also generates MSX CAS file loadable using BLOAD ./TAPE_LOAD_XXXX_YYYY_ZZZZ_bin.cas
    mload_cas_data = open(infn, "rb").read()
    load_name, load_addr, stop_addr, exe_addr, bload_out, cas_bload_out = (
        mload_to_bload(mload_cas_data)
    )
    load_suffix = ""
    if load_name is not None:
        load_name_unicode = decode_msx_8bit_charset(load_name)
        load_name_fs_safe = ""
        for i, ch in enumerate(load_name_unicode):
            if ch in set('"*+,/:;<=>?[\\]|\x7f¥¦') | set(chr(i) for i in range(0x20)):
                ch = "_"
            load_name_fs_safe += ch
        load_suffix = f"_{load_name_fs_safe}" + load_suffix
    outfn = f"{os.path.splitext(os.path.basename(infn))[0]}{load_suffix}_{load_addr:04X}_{stop_addr:04X}_{exe_addr:04X}.bin"
    if os.path.exists(outfn):
        os.remove(outfn)
        print(f"Removed old {outfn}")
    print(f"Writing {outfn}")
    open(outfn, "wb").write(bload_out)
    cas_outfn = f"{os.path.splitext(os.path.basename(infn))[0]}{load_suffix}_{load_addr:04X}_{stop_addr:04X}_{exe_addr:04X}_bin.cas"
    if os.path.exists(cas_outfn):
        os.remove(cas_outfn)
        print(f"Removed old {cas_outfn}")
    print(f"Writing {cas_outfn}")
    open(cas_outfn, "wb").write(cas_bload_out)


if __name__ == "__main__":
    main()
