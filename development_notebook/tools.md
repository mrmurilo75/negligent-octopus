# Cheat Sheet

## tmux

prefix: `Ctrl + a` or `Ctrl + b`

### Session
tmux ps
    ? list sessions

tmux at -t \<session name\>
    ? Enter session

### Windows
`prefix` then `[hjkl]
    ? Change window using VIM keys

`prefix` then `%`
    ? Split horizontal

`prefix` then `"`
    ? Split vertical

`prefix` then `[HJKL]`
    ? Resize window by `N` to [Up, Down, Left, Right]

## NVim

`Ctrl + n` or `Ctrl + \<space\>`
    ? Cycle autocomplete options

`,` then `d`
    ? Jump to definition
        - Hint: duplicate window using `:sp` before jump

:sp \<filepath\>
    ? Split vertical

:vsp \<filepath\>
    ? Split horizontal

### Windows
`Ctrl + W` then `[hjkl]`
    ? Move cursor to window

`Ctrl + W` then `[HJKL]`
    ? Move window

`Ctrl + W` then `[+ -]`
    ? Resize window vertically

`Ctrl + W` then `[\< \>]`
    ? Resize window horizontally

`Ctrl + W` then `\_`
    ? Resize to near full-screen

`Ctrl + W` then `\=`
    ? Resize to equal parts

### NERDTree
`:NERDTree`


## Bash

`w`
    ? Shows processes running

`ESC + b`
    ? Equivalent to `Ctrl + \<left arrow\>`

`ESC + l`
    ? Equivalent to `Ctrl + \<right arrow\>`

`ESC + \<Backspace\>`
    ? Equivalent to `Ctrl + \<Backspace\>`

`Ctrl + R` then `Enter`
    ? Search command history. Press `Enter` for next result.
