# FastMath

A terminal-based math practice game that adapts to your skill level. Problems get harder as you improve, and the game focuses practice on your weak areas using spaced repetition and error pattern detection.

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Install

```bash
pip install fastmath-cli
```

Or run from source:

```bash
git clone https://github.com/michaelkrauty/fastmath.git
cd fastmath
pip install .
```

Then run:

```bash
fastmath
```

## Controls

| Key | Action |
|-----|--------|
| Arrow keys | Navigate menus |
| Enter | Select / confirm |
| Numbers | Type your answer |
| PgDn | Skip a problem (reveals the answer) |
| q | Pause / quit |

## Features

### Adaptive difficulty
Each operation (add, subtract, multiply, divide) has its own difficulty level that adjusts automatically based on your accuracy and response time. You can also set difficulty manually from the settings menu.

### Smart problem selection
The game uses a weighted scoring system to pick the most useful problem for you to practice right now:

- **Performance history** — problems you've gotten wrong recently appear more often
- **Spaced repetition** — correctly-answered problems resurface at optimal review intervals
- **Error pattern detection** — identifies specific weaknesses (carrying, borrowing, multiplication tables) and generates targeted drills
- **Educational value** — prioritizes pedagogically important patterns like number bonds, doubling, halving, and near-multiples
- **Variety enforcement** — avoids repeating the same answers or number pairs back-to-back

### Algebra mode
Optional algebra problems covering:
- Parentheses — `(3 + 4) * 2`, nested expressions
- Exponents — `2^3`, `(2+1)^2`
- Fractions — `1/2 + 1/4`, mixed numbers
- Variables — `2x + 1 = 7`, equations with variables on both sides

Each algebra type has its own difficulty tracking. Enable from the Algebra menu.

### Statistics
Track your accuracy, average/median solve times, streaks, and recent trends per operation.

## Data storage

Performance data and settings are stored in your OS-specific user data directory (via [platformdirs](https://pypi.org/project/platformdirs/)):

| OS | Location |
|----|----------|
| Linux | `~/.local/share/fastmath/` |
| macOS | `~/Library/Application Support/fastmath/` |
| Windows | `%LOCALAPPDATA%\michaelkrauty\fastmath\` |

## License

MIT
