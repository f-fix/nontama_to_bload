# nontama_to_bload
convert PC-6001 mkII NONTAMA-loader tape images to normal PC-6001 BLOAD files

# Usage
```
usage: python nontama_to_bload.py INPUT.p6  ## writes OUTPUT[_name][_loadNN]_start_stop_exe.bin
```
Afterward, you can run `python mkrom.py` to make Warrior bootable cartridge conversions from the BLOAD files

# mload_to_bload
convert MSX "M"-loader (my name, I don't know what they called it) tape images to normal MSX BLOAD files

# Usage
```
usage: python mload_to_bload.py INPUT.cas  ## writes INPUT[_name]_start_stop_exe.bin and INPUT[_name]_start_stop_exe_bin.cas
```

# Compatibility
The nontama_to_bload tool was initially created in order to understand whether my Itasundorious tape was damaged (it wasn't, or rather the damage happened before the tape was written.) It has since been used successfully with:
- `Itasundorious`/`イタサンドリアス`
- `Cannon Ball`/`キャノンボール`
- `Gang Man`/`ギャングマン`
- `Ginkou Goutou (Machinegun Joe vs. the Mafia)`/`銀行強盗（マシンガンジョー VS ザ・マフィア）`
- `Salad no Kuni no Tomato-hime`/`サラダの国のトマト姫`
- `3-biki no Kobuta no Daibouken` `STEP 1`/`３びきの子ぶたの大冒険` `STEP1`
- `Dimensional Wars (Jigen Sensou)`/`ディメンジョナルウォーズ（次元戦争）`
- `Dezeni Land`/`デゼニランド`
- `Nuts & Milk`/`ナッツ&ミルク`
- `Power Fail`/`パワーフェイル`
- `Punchball ***** Bros.`/`パンチボール〇〇〇ブラザーズ`
- `Hitsuji Yai!`/`ひつじや～い！` 
- `***** Bros. Special`/`〇〇〇ブラザーズSPECIAL`
- `Yakyuukyou`/`野球狂`

The mload_to_bload tool was initially created in order to understand whether my Vegetable Crash tape was OK (it was!) It has since been used successfully with:
- `Binary Land` (Hudson Soft) (UK)
- `Fire Rescure` (Hudson Soft) (UK)
- `Stop the Express` (Hudson Soft) (Aackosoft - Eaglesoft) (Europe?)
- `Tanque Destructor`/`Driller Tank` (Hudson Soft) (Indescomp) (Sony) (Spain)
- `Vegetable Crash`/`ベジタブルクラッシュ` (Honeybee Soft) (Hudson Soft) (Japan)
- `Zero Fighter`/`ゼロファイター` (Honeybee Soft) (Hudson Soft) (Japan)

# History
Hudson Soft released some games on tape for the NEC PC-6001 mkII which used a special loader that a lot of modern tools have trouble with. I will call this loader "NONTAMA" since that is the special string used to mark the start of the game payload. The name likely refers to Katsuhiro Nozawa / 野沢 勝広, alias "Nontama", who worked on
several of Hudson Soft's games, and who may be the programmer who designed and/or implemented this loader too.

## Trivia
At least one of the games that uses this loader, Itasundorious, has signs of data corruption recorded by Hudson Soft on their tape. This manifests as wrong text displayed on the screen after the intro screen and just prior to starting to play the game. The corrupted text was already corrupted in RAM on Hudson's computer before the game was XOR'ed and written to tape. The cleanly modulated (... 0x52) 0x13 0x13 0x12 0x32 0x67 0x63 0x67 0x6F 0x6F 0x4F 0x00 0x20 sequence appears on the tape, and after XOR it produces (... 0x20) 0x41 0x00 0x01 0x20 0x55 0x04 0x04 0x08 0x00 0x20 0x4F 0x20, i.e. (... ` `) `A` `\x00` `月` ` ` `U` `木` `木` `年` `\x00` ` ` `O` ` ` after `I` ` ` `T` ` ` `A` instead of the expected (... 0x20) 0x41 0x20 0x53 0x20 0x55 0x20 0x4E 0x20 0x44 0x20 0x4F 0x20, i.e. (... ` `) `A` ` ` `S` ` ` `U` ` ` `N` ` ` `D` ` ` `O`. To produce the expected text in RAM / on screen the modulated bytes would instead have been (...  0x52) 0x13 0x33 0x60 0x40 0x15 0x35 0x7B 0x5B 0x1F 0x3F 0x70 0x50... but this would have changed the bytes for the entire remainder of the tape. Thus, the data was wrong before it was recorded. Also, the modulated waveforms show no sign of degradation. in other words, the software was just shipped by Hudson Soft in a slightly broken/buggy state.

At least one PC-8801 game uses a loader with the string `\xFF` `N` `O` `N` `T` `A` `M` `A` in it too, and the same header structure, but that one does not use XOR - the data on the tape is loaded into memory verbatim.
