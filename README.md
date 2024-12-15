# Cardfight!! Vanguard WALLBOY SIMULATOR

This is a Monte Carlo simulator of the card game's V-format. It estimates the probability of, in the same game, having any given combination of cards (however many copies per card), across any given combination of game timings, while prioritizing any set of cards. It tries to approximate real play for more realistic results.

E.g. "probability of having a 'PG' by the end of turn 2 AND a grade 3 unit to ride at the start of turn 3", or "probability of having Golden Beast Tamer at the start of turn 3, AND, having 2 copies of Alice in the main phase of turn 3, AND, having either 1 Jumping Jill or 1 Purple Trapezist on turn 4's main phase".

## Description

The user must provide, at least, a deck and a test (propositional formula) to be evaluated, written in a file which the program will then read from. The program will run as many simulations as instructed, and then output the percentage of simulations that passed the test (i.e. the percentage of games where the formula was evaluated as being *True*). Though it tries to approximate real games, this is a simple simulator. It does not use AI, and it does not simulate calling rearguards, defending, nor selecting which cards to remove from the game when performing G-assist. It does not use unit effects except for the starter, which draws when rode upon, and the gift mechanic, which also draws when riding an 'accel' gifted unit *if* the 'gift' in the input file is 'accel2'. Therefore the output probability serves as a baseline that is always lower than that of real games where effects are used. The purpose of the simulator is, then, to provide said probabilistic lower limit, but also to get an idea of the difference of outcome when: varying the number of copies of cards (including triggers), varying the damage received, softly prioritizing different cards, and even aggressively looking for key cards during mulligan by sending back decent ones. Explore the `help` menu for detailed explanations of each field of the input file. Have fun!

## Getting Started

### Dependencies

* Python 3

### Executing program

Open a terminal in the script's directory and type the following command to run the script:
```
python3 raibot.py
```
You will then be prompted to type in your input file's name and the number of simulations you would like to run. Results typically deviate < 1% with 100 000 runs (takes < 10 seconds). Type in a command with the following format:
```
<file name> <number of runs> [seeGame]
```
For example, using the input file [gbt.txt](gbt.txt) (a sample file with a **G**olden **B**east **T**amer deck):
```
gbt.txt 100000
```
You may opt to include `seeGame` as the last argument to visualize games. Choose a small number of runs so as to not flood your terminal.
```
gbt.txt 1 seeGame
```
You can also type `about` for tips and guidelines, or `help` for input file formatting specifications.

## Help

If the program crashes due to input file misformatting, it is likely caused by spaces or empty lines being present where they shouldn't be, or missing where they are required.

## To do

Looking to implement:
- Plussing - adding draw and soul charging effects
- Soul - currently the only zones accounted for are the player's hand and VG circle
- Literal negation - why not
- P-format support - starter unit behavior, strides, quadruple drive, ...

## Authors

Joao Silva

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
