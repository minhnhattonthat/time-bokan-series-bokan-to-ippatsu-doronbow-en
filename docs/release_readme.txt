Time Bokan Series: Bokan to Ippatsu! Doronbow (PlayStation) - English translation patch v$version

Unofficial fan translation. This zip holds the patch and this file only. No game data is included, and pre-patched
images must not be shared.


WHAT YOU NEED

Your own dump of the Japanese disc, SLPS-00609, as BIN/CUE with 22 tracks (Redump: Time Bokan Series - Bokan to
Ippatsu! Doronbow (Japan), http://redump.org/discs/quicksearch/SLPS-00609/). The patch changes Track 01 only:

    Time Bokan Series - Bokan to Ippatsu! Doronbow (Japan) (Track 01).bin
    Size    $size bytes
    CRC32   $crc32
    MD5     $md5
    SHA-1   $sha1

After patching, Track 01 has:

    CRC32   $new_crc32
    SHA-1   $new_sha1


HOW TO PATCH

1. Copy the whole game folder, so your original stays as it is.
2. Apply $patch to Track 01 with xdelta3 or Delta Patcher:

       xdelta3 -d -s "original Track 01.bin" $patch "patched Track 01.bin"

3. Replace Track 01 in the copy with the patched file, under the same file name. The .cue and tracks 02-22 stay as they
   are.
4. Open the .cue in your emulator and start from a cold boot. Savestates made on the original disc hold the old graphics
   and will not show the English.


TRANSLATION STATUS

Movie dialogue               English subtitles burned into all 6 movies; voices stay Japanese
Title and options menus      Translated
Memory card messages         Translated; the save's name in the card manager reads BOKAN! DORONBOW
Ship select, stage cards     Translated
Banners, HUD, signs          Translated
Sound test                   Song titles and voice captions translated
Credits                      Translated
Title logo                   Left in Japanese, as no official English logo is known
Songs and voice samples      Left in Japanese (audio)


KNOWN ISSUES

- Nobody checked the movie subtitles by ear. They come from machine transcription, corrected from context and
  knowledge of the series; about 30 lines on unclear audio are best guesses.
- Subtitles use official English names, so they say "Tonzra" where the voice says "Tonzura".
- Song titles are our own English; no official ones are known.
- Some credit name readings are unconfirmed, because their kanji can be read more than one way.
- 23 graphics labels were never seen drawn in testing (damaged-save messages, a trial-version stamp and a few HUD
  pieces) and may be unused. They are translated anyway.
- The stage 6 and 7 cards say "IPPATUMAN": that is the game's own English, left as it is.

Tested on PCSX-Redux 30282.20261104.5 only, by scripted warps to every scene rather than a full playthrough. Not tested
on real hardware or other emulators. Please report bugs:
https://github.com/minhnhattonthat/time-bokan-series-bokan-to-ippatsu-doronbow-en/issues


CREDITS

Translation and tools: minhnhattonthat, with extensive AI assistance (Claude by Anthropic), including the machine
transcription of the movies. Corrections are very welcome.
Fonts: Bangers, Jersey 10, Jersey 15, Liberation Serif and Liberation Sans, under the SIL Open Font License 1.1.
Time Bokan Series: Bokan to Ippatsu! Doronbow is (c) Banpresto and Tatsunoko Production. This project is not
affiliated with them.
