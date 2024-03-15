# Cheat Sheet

## tmux

### Session
tmux list-sessions
tmux attach-session -t \<session name\>

### Windows
`Ctrl + b` then \<arrow-key\>
    ? Change window

`Ctrl + b` then `%`
    ? Split horizontal

`Ctrl + b` then `"`
    ? Split vertical

`Ctrl + b` then `Alt+[Arrow UDLR]`
`Ctrl + b` then `:resize-pane -[UDLR] N`
    ? Resize window by `N` to [Up, Down, Left, Right]

## NVim

:sp \<filepath\>
    ? Split vertical

:vsp \<filepath\>
    ? Split horizontal

###  TODO -> Include plugin commands

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
