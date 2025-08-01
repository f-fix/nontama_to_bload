#!/bin/bash --
#
# mkrom - build Warrior's cartridge/mkII/mkIII paged ROM images for games converted from NONTAMA loader
#
# The loader on tape XOR's the game as it reads it into RAM, so use nontama_to_bload.py to convert from P6/P6T to BLOAD format. The expected filename is something like `GAME_0103_5327_0103.bin`. By default all such files in the current directory will be processed. The generated ROM will be `GAME_warrior.rom` or so.

mkrom() {
    local next_page=0
    local prog="$1"
    local entry=$(( 0x$( echo "${prog}" | cut -d . -f 1 | rev | cut -d _ -f 1 | rev ) ))
    local stop_addr=$(( 0x$( echo "${prog}" | cut -d . -f 1 | rev | cut -d _ -f 2 | rev ) ))
    local load_addr=$(( 0x$( echo "${prog}" | cut -d . -f 1 | rev | cut -d _ -f 3 | rev ) ))
    local length=$(( stop_addr - load_addr ))
    local actual_length=$(( $( LC_ALL=C wc -c < "$prog" ) ))
    if [[ $actual_length != $(( 4 + $length )) ]]
    then
        printf "%s: wrong length, expected 0x%04X from filename but got 0x%04X\n" "$prog" "$length" "$actual_length" >&2
        exit 1
    fi
    if [[ :"$( printf "$(printf '\\x%02x' $(( $load_addr & 0xFF )) $(( $load_addr >> 8 )) $(( $stop_addr & 0xFF )) $(( $stop_addr >> 8 )) )" | od -tx1 )" != :"$( dd bs=1 count=4 < "$prog" 2>/dev/null | od -tx1 )" ]]
    then
        printf "%s: filename suffix and BLOAD header do not match\n" "$prog" >&2
        exit 1
    fi
    loader() {
        local start=$(( $1 ))
        local stop=$(( $2 ))
        local exec=$(( $3 ))
        next_page=$(( $next_page + 1))
        LC_ALL=C printf '\x41\x42\x10\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        LC_ALL=C printf '\x00\x00\x00\x00\x00\x00\x3a\xe0\xf3\xe6\xfc\xf6\x02\x32\xe0\xf3'
        LC_ALL=C printf '\x00\x00\x00\xed\x5b\x41\x40\xaf\x2a\x43\x40\xed\x52\x44\x4d\x21'
        LC_ALL=C printf '\x47\x40\xed\xb0\x2a\x45\x40\xe9\x3e'"$( printf '\\x%02x' $(( $next_page )) )"'\xd3\x70\xd3\x32\x18\xc4'
        LC_ALL=C printf '\xfe'"$(printf '\\x%02x' $(( $start & 0xff )) $(( $start >> 8 )) $(( $stop & 0xff )) $(( $stop >> 8 )) $(( $exec & 0xff )) $(( $exec >> 8 ))   )"
    }
    local block_size=$(( 0x2000 - 0x47 ))
    local data_addr=$load_addr
    loader 0xc800 0xc810 0x4038
    LC_ALL=C printf '\x3e\xdd\xd3\xf0\xc3'"$(printf '\\x%02x' $(( $entry & 0xff )) $(( $entry >> 8 )))"'\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    dd bs=1 count=$(( $block_size - ( 0xc810 - 0xc800 ) )) if=/dev/zero
    entry=0xc800
    while [[ $(( $data_addr - $load_addr )) -lt $length ]]
    do
        local block_entry=$entry
        local data_length=$(( $length - ( $data_addr - $load_addr ) ))
        if [[ $data_length -gt $block_size ]]
        then
            block_entry=0x4038
            data_length=$block_size
        fi
        local pad_length=$(( $block_size - $data_length ))
        loader $data_addr $(( $data_addr + $data_length )) $block_entry
        dd bs=1 count=$data_length skip=$(( 4 + $data_addr - $load_addr )) if="$prog"
        dd bs=1 count=$pad_length if=/dev/zero
        data_addr=$(( $data_addr + $data_length ))
    done
}

main() {
    ret=0
    if [[ $# = 0 ]]
    then
        set : *_[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]_[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]_[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].bin
        shift
    fi
    for x in "$@"
    do
        if ! test -f "$x"
        then
            ls -d "$x"
            ret=1
            continue
        fi
        y="${x%_[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]_[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F]_[0-9a-fA-F][0-9a-fA-F][0-9a-fA-F][0-9a-fA-F].bin}_warrior.rom"
        echo "[$x] -> [$y]"
        rm -v -f "$y"
        mkrom "$x" > "$y" &&
            echo "generated $y"
        ret=$(( ret ? ret : $? ))
    done
    exit $ret
}

main "$@"; exit $?
