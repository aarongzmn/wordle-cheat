from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as bs
import random
import time
import os


def get_driver(CHROME_DRIVER_PATH) -> webdriver.Chrome:
    """Startup Chrome webdriver which will be used to solve Wordle

    Returns:
        webdriver.Chrome: Selenium Chrome webdriver object.
    """
    useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={useragent}")

    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, options=chrome_options)
    return driver


def driver_send_keys(driver, guess) -> None:
    """Use to submit word to Wordle puzzle.

    Args:
        guess (str): 5 character string
    """
    input_letters = list(guess)
    for letter in input_letters:
        actions = ActionChains(driver)
        actions.send_keys(letter)
        actions.perform()
        time.sleep(0.1)
    actions.send_keys(Keys.ENTER)
    actions.perform()


def driver_send_message(driver, message) -> None:
    """Output message using Wordle grid

    Args:
        message (str): String (sentance) with words no more than 5 characters long each (Wordle display limit).
    """
    message_chunks = message.split(" ")
    for chunk in message_chunks:
        chunk_letters = list(chunk)
        for i in range(len(chunk_letters)):
            actions = ActionChains(driver)
            actions.send_keys(chunk_letters[i])
            actions.perform()
            time.sleep(0.1)
        for i in range(len(chunk_letters)):
            actions.send_keys(Keys.BACKSPACE)
            actions.perform()
            time.sleep(0.1)


def get_wordle_hints(driver) -> ([None]*5, ["str"], ["str"]):
    page_source = bs(driver.page_source, 'html.parser')

    game_rows = page_source.find_all("div", class_="game-row")  # incorrect/red
    green = [None]*5
    for row in game_rows:
        letter_results = row.find_all("div", class_="game-tile")
        letter_guesses = row.find_all("div", class_="game-tile-letter")
        results = list(zip(letter_results, letter_guesses))
        for i in range(len(results)):
            if "game-tile-correct" in results[i][0].get("class"):
                green[i] = results[i][1].text.strip()

    letters_yellow = page_source.find_all("div", class_="game-tile game-tile-present")  # incorrect/red
    yellow = []
    for i in letters_yellow:
        letter = i.find("div", class_="game-tile-letter").text.strip()
        yellow.append(letter)

    letters_red = page_source.find_all("div", class_="game-tile game-tile-absent")  # incorrect/red
    red = []
    for i in letters_red:
        letter = i.find("div", class_="game-tile-letter").text.strip()
        red.append(letter)
    return green, yellow, red


def get_wordle_hints_local(guess, answer) -> ([None]*5, ["str"], ["str"]):
    guess_letters = list(guess)
    answer_letters = list(answer)

    green = [None]*5
    yellow = []
    red = []

    for position in range(len(guess_letters)):
        if guess_letters[position] == answer_letters[position]:
            green[position] = guess_letters[position]
        if guess_letters[position] in answer_letters:
            yellow.append(guess_letters[position])
        if guess_letters[position] not in answer_letters:
            red.append(guess_letters[position])

    return green, yellow, red


def get_opening_guess(word_list, common_letters="etaionshr") -> (str, str) :
    """Generate word pairs that have the least letters common with each other,
    but still have a high amount of 'common_letters'. These are meant to be used to open the game,
    thus increasing the chance possible matches within the first two turns.

    Args:
        word_list (list): List of words to choose from.
        common_letters (str): String containing frequently occuring letters.
            Words that have the most matching letters will be prioritized.

    Returns:
        (str, str): Pair of words that should be used in the first two rounds of Wordle.
    """
    random.shuffle(word_list)   # shuffle word list just because
    opening_guess = ""
    for word in range(len(word_list)):
        new_option = len(list(dict.fromkeys([i for i in word_list[word] if i in common_letters])))
        old_option = len(list(dict.fromkeys([i for i in opening_guess if i in common_letters])))
        if new_option > old_option:
            opening_guess = word_list[word]

    second_guess = word_list[0]  # temporary value that will be replaced by word in 'word_list'
    for word in range(len(word_list)):
        new_option_len = len(list(dict.fromkeys([i for i in word_list[word] if i in opening_guess])))
        old_option_len = len(list(dict.fromkeys([i for i in second_guess if i in opening_guess])))
        if new_option_len < old_option_len:
            new_option = len(list(dict.fromkeys([i for i in word_list[word] if i in common_letters])))
            old_option = len(list(dict.fromkeys([i for i in second_guess if i in common_letters])))
            if new_option > old_option:
                second_guess = word_list[word]
    return (opening_guess, second_guess)


def check_red(word_list, red) -> list:
    """Remove words from 'word_list' list if they DO contain any 'red' letters

    Args:
        word_list (list): List of words to choose from.
        red (list): List of letters that are confirmed to not be in the Wordle answer.

    Returns:
        list: List of words that do not contain any of the letters in 'red' list.
    """
    filtered_red = []
    for word in range(len(word_list)):
        if any(x in list(word_list[word]) for x in red):
            continue
        else:
            filtered_red.append(word_list[word])
    return filtered_red


def check_yellow(word_list, yellow) -> list:
    """Remove words from 'word_list' list if they DONT contain any 'yellow' letters

    Args:
        word_list (list): List of words to choose from.
        yellow (list): List of letters that are confirmed to be in the Wordle answer.

    Returns:
        list: List of words that contain all of the letters in the 'yellow' list.
    """
    filtered_yellow = []
    for word in range(len(word_list)):
        if all(x in list(word_list[word]) for x in yellow):
            filtered_yellow.append(word_list[word])
        else:
            continue
    return filtered_yellow


def check_green(word_list, green) -> list:
    """Remove words from 'word_list' list if they do not match the letter positions in the 'green' list.

    Args:
        word_list (list): List of words to choose from.
        green (list): List of 5 items. Each item starts as None type and
            is replaced by any confimed letters as the Wordle puzzile is solved.

    Returns:
        list: List of words that contain the letters in the exact position as the 'green' list.
    """
    filtered_green = []
    for word in range(len(word_list)):
        shape = [None]*5
        for position in range(len(green)):
            if green[position] is None:
                shape[position] = None
            else:
                if word_list[word][position] == green[position]:
                    shape[position] = word_list[word][position]
        if green == shape:
            filtered_green.append(word_list[word])
    return filtered_green


def check_if_solved(driver) -> bool:
    """Search for text on web page indicating if Wordle puzzle is solved.

    Returns:
        bool: Returns True if puzzle is solved, returns False if not solved.
    """
    if "correct word" in driver.page_source:
        return True
    else:
        return False


def get_word_options() -> list:
    with open("words.txt") as file:
        words = [line.rstrip() for line in file]
    return words


def main(local_test=False):
    word_list = get_word_options()
    opening_guesses = list(get_opening_guess(word_list))

    if local_test:
        answer = random.choice(word_list)
    else:
        CHROME_DRIVER_PATH = os.getenv("CHROME_DRIVER")
        driver = get_driver(CHROME_DRIVER_PATH)
        driver.get("https://wordle.drakemain.dev/")

        driver_send_message(driver, "aaron wuz here")  # assert dominance here

    guess_list = []
    for guess in opening_guesses:
        guess_list.append(guess)
        if local_test:
            # This section will be determined from HTML when HTML scraping is setup
            green, yellow, red = get_wordle_hints_local(guess, answer)  # use for local testing
        else:
            driver_send_keys(driver, guess)
            green, yellow, red = get_wordle_hints(driver)

        filtered_red = check_red(word_list, red)
        filtered_yellow = check_yellow(filtered_red, yellow)
        filtered_green = check_green(filtered_yellow, green)
        word_list = filtered_green

        if local_test:
            solved = answer == guess
        else:
            time.sleep(.5)
            solved = check_if_solved(driver)

    while solved is False and len(guess_list) <= 6:
        guess = random.choice(word_list)
        guess_list.append(guess)
        if local_test:
            # This section will be determined from HTML when HTML scraping is setup
            green, yellow, red = get_wordle_hints_local(guess, answer)  # use for local testing
        else:
            driver_send_keys(driver, guess)
            green, yellow, red = get_wordle_hints(driver)

        filtered_red = check_red(word_list, red)
        filtered_yellow = check_yellow(filtered_red, yellow)
        filtered_green = check_green(filtered_yellow, green)
        word_list = filtered_green

        if local_test:
            solved = answer == guess
        else:
            time.sleep(.5)
            solved = check_if_solved(driver)

    if solved:
        answer = guess_list[-1]
        print(f"\n{answer=} found on turn {len(guess_list)}, {guess_list=}")
        time.sleep(5)
    else:
        print(f"\nRan out of turns. Word list was narrowed down to: {len(word_list)} words")
        time.sleep(5)


main()
