# FastMath v1.1.0

A terminal-based math practice application that adapts to your skill level.

## Requirements
- [blessed](https://pypi.org/project/blessed/)

## Controls
- Arrow keys/Enter to navigate menus
- q to pause/exit
- Numbers to input answers

## How to Play
- Enter the answer to the math problems presented
- Difficulty will automatically ramp up to meet your skill level
- The application tracks your performance and focuses on problems you need to practice

## Features

### Smart Problem Selection
The application uses an intelligent algorithm to select problems based on:
- Your past performance on specific problems
- The time it takes you to solve each problem (adjusted for typing time)
- Whether you've gotten a problem wrong or right before
- Problem variants (e.g., 4+12 vs 12+4) are tracked separately

### Adaptive Difficulty
- Difficulty levels adjust automatically based on your performance
- Each operation (addition, subtraction, multiplication, division) has its own difficulty setting
- You can manually adjust difficulty levels in the settings

### Performance Tracking
- Detailed statistics on your performance across different operations
- Tracks metrics like accuracy, average time, and improvement over time

## Stats
Use the Stats option in the main menu to view your performance metrics including:
- Accuracy per operation
- Average, median, and mode solution times
- Recent performance trends
- Longest correct streak
