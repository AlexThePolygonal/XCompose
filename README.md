## My XCompose File

TLDR: XCompose for maths

1. What is XCompose? First, look it up. Second, its a multi-key input system for X. RCtrl + c + , = ç, RCtrl + b + N = ℕ, that kind of thing.
2. Why XCompose? Sometimes, you want to talk about mathematics with people. For articles, we have latex, however messengers don't support it, so people try to write latex explicitly \hat{Z} \otimes C or pictograms \hat{Z} (x) {C} and it's unreadable. And that's terrible. However, messengers support unicode, and unicode supports a bunch of mathematical symbols, so we can type ℤ̂  ⨂ ℂ, which is somewhat better. 
3. The config is `XCompose`, all other files are intermediate files which I used for processing at some point. They are still kept in case reprocessing is necessary.
4. Config rules:
   - `<i>` means mathematical italic
   - `<i> <dagger>` is italic bold
   - `<z>` is script (cause collisions)
   - `<k>` is calligraphic (kalligraphic, geddit?? because collisions)
   - `<f>` is fraktur
   - `<f> <dagger>` is bold fraktur
   - `<m>` is small caps (`<s>` and `<c>` are already taken ...)
   - `<g>` is greek
   - `r` is roman numerals
   - `<slash>` is usually negation
   - Capital letters correspond to large (N-ary) versions of the symbol
   - `<^>` or `<asciicircum` is superscript or combining above characters
   - `<_>` or `<underscore>` is subscript
   - Mathematicals symbols are random, my own mnemonics
  TLDR: read the file, it's not that large
1. Fun facts: 
    - There are two types of fraktur, double-struck and script letters. Compare 𝔹, ℂ, ℍ, ℕ, ℚ and 𝔸, 𝔼, 𝕌, 𝕎, They look slighly different and come from different unicode blocks. Why? Because we live in a society.
    - How do I type `<dagger` or `<†>`? Well I modded my /usr/share/X11/xkb/symbols. Enjoy.
  