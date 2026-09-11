# TODO

## Timings

3S is accurate, getting real numbers for any other game would require either annotated disassembly or decompiled code that doesn't currently exist. Another method would be using mame lua and memory editing to figure it out.

## Tekken 3

This will be difficult due to the combo structure instead of motion input, <https://gamefaqs.gamespot.com/arcade/563192-tekken-3/faqs/979>

## Timing

Maybe change measurements to frames? Then pytest can 3x or 4x speed?

## Move playback feature to see what the motion should be

## Make the game internal names mame accurate

## Input display

In the input display 'character' currently the motions light up as they are performed change this to a lighter green/grey. 

On the input feed they change to green when a punch or kick is pressed meaning a move would have executed

If a move would have been executed, light up the motion the regular green for half? a second, same as on the actual character screens
