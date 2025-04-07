import random
import time
from blessed import Terminal
from datetime import datetime
import json
import os
import statistics


# File paths

performance_data_file_path = "performance.json"
config_file_path = "config.json"


# List to store performance data of the user
performance_data = []

def save_performance_data():
    """
    Save the performance data to a JSON file.
    If the file does not exist, it creates a new file with an empty list.
    """
    if not os.path.exists(performance_data_file_path):
        with open(performance_data_file_path, 'w') as f:
            json.dump([], f)  # Create an empty list in the file if it doesn't exist

    with open(performance_data_file_path, 'w') as f:
        json.dump(performance_data, f, indent=1)

def load_performance_data():
    """
    Load the performance data from a JSON file.
    If the file does not exist, initializes the performance_data as an empty list.
    """
    global performance_data
    if os.path.exists(performance_data_file_path):
        with open(performance_data_file_path, 'r') as f:
            performance_data = json.load(f)
    else:
        performance_data = []  # Initialize as empty list if file doesn't exist

def get_problem_weights():
    """
    Calculate weights for each problem type based on past performance and time decay.
    This helps in adjusting the frequency of problem types based on user performance.
    """
    problem_stats = {}
    current_time = datetime.now()

    for entry in performance_data:
        problem_type = entry['problem'].split()[1]
        if problem_type == '+':
            problem = 'addition'
        elif problem_type == '-':
            problem = 'subtraction'
        elif problem_type == '*':
            problem = 'multiplication'
        elif problem_type == '/':
            problem = 'division'

        difficulty = entry.get('difficulty', 1)  # Default to difficulty level 1 if not specified
        time_diff = current_time - datetime.fromisoformat(entry['timestamp'])
        # Adjust decay based on difficulty, more difficult problems have slower decay
        time_weight = max(0, (24 - time_diff.total_seconds() / 3600) / (18 * difficulty))

        if problem not in problem_stats:
            problem_stats[problem] = {'correct_weight': 0, 'incorrect_weight': 0, 'total_time': 0, 'attempts': 0, 'times': [], 'difficulty_sum': 0}

        if entry['correct']:
            problem_stats[problem]['correct_weight'] += time_weight
        else:
            problem_stats[problem]['incorrect_weight'] += time_weight

        problem_stats[problem]['total_time'] += entry['time_taken']
        problem_stats[problem]['attempts'] += 1
        problem_stats[problem]['times'].append(entry['time_taken'])
        problem_stats[problem]['difficulty_sum'] += difficulty

    problem_weights = {}
    for problem, stats in problem_stats.items():
        if stats['attempts'] > 0:
            avg_difficulty = stats['difficulty_sum'] / stats['attempts']
            accuracy = stats['correct_weight'] / stats['attempts']
            # Adjust weight calculation to factor in average difficulty
            weight = (1 / (accuracy + 0.1)) * avg_difficulty
            problem_weights[problem] = max(1, min(weight, 5))  # Cap the weight to a maximum of 5

    return problem_weights

def generate_problem(operation, difficulty, allow_negative):
    """
    Generate a math problem based on the operation type, difficulty, and whether negative results are allowed.
    """
    # Adjusted scaling: use a smaller base for exponential growth or a linear growth
    base_val = 5  # Base value for difficulty scaling
    growth_factor = 1.1  # Growth factor for each difficulty level

    # Calculate the maximum value based on the new scaling formula
    adjusted_max_val = int(base_val * (growth_factor ** (difficulty - 1)))

    if operation == 'addition':
        num1 = random.randint(1, adjusted_max_val)
        num2 = random.randint(1, adjusted_max_val)
        answer = num1 + num2
        problem = f"{num1} + {num2}"
    elif operation == 'subtraction':
        num1 = random.randint(1, adjusted_max_val)
        num2 = random.randint(1, num1) if not allow_negative else random.randint(1, adjusted_max_val)
        answer = num1 - num2
        problem = f"{num1} - {num2}"
    elif operation == 'multiplication':
        num1 = random.randint(1, adjusted_max_val)
        num2 = random.randint(1, adjusted_max_val)
        answer = num1 * num2
        problem = f"{num1} * {num2}"
    elif operation == 'division':
        num2 = random.randint(1, adjusted_max_val)
        answer = random.randint(1, adjusted_max_val)
        num1 = num2 * answer
        problem = f"{num1} / {num2}"

    return problem, str(answer)

def log_attempt(problem, correct, time_taken, difficulty):
    """
    Log an attempt, updating performance data and adjusting difficulty based on recent performance.
    This function also handles the logic for adjusting the difficulty level based on user performance.
    """
    global config
    # Parse the problem to store its components separately
    problem_parts = problem.split()
    num1 = int(problem_parts[0])
    operation_symbol = problem_parts[1]
    num2 = int(problem_parts[2])
    
    entry = {
        "problem": problem,
        "num1": num1,
        "operation": operation_symbol,
        "num2": num2,
        "correct": correct,
        "time_taken": time_taken,
        "typing_time_estimate": estimate_typing_time(str(eval(problem))),
        "difficulty": difficulty,
        "timestamp": datetime.now().isoformat()
    }
    performance_data.append(entry)

    # Map operation symbols to names
    operation_map = {'+': 'addition', '-': 'subtraction', '*': 'multiplication', '/': 'division'}
    operation = operation_map[operation_symbol]

    # Analyze recent performance for this operation
    recent_attempts = [x for x in performance_data if x['problem'].split()[1] == operation_symbol][-20:]  # Consider last 20 attempts for more data
    recent_correct = sum(1 for x in recent_attempts if x['correct'])
    recent_times = [x['time_taken'] for x in recent_attempts]

    if len(recent_times) > 1:
        mean_time = statistics.mean(recent_times)
        std_dev_time = statistics.stdev(recent_times)
        z_score = (time_taken - mean_time) / std_dev_time if std_dev_time > 0 else 0
    else:
        z_score = 0  # Default to no change if insufficient data

    # Define performance criteria (more forgiving and encouraging)
    high_performance_z = -0.5  # Better than 0.5 SD below the mean time
    low_performance_z = 0.5    # Worse than 0.5 SD above the mean time

    # Adjust difficulty based on performance
    if recent_correct / len(recent_attempts) > 0.75 and z_score <= high_performance_z:
        config['difficulties'][operation] += 1  # Increase difficulty
    elif recent_correct / len(recent_attempts) < 0.6 or z_score >= low_performance_z:
        config['difficulties'][operation] = max(1, config['difficulties'][operation] - 1)  # Decrease difficulty but not below 1

    save_config(config)

def estimate_typing_time(answer):
    """
    Estimate the time it takes to type an answer.
    This function provides a simple estimate based on the length of the answer
    and an average typing speed.
    """
    # Average time per character in seconds (adjust based on typical user typing speed)
    avg_time_per_char = 0.2
    # Base time for processing the problem (thinking time)
    base_time = 0.5
    
    return base_time + (len(answer) * avg_time_per_char)

def load_config():
    """
    Load the configuration from a JSON file.
    """
    default_config = {
        'operations': {'addition': True, 'subtraction': True, 'multiplication': True, 'division': True},
        'difficulties': {'addition': 1, 'subtraction': 1, 'multiplication': 1, 'division': 1},
        'allow_negative': True
    }
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            return json.load(f)
    else:
        return default_config

def save_config(config):
    """
    Save the configuration to a JSON file.
    """
    with open(config_file_path, 'w') as f:
        json.dump(config, f, indent=4)

def main_menu(term):
    """
    Display the main menu and handle user interactions.
    This function uses the blessed library to handle terminal input/output.
    """
    global config
    while True:
        print(term.clear)
        menu_items = [
            'Start Game',
            'Operations',
            'Difficulties',
            f"Allow Negative Results: {'Enabled' if config['allow_negative'] else 'Disabled'}",
            'Stats',  # Added Stats option
            'Quit'
        ]
        current_selection = 0

        with term.cbreak(), term.hidden_cursor():
            while True:
                print(term.clear)
                for i, item in enumerate(menu_items):
                    if i == current_selection:
                        print(term.reverse + item)
                    else:
                        print(term.normal + item)

                key = term.inkey()
                if key.code == term.KEY_UP:
                    current_selection = max(0, current_selection - 1)
                elif key.code == term.KEY_DOWN:
                    current_selection = min(len(menu_items) - 1, current_selection + 1)
                elif key.code == term.KEY_ENTER:
                    if menu_items[current_selection] == 'Quit':
                        print(term.normal, term.clear, end="")
                        return
                    elif menu_items[current_selection] == 'Start Game':
                        main_game(term)
                    elif menu_items[current_selection] == 'Operations':
                        toggle_operations(term)
                    elif menu_items[current_selection] == 'Difficulties':
                        adjust_difficulties(term)
                    elif menu_items[current_selection] == 'Stats':
                        display_stats(term)  # Handle Stats selection
                    elif menu_items[current_selection].startswith('Allow Negative Results'):
                        config['allow_negative'] = not config['allow_negative']
                        menu_items[current_selection] = f"Allow Negative Results: {'Enabled' if config['allow_negative'] else 'Disabled'}"
                        save_config(config)
                elif key.lower() == 'q':
                    print(term.normal, term.clear, end="")
                    return

def toggle_operations(term):
    """
    Toggle operations on and off.
    This function allows the user to enable or disable specific math operations.
    """
    global config
    operations = list(config['operations'].keys())
    current_selection = 0
    with term.cbreak(), term.hidden_cursor():
        while True:
            print(term.clear)
            for i, op in enumerate(operations):
                if config['operations'][op]:
                    status = "Enabled"
                else:
                    status = "Disabled"
                if i == current_selection:
                    print(term.reverse + f"{op}: {status}")
                else:
                    print(term.normal + f"{op}: {status}")

            key = term.inkey()
            if key.code == term.KEY_UP:
                current_selection = max(0, current_selection - 1)
            elif key.code == term.KEY_DOWN:
                current_selection = min(len(operations) - 1, current_selection + 1)
            elif key.code == term.KEY_ENTER:
                op = operations[current_selection]
                config['operations'][op] = not config['operations'][op]
                save_config(config)
            elif key.lower() == 'q':
                return

def adjust_difficulties(term):
    """
    Adjust difficulties for each operation.
    This function allows the user to manually adjust the difficulty levels for each math operation.
    """
    global config
    operations = list(config['difficulties'].keys())
    current_selection = 0
    with term.cbreak(), term.hidden_cursor():
        while True:
            print(term.clear)
            for i, op in enumerate(operations):
                difficulty = config['difficulties'][op]
                if i == current_selection:
                    print(term.reverse + f"{op}: {difficulty}")
                else:
                    print(term.normal + f"{op}: {difficulty}")

            key = term.inkey()
            if key.code == term.KEY_UP:
                current_selection = max(0, current_selection - 1)
            elif key.code == term.KEY_DOWN:
                current_selection = min(len(operations) - 1, current_selection + 1)
            elif key.code == term.KEY_LEFT:
                if config['difficulties'][operations[current_selection]] > 1:
                    config['difficulties'][operations[current_selection]] -= 1
                    save_config(config)
            elif key.code == term.KEY_RIGHT:
                config['difficulties'][operations[current_selection]] += 1
                save_config(config)
            elif key.lower() == 'q':
                return
            
def display_stats(term):
    """
    Display enhanced statistics about the user's performance.
    This function provides a detailed breakdown of the user's performance across different operations.
    """
    if not performance_data:
        print(term.clear + "No data available.")
        return

    operation_counts = {op: {'correct': 0, 'incorrect': 0, 'total_time': 0, 'times': []} for op in ['addition', 'subtraction', 'multiplication', 'division']}
    correct_streaks = []
    current_streak = 0
    last_problems = performance_data[-10:]  # Last 10 problems for recent trend

    for entry in performance_data:
        op = entry['problem'].split()[1]
        if op == '+':
            op = 'addition'
        elif op == '-':
            op = 'subtraction'
        elif op == '*':
            op = 'multiplication'
        elif op == '/':
            op = 'division'

        if entry['correct']:
            operation_counts[op]['correct'] += 1
            current_streak += 1
        else:
            operation_counts[op]['incorrect'] += 1
            correct_streaks.append(current_streak)
            current_streak = 0
        operation_counts[op]['total_time'] += entry['time_taken']
        operation_counts[op]['times'].append(entry['time_taken'])

    correct_streaks.append(current_streak)  # Add the last streak
    longest_streak = max(correct_streaks)

    print(term.clear)
    for op, stats in operation_counts.items():
        total_attempts = stats['correct'] + stats['incorrect']
        if total_attempts == 0:
            continue
        accuracy = (stats['correct'] / total_attempts) * 100
        avg_time = stats['total_time'] / total_attempts
        median_time = statistics.median(stats['times']) if stats['times'] else 0
        mode_time = statistics.mode(stats['times']) if stats['times'] else 0
        std_dev_time = statistics.stdev(stats['times']) if len(stats['times']) > 1 else 0
        print(f"{op.title()} - Accuracy: {accuracy:.2f}%, Average Time: {avg_time:.2f}s, Median Time: {median_time:.2f}s, Mode Time: {mode_time:.2f}s, Std Dev Time: {std_dev_time:.2f}s")

    print(f"\nLongest Correct Streak: {longest_streak}")
    recent_accuracy = sum(1 for x in last_problems if x['correct']) / len(last_problems) * 100 if last_problems else 0
    recent_avg_time = sum(x['time_taken'] for x in last_problems) / len(last_problems) if last_problems else 0
    print(f"Recent Performance (Last 10): Accuracy: {recent_accuracy:.2f}%, Average Time: {recent_avg_time:.2f}s")

    print("\nPress any key to return.")
    term.inkey()

def get_specific_problem_history(num1, operation, num2):
    """
    Get history of a specific problem including the exact problem and variants
    where operands are in different order for commutative operations.
    
    Returns: List of entries for this specific problem
    """
    exact_match = []
    similar_match = []  # For commutative operations (a+b = b+a, a*b = b*a)
    
    for entry in performance_data:
        # Check for exact match
        if (entry.get('num1') == num1 and 
            entry.get('operation') == operation and 
            entry.get('num2') == num2):
            exact_match.append(entry)
        
        # For addition and multiplication, check for commutative variant
        if operation in ['+', '*'] and (entry.get('num1') == num2 and 
                                        entry.get('operation') == operation and 
                                        entry.get('num2') == num1):
            similar_match.append(entry)
    
    return exact_match, similar_match

def evaluate_problem_difficulty(num1, operation, num2, normalized_typing_time):
    """
    Evaluate how difficult a specific problem is for the user based on:
    1. Previous correctness
    2. Time taken to solve (adjusted for typing time)
    3. Problem variants (e.g., 4+12 vs 12+4)
    
    Returns a score where higher means the user needs more practice on this problem
    """
    # Get history for this exact problem and similar problems (commutative variants)
    exact_history, similar_history = get_specific_problem_history(num1, operation, num2)
    
    # Initialize base score
    score = 1.0
    
    # Factor 1: Has the player gotten this wrong before?
    exact_wrong = sum(1 for entry in exact_history if not entry['correct'])
    if exact_wrong > 0:
        # Increase score if user has gotten this wrong before
        score += min(exact_wrong * 0.5, 2.0)  # Cap at 2.0
    
    # Factor 2: Has the player gotten this right before?
    exact_correct = sum(1 for entry in exact_history if entry['correct'])
    if exact_correct > 0:
        # Reduce score if user has gotten this right before (but not to zero)
        score = max(0.5, score - (0.3 * exact_correct))
    
    # Factor 3: Consider similar problems (for commutative operations)
    if operation in ['+', '*'] and similar_history:
        similar_wrong = sum(1 for entry in similar_history if not entry['correct'])
        similar_correct = sum(1 for entry in similar_history if entry['correct'])
        
        # Slightly increase score for wrong similar problems
        if similar_wrong > 0:
            score += min(similar_wrong * 0.3, 1.0)  # Lower impact, capped at 1.0
            
        # Slightly decrease score for correct similar problems
        if similar_correct > 0:
            score = max(0.3, score - (0.2 * similar_correct))
    
    # Factor 4: Consider typing time impact - we want to avoid giving problems with the same
    # answer repeatedly in a row as it may just be rote memory of typing pattern
    last_five_entries = performance_data[-5:] if performance_data else []
    recent_answers = [str(eval(f"{entry.get('num1')} {entry.get('operation')} {entry.get('num2')}")) 
                     for entry in last_five_entries if 'num1' in entry and 'operation' in entry and 'num2' in entry]
    
    current_answer = str(eval(f"{num1} {operation} {num2}"))
    if current_answer in recent_answers:
        # Reduce score for answers we've typed very recently
        score *= 0.7
    
    # Factor 5: Adjust based on normalized typing time
    score *= (1.0 + normalized_typing_time * 0.3)  # Up to 30% boost for problems with complex answers
    
    return score

def smart_generate_problem(operation, difficulty, allow_negative):
    """
    Generate a math problem using smart selection based on user performance history.
    This version considers:
    1. Time to solve problems (adjusted for typing time)
    2. Previous right/wrong answers
    3. Problem variants (e.g., 4+12 vs 12+4)
    """
    # Adjusted scaling: use a smaller base for exponential growth
    base_val = 5  # Base value for difficulty scaling
    growth_factor = 1.1  # Growth factor for each difficulty level
    
    # Maximum value based on difficulty
    adjusted_max_val = int(base_val * (growth_factor ** (difficulty - 1)))
    
    # Generate candidate problems and evaluate them
    candidates = []
    max_candidates = 10  # Generate several candidates and pick the best one
    
    for _ in range(max_candidates):
        if operation == 'addition':
            num1 = random.randint(1, adjusted_max_val)
            num2 = random.randint(1, adjusted_max_val)
            answer = num1 + num2
            problem = f"{num1} + {num2}"
            
            # Sometimes swap operands to ensure we practice different representations
            if random.random() < 0.5:
                problem = f"{num2} + {num1}"
                # Answer remains the same
            
        elif operation == 'subtraction':
            num1 = random.randint(1, adjusted_max_val)
            num2 = random.randint(1, num1) if not allow_negative else random.randint(1, adjusted_max_val)
            answer = num1 - num2
            problem = f"{num1} - {num2}"
            
        elif operation == 'multiplication':
            num1 = random.randint(1, adjusted_max_val)
            num2 = random.randint(1, adjusted_max_val)
            answer = num1 * num2
            problem = f"{num1} * {num2}"
            
            # Sometimes swap operands to ensure we practice different representations
            if random.random() < 0.5:
                problem = f"{num2} * {num1}"
                # Answer remains the same
                
        elif operation == 'division':
            num2 = random.randint(1, adjusted_max_val)
            answer = random.randint(1, adjusted_max_val)
            num1 = num2 * answer
            problem = f"{num1} / {num2}"
        
        # Parse the problem to evaluate difficulty
        problem_parts = problem.split()
        candidate_num1 = int(problem_parts[0])
        candidate_op = problem_parts[1]
        candidate_num2 = int(problem_parts[2])
        
        # Estimate typing time and normalize it
        answer_str = str(eval(problem))
        typing_time = estimate_typing_time(answer_str)
        normalized_typing_time = min(1.0, typing_time / 5.0)  # Normalize to 0-1 range, cap at 1.0
        
        # Evaluate problem difficulty
        score = evaluate_problem_difficulty(candidate_num1, candidate_op, candidate_num2, normalized_typing_time)
        
        candidates.append((problem, str(answer), score))
    
    # Choose based on weighted scores (higher score = higher chance of selection)
    total_score = sum(score for _, _, score in candidates)
    if total_score > 0:
        # Select problem weighted by difficulty score
        selection_weights = [score/total_score for _, _, score in candidates]
        selected_index = random.choices(range(len(candidates)), weights=selection_weights, k=1)[0]
        return candidates[selected_index][0], candidates[selected_index][1]
    else:
        # Fallback if scores are all zero
        return candidates[0][0], candidates[0][1]

def main_game(term):
    """
    Main game loop where the user is presented with math problems to solve.
    This function handles the game logic, including generating problems, checking answers, and logging attempts.
    """
    global config
    operations = config['operations']
    allow_negative = config['allow_negative']

    try:
        exit_game = False
        with term.cbreak(), term.hidden_cursor():
            while True:
                difficulties = config['difficulties']
                problem_weights = get_problem_weights()
                operation = random.choices(list(operations.keys()), weights=[problem_weights.get(op, 1) for op in operations], k=1)[0]
                problem, correct_answer = smart_generate_problem(operation, difficulties[operation], allow_negative)
                print(term.clear + term.bright_green + term.move_yx(0, 0) + f"Solve: {term.normal}{problem} = ", end="", flush=True)

                user_answer = ""
                start_time = time.time()
                for char in correct_answer:
                    if exit_game:
                        continue
                    inp = term.inkey()
                    if inp == 'q':
                        print(term.clear + "Quitting...")
                        exit_game = True
                        return  # Exit the loop to save data
                    if inp == char:
                        user_answer += inp
                        print(term.green + inp, end="", flush=True)
                    else:
                        print(f"{term.red}{inp}\n       {term.bright_green}{problem} {term.normal}= {term.bright_green}{correct_answer}{term.normal}", flush=True)
                        log_attempt(problem, False, time.time() - start_time, difficulties[operation])
                        # Ignore any input during the cooldown period
                        start_cooldown = time.time()
                        while time.time() - start_cooldown < 1.5:
                            term.inkey(timeout=1.5 - (time.time() - start_cooldown))
                        break
                else:
                    if len(user_answer) == len(correct_answer):
                        log_attempt(problem, True, time.time() - start_time, difficulties[operation])
    finally:
        save_performance_data()  # Save data when exiting the game loop

def main():
    """
    Main function to run the application.
    This function initializes the terminal and loads necessary configurations before starting the main menu.
    """
    term = Terminal()
    load_performance_data()  # Load data once at startup
    global config
    config = load_config()
    main_menu(term)

if __name__ == "__main__":
    main()
