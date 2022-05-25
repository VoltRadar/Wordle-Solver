"""
Wordle
Guess the wordle in 6 guesses
Each guess must be a 5 letter word
Each guess the colour of the tiles will change to show how close it is to the correct guess
The guess might match the clues before

This contains classes and methods to pick for working what the optimal guess to narrow down the wordle so you can
guess the wordle in as few guesses as possible

Info:
    Green: Correct letter in the correct place
    Yellow: This letter appers in the word, but it is not in the correct place
    Grey: This letter doesn't apper in the word
"""
import itertools
import math
import random
import time
import json


class WordleGame:
    """Class for simulating a game of wordle where the wordle is known"""

    def __init__(self, wordle=None):
        if wordle:
            wordle = wordle.upper()
            self.wordle = wordle
            self.length = len(self.wordle)

    def set_wordle(self, wordle):
        """Sets the wordle to the input value"""
        self.wordle = wordle
        self.length = len(self.wordle)

    def guess(self, guess):
        """
        Returns the result of guessing a word
        Returns a list where a value of 1 is green, 0 is yellow, and -1 is Grey
        """
        if len(guess) != self.length:
            return False

        guess = guess.upper()

        output = [0 for i in range(self.length)]
        for letter_index, letter in enumerate(guess):
            if letter == self.wordle[letter_index]:
                output[letter_index] = 1

            elif letter in self.wordle:
                output[letter_index] = 0

            else:
                output[letter_index] = -1

        return output


def expected(input_list):
    """
    Returns how metric of how good a letter combination list from the analise quick section function
    This metric (i think) is the avrige number of wordles the wordle could be if you made this guess

    Takes as input a list of numbers generated from counting the number of possible wordles contain or don't contain
    a certain set of letters, ordered in a way where the binary of the index gives you what letters these wordles do
    or don't contain. So the index 5 is 00101, so this number is the number of possible wordles that contain only
    the 3rd and 5th letter.

    Computes for all numbers of possible wordles that contain or don't contain the certain set of letters (all values
    from the input_list), it calculates the expected value for a random wordle to meet these criteria. However, as
    knowing if a letter is in a word give you much more information then if you know that that letter isn't in the
    word, it is a wighted avrige, such that values with higher number of letters in the word get much lower scores

    The LETTER_NUMER_COMPASON dictionary is ruffly how much better knowing n letters is compared to knowing 0 letters.
    Calculated with 5 letter wordles.
    Will currently crash if the number of letters in the wordle is greater then 5
    """
    LETTER_NUMER_COMPASON = {0: 1.0, 1: 3.4969000078182506, 2: 14.637312414916163,
                             3: 86.66175819389429, 4: 1349.5147462302787, 5: 25000}

    return sum([x ** 2 / sum(input_list) * (1 / LETTER_NUMER_COMPASON[str(bin(i)).count('1')])
                for i, x in enumerate(input_list)])


class WordlePlayer:
    """
    Contain the methods to calculate the best guess given some information
    This serves as the back end of the system
    """

    def __init__(self, length):
        self.length = length

        self.best_start_word = "LARES"

        self.possible_words = []
        with open("words.txt") as txt:
            for line in txt.readlines():
                line = line.strip("\n")
                if len(line) == self.length:
                    self.possible_words.append(line)

        self.possible_wordles = self.possible_words[:]

        self.game = WordleGame()

        # The letters that it could be in each position
        self.hints = {"Green": [],
                      "Yellow": [],
                      "Grey": []}

    def update_hints(self, guess, result, hints=None):
        """
        Adds the information gained from the result of a guess and result and adds this to the hints. Modifies the
        hints in place.
        """
        guess = guess.upper()

        if hints is None:
            hints = self.hints

        for letter_index, letter in enumerate(guess):
            if result[letter_index] == 1:
                to_add = (letter, letter_index)
                if to_add not in hints["Green"]:
                    hints["Green"].append(to_add)

            elif result[letter_index] == 0:
                to_add = (letter, letter_index)
                if to_add not in hints["Yellow"]:
                    hints["Yellow"].append(to_add)

            else:
                if letter not in [item[0] for item in hints["Green"] + hints["Yellow"]] + hints["Grey"]:
                    hints["Grey"].append(letter)

    def is_match(self, wordle, hints=None):
        """Returns True if the wordle guess matches the hints. If hints is set to None, then the self.hints is used"""
        if hints is None:
            hints = self.hints

        matching = True

        for colour, letters in hints.items():
            if colour == "Green":
                i = 0
                while matching and i < len(letters):
                    letter, letter_index = letters[i]
                    matching = wordle[letter_index] == letter
                    i += 1

            if colour == "Yellow":
                i = 0
                while matching and i < len(letters):
                    letter, letter_index = letters[i]
                    matching = letter in wordle and wordle[letter_index] != letter
                    i += 1

            if colour == "Grey":
                i = 0
                while matching and i < len(letters):
                    matching = letters[i] not in wordle
                    i += 1

            if matching is False:
                return False

        return matching

    def possible_wordle_count(self, hints=None):
        """Returns the number of wordles from the possible wordle list that match the hints"""

        if hints is None:
            hints = self.hints

        count = 0
        matching_wordles = []

        for wordle in self.possible_wordles:
            if self.is_match(wordle, hints):
                count += 1
                matching_wordles.append(wordle)

        return count, matching_wordles

    def possible_wordle_count_v2(self, hints=None):
        """A faster version of the possible_wordle_count function"""
        if hints is None:
            hints = self.hints

        matching_wordles = self.possible_wordles[:]

        for letter in hints["Green"]:
            matching_wordles = [wordle for wordle in matching_wordles if wordle[letter[1]] == letter[0]]

        for letter in hints["Yellow"]:
            matching_wordles = [wordle for wordle in matching_wordles
                                if letter[0] in wordle and wordle[letter[1]] != letter[0]]

        yellow_letters = [letter[0] for letter in hints["Yellow"] + hints["Green"]]
        for letter in hints["Grey"]:
            matching_wordles = [wordle for wordle in matching_wordles
                                if letter not in wordle and letter not in yellow_letters]

        return len(matching_wordles), matching_wordles

    def get_rand_word(self):
        """Returns a random word from the possible word list"""
        return random.choice(self.possible_words)

    def analise(self, print_progress=True):
        """
        Analyses all possible guesses and calculates the average number of wordles each guess narrows it down to.
        The time it takes to execute this function is proportional to len(self.possible_words) *
        len(self.possible_wordles) ** 2. This is about 2 * 10 ** 12 for 5 letters with no information.

        As this function takes too long to execute with a reasonably large pool of possible wordles, if the function
        will take three minutes or more to execute, then it returns an empty dictionary

        If print_progress is set then the function prints the % of how much it's done every 5 seconds

        Returns a dictionary
        """

        # Returns the base case when no information is known
        if len(self.possible_wordles) == len(self.possible_words) and self.length == 5:
            return self.best_start_word

        random.shuffle(self.possible_wordles)

        guesses = {word: [] for word in self.possible_words}

        hints_copy = {key: value[:] for key, value in self.hints.items()}

        t = start_time = time.time()
        for wordle_index, wordle in enumerate(self.possible_wordles):
            self.game.set_wordle(wordle)
            for i, word in enumerate(self.possible_words):

                self.update_hints(word, self.game.guess(word), hints_copy)

                guesses[word].append(self.possible_wordle_count_v2(hints_copy)[0])

                hints_copy = {key: value[:] for key, value in self.hints.items()}

                if print_progress and t + 5 < time.time():
                    t = time.time()
                    fraction_done = (wordle_index + i / len(self.possible_words)) / len(self.possible_wordles)

                    if (1 / fraction_done) * (t - start_time) > 180:
                        return {}

                    print(f"{round(fraction_done * 100, 1)}% Done")

        guesses_with_scores = {guess: sum(result) / len(result) for guess, result in guesses.items()}

        return guesses_with_scores

    def narrow_possible_wordles(self, guess, result):
        """
        Modifies the known hints to include the results from this guess. result input takes the format of the output
        of the WordleGame.guess output; in the format of a list of ints where -1 is Grey, 0 is Yellow, and 1 is Green
        """
        self.update_hints(guess, result)
        self.possible_wordles = [wordle for wordle in self.possible_wordles if self.is_match(wordle)]

    def analise_quick_section(self, letter_num=5, print_progress=True):
        """
        Returns a given number of sets of letters, with a score.
        At the moment it returns top 1000 letter combinations

        The number of letters in the letter combos are specified by the letter_num input.
        """
        good_letters = [((), 100000)]
        start = t = time.time()

        # Returns the base case where the guess is the first guess, which will take a long time so is pre-computed
        if self.possible_words == self.possible_wordles and self.length == 5:
            return self.best_start_word

        for letters_index, letters in enumerate(itertools.combinations("QWERTYUIOPASDFGHJKLZXCVBNM", letter_num)):
            grouping = [0] * 2 ** letter_num
            for wordle in self.possible_wordles:
                grouping_index = 0

                for index, letter in enumerate(letters):
                    if letter in wordle:
                        grouping_index += 2 ** index

                grouping[grouping_index] += 1

            score = expected(grouping)

            # If any of the letters are green, then this score should be lowered
            for letter in letters:
                if letter in [l[0] for l in self.hints["Green"]]:
                    score /= 1.5

            if score < good_letters[-1][1]:
                good_letters.append((letters, score))
                good_letters.sort(key=lambda x: x[1])
                good_letters = good_letters[:1000]

            if t + 5 < time.time():
                t = time.time()

                total = math.factorial(26) / math.factorial(26 - letter_num) / math.factorial(letter_num)

                fraction_done = letters_index / total

                if (1 / fraction_done) * (t - start) > 60:
                    return []

                if print_progress:
                    print(f"{round(fraction_done * 100, 1)}% Done for {letter_num} letters")

        return good_letters

    def analise_quick(self, print_progress=True):
        """
        Quickly returns a full list of possible words followed by a score. This is supposed to be a faster way of
        calculating analysis then the self.analise, and will not often collate to the result of the analise function.
        In order for these scores to be useful the best words of them should have a new score calculated with the
        analise_word function

        This functions scores words based on what letters they contain, where letter combinations the letters are often
        in the possible wordles are scored lower and better.

        Returns a dictionary
        """

        # Returns the base case where the guess is the first guess, which will take a long time so is pre-computed
        if len(self.possible_wordles) == len(self.possible_words) and self.length == 5:
            return self.best_start_word

        best_letter_combos = []
        for i in range(self.length):
            section = self.analise_quick_section(i + 1, print_progress=print_progress)
            best_letter_combos.extend(section)

            if print_progress:
                print(f"Finished analysing {i + 1} letter combos")

        best_letter_combos.sort(key=lambda x: x[1])

        words_with_score = {}

        if print_progress:
            print("Scoring all possible guesses")

        t = time.time()
        for word_index, word in enumerate(self.possible_words):
            for letters, score in best_letter_combos:
                if all([letter in word for letter in letters]):
                    words_with_score[word] = score
                    break

            if print_progress and t + 5 < time.time():
                t = time.time()
                print(f"{round(word_index / len(self.possible_words) * 100, 1)}% Done scoring words")

        return words_with_score

    def get_best_guesses(self, print_progress=True):
        """
        Returns the 20 best guesses which narrow it down the most, and the 20 best guesses that are possible wordles.
        Set print_progress to True to print out the progress of the function.
        """

        # word_scores is most likely a dictionary of all possible words with a score. lower scores are better

        word_scores = self.analise_v2(print_progress)
        if not word_scores:
            word_scores = self.analise_quick(print_progress)
            used_quick_analise = True
        else:
            used_quick_analise = False

        # Deals with the starting case where best word would take a very long time to calculate
        if type(word_scores) is str:
            return [(word_scores, 289)], [(word_scores, 289)]

        wordle_scores = {key: value for key, value in word_scores.items() if key in self.possible_wordles}

        # calculates the real value for the 100 best word and wordles
        if used_quick_analise:
            if print_progress:
                print("Calculate real scores")

            best_words = [word for word in word_scores]
            best_words.sort(key=lambda x: word_scores[x])
            best_words = best_words[:100]

            best_wordles = [word for word in wordle_scores]
            best_wordles.sort(key=lambda x: wordle_scores[x])
            best_wordles = best_wordles[:100]

            word_scores = {}
            wordle_scores = {}

            # This is a set of the 100 best words and the 100 best wordles that should have a real calculated score
            words_to_score = set(best_words + best_wordles)

            t = time.time()
            for index, word in enumerate(words_to_score):
                word_scores[word] = self.analise_word_v2(word)
                if word in self.possible_wordles:
                    wordle_scores[word] = word_scores[word]

                if print_progress and t + 5 < time.time():
                    t = time.time()
                    print(f"{round(index / len(words_to_score) * 100, 1)}% Done calculating real scores")

        output = []

        for score_dict in (word_scores, wordle_scores):
            score_list = sorted(list(score_dict.items()), key=lambda x: x[1])[:20]

            output.append(score_list)

        return output[0], output[1]

    def analise_word(self, word, print_progress=True):
        """
        Returns the average number of wordles this word if guesses narrows it down to. Time it takes to execute is
        proposal to the square of number of possible wordles, and can take up to 120 seconds with 13000 wordles. If
        print_progresss is set to True, then the function displays how much the of the function is complete
        """
        output = []

        hints_copy = {key: value[:] for key, value in self.hints.items()}

        t = time.time()

        for index, wordle in enumerate(self.possible_wordles):
            self.game.set_wordle(wordle)

            self.update_hints(word, self.game.guess(word), hints_copy)
            output.append(self.possible_wordle_count_v2(hints_copy)[0])

            hints_copy = {key: value[:] for key, value in self.hints.items()}

            if print_progress and t + 5 < time.time():
                t = time.time()
                print(f"{round(index / len(self.possible_wordles) * 100, 1)}% Done analysing {word}")

        return sum(output) / len(output)

    def analise_test(self):
        """Counts the most common letters in the wordle list"""
        letter_freq = {}

        for wordle in self.possible_wordles:
            for letter in wordle:

                # Doesn't count letters used multiple times
                if wordle.index(letter) == 0:
                    if letter in letter_freq:
                        letter_freq[letter] += 1
                    else:
                        letter_freq[letter] = 1

        letter_freq_list = list(letter_freq.items())
        letter_freq_list.sort(key=lambda x: letter_freq[x[0]], reverse=True)

        print(letter_freq_list)
        most_common_letters = letter_freq_list[:3] + letter_freq_list[4:6]
        print(most_common_letters)
        most_common_letters = [x[0] for x in most_common_letters]

        good_guesses = {wordle: self.analise_word(wordle, print_progress=True) for wordle in self.possible_wordles
                        if all([letter in wordle for letter in most_common_letters])}

        print(good_guesses)

    def analise_word_v2(self, word, print_progress=True):
        """Quickly analyses a word, and returns the average number of wordles it will narrow it down to"""

        possible_wordles_copy = self.possible_wordles[:]

        guess_results = []
        # While there are still words to analise...

        start_time = t = time.time()
        while possible_wordles_copy:
            hints = {key: value[:] for key, value in self.hints.items()}

            # Picking the first word form our list of possible wordles
            wordle = possible_wordles_copy[0]
            self.game.set_wordle(wordle)
            result = self.game.guess(word)

            # Updating the hints
            self.update_hints(word, result, hints)

            # A list of all the wordles that match the result
            wordles_that_match_result = self.possible_wordle_count_v2(hints)[1]

            # Adds the number of wordles that match this guess to the guess_result list
            guess_results.append(wordles_that_match_result)

            # Filters out the possible wordles to check be
            possible_wordles_copy = [wordle for wordle in possible_wordles_copy
                                     if wordle not in wordles_that_match_result]

            if print_progress and t + 5 < time.time():
                print(f"{len(possible_wordles_copy) / len(self.possible_wordles)}% Done with {word}")

        def prob(possible_remaining_wordles):
            """Returns the probability of a list of wordles occurring"""
            #
            return len(possible_remaining_wordles) / len(self.possible_wordles)

        expected_score = [len(remainging_wordles) * prob(remainging_wordles) for remainging_wordles in guess_results]

        return sum(expected_score)

    def analise_v2(self, print_progress=True):
        """A faster verstion on the self.analise fucntion"""

        if len(self.possible_wordles) == len(self.possible_words):
            word_scores = read_from_file("StartingWordScores.txt")

            if str(self.length) in word_scores:
                return word_scores[str(self.length)]
            else:
                return {}

        result = {}
        start_time = t = time.time()
        for word_index, word in enumerate(self.possible_words):
            result[word] = self.analise_word_v2(word, print_progress=print_progress)

            if print_progress and t + 5 < time.time():
                t = time.time()

                fraction_done = word_index / len(self.possible_words)

                if (t - start_time) * 1 / fraction_done > 120:
                    return {}

                print(f"{round(fraction_done * 100, 1)}% Done")

        return result


class WordleOptimalPlayer(WordlePlayer):
    """
    This class contains methods to directly ask a user what guess they make and display results of analyse of what the
    best guesses are.
    """

    def __init__(self, length):
        super().__init__(length)

    def input_guess(self):
        """
        Displays text on the screen to input a guess and the result of the guess
        It then narrows down the possible wordles
        """
        guess = input("\nWhat was the guess? > ").strip("\n").strip(" ")
        result = input("What was the result of the guess (eg. GGYRR) > ")

        values = {"G": 1, "Y": 0, "R": -1}
        self.narrow_possible_wordles(guess, [values[i.upper()] for i in result])

    def display_possible_wordles(self):
        """
        Displays possible wordles. If the number of possible wordles is greater then 10, then is displays the number
        of possible wordles
        """
        number = len(self.possible_wordles)
        if number > 10:
            print("Remaining wordles: ", number)
        else:
            print("Remaining wordles: ", ", ".join(self.possible_wordles))

    def ask_to_analyse(self):
        """
        Asks if the player wants to analyse, and if they do, preform the analysis and display the best words and
        wordles to guess. If it has no information, then it displays one word that is precalculated to be the best.
        Displays along with the words, the average number of wordles that this word will narrow it down to if the word
        is guessed
        """

        inp = ""
        while not inp:
            inp = input("Do analysis to find the best word? ('y' or 'n') > ").lower()
            if inp and inp[0] != "y":
                return None

        best_guesses = self.get_best_guesses()

        print("\n\n----- Done! -----")

        print("Best guesses:")
        for word, score in best_guesses[0]:
            print(f"{word}: {score}")

        print(f"\nBest out of {len(self.possible_wordles)} wordles")
        for word, score in best_guesses[1]:
            print(f"{word}: {score}")

    def start(self):
        """Starts the analysis of a wordle game. Repeatedly ask the user if they want to preform analisys to ask for
        the best guess for their guess and display the results of these and the result of the
         guess and narrows down the possible wordles and displays them to the user """
        while len(self.possible_wordles) > 1:
            self.display_possible_wordles()
            self.ask_to_analyse()
            self.input_guess()

        print("Finished!")
        print("\nWord Found:", self.possible_wordles[0])

    def start_sim_game(self):
        """
        Picks a random word, and simulates a game of wordle with you typing in the answers you want until you're done
        """
        wordle = self.get_rand_word()
        simGame = WordleGame()
        simGame.set_wordle(wordle)

        guess_num = 0

        while True:
            self.display_possible_wordles()
            self.ask_to_analyse()

            guess_num += 1
            guess = input(f"\nGuess {guess_num} > ")

            result = simGame.guess(guess)

            for item in result:
                print(item, end=" ")
                time.sleep(1)
            print()

            if result == [1] * self.length:
                print(f"Well done! Guessed in {guess_num} guesses")
                break

            self.narrow_possible_wordles(guess, result)


def string_date(diff):
    """
    Takes a number in seconds, and returns a string of how many days, hours, minutes, and seconds it is rounds up the
    number of seconds to the nearest second
    """
    if diff > 10 ** 11:
        return ""

    times = {
        "day": 86400,
        "hour": 3600,
        "minute": 60,
        "second": 1
    }

    output_list = []
    for item in times.keys():
        number = math.ceil(diff // times[item])

        if number == 1:
            output_list.append("1 {}".format(item))
        elif number >= 2:
            output_list.append("{} {}s".format(number, item))

        diff -= times[item] * number

    if len(output_list) == 0:
        return ""

    elif len(output_list) == 1:
        return output_list[0]

    else:
        output = ""
        last = output_list[-1]
        for item in output_list:
            if item is not last:
                output += "{}, ".format(item)
            else:
                output += "and {}".format(item)

        return output


def write_to_file(filename, obj):
    """
    Writes an object to a text file, as a json object
    WARNING: REPLACES ALL TEXT IN THE FILE WITH THE TEXT OF THE INPUT
    """
    text = json.dumps(obj)
    with open(filename, "w") as txt:
        txt.write(text)


def read_from_file(filename):
    """Returns the json object from a given textfile, assuming that the file just contains 1 object"""
    with open(filename, "r") as txt:
        return json.loads(txt.read())


class WordleSim:
    """
    An AI to simulate a game of wordle.
    """
    def __init__(self, length):
        self.length = length
        self.sim_game = WordleGame()
        self.sim_player = WordlePlayer(self.length)

    def sim(self, print_progress=True, word=None):
        """
        Simulates a game of wordle, playing a stratagy. Returns the wordles guesses.
        Ends with the correct wordle being guesses.
        """
        self.sim_player = WordlePlayer(self.length)

        if word is None:
            # Set the random word as the game
            self.sim_game.set_wordle(self.sim_player.get_rand_word())
        else:
            self.sim_game.set_wordle(word)

        guesses = []
        done = False

        while not done:
            best_guesses = self.sim_player.get_best_guesses(print_progress=print_progress)

            # The best word to guess to narrow it down the most
            best_word = best_guesses[0][0]

            # Best word to guess to narrow it down the most that is also a wordle
            best_wordle = best_guesses[1][0]

            if len(guesses) in [0, 1, 4]:
                if len(self.sim_player.possible_wordles) > 20 and len(guesses) != 4:
                    guess = best_word[0]
                else:
                    guess = best_wordle[0]
            elif len(guesses) == 2 and best_word[1] == 1.0 and best_wordle[1] > 1.0:
                guess = best_word[0]
            else:
                guess = best_wordle[0]

            guesses.append(guess)

            result = self.sim_game.guess(guesses[-1])

            if print_progress:
                print(f"Guessed {guess}: result was {result}")

            if result == [1] * self.length:
                done = True
            else:
                self.sim_player.narrow_possible_wordles(guesses[-1], result)

        return guesses


class BestStarterFinder(WordlePlayer):
    """
    Calculates the scores of the opening words.
    The results of this only have to be calculated once.
    Writes the scores into a text files for each possible word.
    """
    def __init__(self, length):
        super().__init__(length)

    def start(self):
        full_scores = read_from_file("StartingWordScores.txt")
        calculatedScores = full_scores[str(self.length)]

        words_to_calculate = [word for word in self.possible_words if word not in calculatedScores]

        start_time = time.time()
        for word_index, word in enumerate(words_to_calculate):
            print(f"{word}: ", end="")
            word_score = self.analise_word(word, False)
            print(word_score)

            calculatedScores[word] = word_score

            print()
            print(f"{len(calculatedScores)} / {len(self.possible_words)} words scored")

            fraction_done = len(calculatedScores) / len(self.possible_words)
            print(f"{round(fraction_done * 100, 1)}% of words scored")

            print(f"{round((time.time() - start_time) / (word_index + 1), 2)} seconds per word")

            seconds_left = (time.time() - start_time) * (len(words_to_calculate) / (word_index + 1) - 1)
            print("Time left:", string_date(seconds_left))

            write_to_file("StartingWordScores.txt", full_scores)

            print()


if __name__ == "__main__":
    me = WordleOptimalPlayer(5)
    print("Key:")
    print("G: green tile,  Y: yellow tile,  R: grey tile")
    while True:
        me.start()
        print("Restarting...")
