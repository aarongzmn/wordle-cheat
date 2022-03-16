# wordle-cheat
This is a program I created to solve Wordle puzzles in webapp a friend of mine created: https://wordle.drakemain.dev/

This program through Chrome using the Selenium webdriver. It also has the ability run local simulations which allows me to measure the efficiency of algorithm changes when solving puzziles.

1. Download Chrome webdriver and set 'CHROME_DRIVER' environment variable to point to the webdrivers path
2. Insall required libraries found in 'requirements.txt'
3. Set 'local_test' to False to run simulation locally. Set to True to solve webapp found at 'https://wordle.drakemain.dev/'