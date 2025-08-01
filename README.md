# nontama_to_bload
convert PC-6001 mkII NONTAMA-loader tape images to normal BLOAD files

# Usage
```
usage: python nontama_to_bload.py INPUT.p6  ## writes OUTPUT_start_stop_exe.bin
```
Afterward, you can run `python mkrom.py` to make Warrior bootable cartridge conversions from the BLOAD files

# History
Hudson Soft released some games on tape for the NEC PC-6001 mkII which used a special loader that a lot of modern tools have trouble with. I will call this loader "NONTAMA" since that is the special string used to mark the start of the game payload. The name likely refers to Katsuhiro Nozawa / 野沢 勝広, alias "Nontama", who worked on
several of Hudson Soft's games, and who may be the programmer who designed and/or implemented this loader too.

## Trivia
At least one of the games that uses this loader, Itasundorious, has signs of data corruption recorded by Hudson Soft on their tape. This manifests as wrong text displayed on the screen after the intro screen and just prior to starting to play the game. The corrupted text was already corrupted in RAM on Hudson's computer before the game was XOR'ed and written to tape. The cleanly modulated (... 0x52) 0x13 0x13 0x12 0x32 0x67 0x63 0x67 0x6F 0x6F 0x4F 0x00 0x20 sequence appears on the tape, and after XOR it produces (... 0x20) 0x41 0x00 0x01 0x20 0x55 0x04 0x04 0x08 0x00 0x20 0x4F 0x20, i.e. (... ` `) `A` `\x00` `月` ` ` `U` `木` `木` `年` `\x00` ` ` `O` ` ` after `I` ` ` `T` ` ` `A` instead of the expected (... 0x20) 0x41 0x20 0x53 0x20 0x55 0x20 0x4E 0x20 0x44 0x20 0x4F 0x20, i.e. (... ` `) `A` ` ` `S` ` ` `U` ` ` `N` ` ` `D` ` ` `O`. To produce the expected text in RAM / on screen the modulated bytes would instead have been (...  0x52) 0x13 0x33 0x60 0x40 0x15 0x35 0x7B 0x5B 0x1F 0x3F 0x70 0x50... but this would have changed the bytes for the entire remainder of the tape. Thus, the data was wrong before it was recorded. Also, the modulated waveforms show no sign of degradation. in other words, the software was just shipped by Hudson Soft in a slightly broken/buggy state.

This tool was initially created in order to understand whether my Itasundorious tape was damaged (it wasn't, or rather the damage happened before the tape was written.) It has since been used successfully with `Itasundorious`/`イタサンドリアス`, `Cannon Ball`/`キャノンボール`, `Dimensional Wars (Jigen Sensou)`/`ディメンジョナルウォーズ（次元戦争）`, `Punchball ***** Bros.`/`パンチボール〇〇〇ブラザーズ`, `Salad no Kuni no Tomato-hime`/`サラダの国のトマト姫`, `Yakyuukyou`/`野球狂`, and the first chapter of `Dezeni Land`/`デゼニランド` (might work for the remaining chapters too; it gets far enough to ask for your save tape at least...)

At least one PC-8801 game uses a loader with the string `\xFF` `N` `O` `N` `T` `A` `M` `A` in it too, and the same header structure, but that one does not use XOR - the data on the tape is loaded into memory verbatim.
