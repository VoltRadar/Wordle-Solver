# Wordle-Solver
Python project to display the best wordle guesses.

Wordle: https://www.nytimes.com/games/wordle/index.html
Wordle is a game where you have to guess a five letter word; the wordle.

With each guess, each letter is displayed as green, yellow, or grey.
Green indicates that the letter is in the wordle at this position.
Yellow indeicates that the letter is the wordle, but not in that position.
Grey indecates that the letter is not in the wordle.
Your guess must be a valid five letter, but doesn't have to match the hints already given

This program finds the optimal guess that you can make.
The assumptions that it makes are the following:
	1. The optimal guess is the guess, on average, narrows the
	   possible wordle's down the smallest number
	2. Words are picked at random. 


You can analyse the current state to find the next best guess.
It will print out the 20 best guesses that will norrow it down the most,
and the 20 best guesses that also match the hints.

Contains other features such as:
	Functions to create a file of precalculated values for words at the start of the game, where no
	infomation is known. This is done because otherwise getting these results is slow or not very accurate,
	and won't change.
	A simulater to play wordle, eaither with a person, or an AI.
