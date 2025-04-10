# FastMath v1.2.1

A terminal-based math practice application that adapts to your skill level.

## Requirements
- [blessed](https://pypi.org/project/blessed/)
- [platformdirs](https://pypi.org/project/platformdirs/)

## Controls
- Arrow keys/Enter to navigate menus
- q to pause/exit
- Numbers to input answers

## How to Play
- Enter the answer to the math problems presented
- Difficulty will automatically ramp up to meet your skill level
- The application tracks your performance and focuses on problems you need to practice

## Features

### Education-Focused Problem Generation
- Problems are selected based on educational value and math learning principles
- Special focus on important math patterns like number bonds (pairs that sum to 10/100)
- Emphasizes critical skills like doubling, halving, and working with near-multiples
- Balanced progression from foundational concepts to more complex operations

### Smart Problem Selection
The application uses an intelligent algorithm to select problems based on:
- Your past performance on specific problems
- The time it takes you to solve each problem (adjusted for typing time)
- Whether you've gotten a problem wrong or right before
- Problem variants (e.g., 4+12 vs 12+4) are tracked separately
- Pattern detection in error types to provide targeted practice

### Adaptive Difficulty
- Difficulty levels adjust automatically based on your performance
- Each operation (addition, subtraction, multiplication, division) has its own difficulty setting
- You can manually adjust difficulty levels in the settings
- Problem selection adapts to your current skill level (beginner, intermediate, advanced)

### Performance Tracking
- Detailed statistics on your performance across different operations
- Tracks metrics like accuracy, average time, and improvement over time
- Analysis of error patterns to identify areas needing improvement

## Stats
Use the Stats option in the main menu to view your performance metrics including:
- Accuracy per operation
- Average, median, and mode solution times
- Recent performance trends
- Longest correct streak
