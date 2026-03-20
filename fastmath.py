#!/usr/bin/env python3

__version__ = "2.0.0"

import random
import time
import statistics
import os
import json
import operator
from blessed import Terminal
from datetime import datetime
from platformdirs import user_data_dir

SAFE_OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}

def safe_eval_basic(num1, op, num2):
    """Evaluate a basic arithmetic expression without eval()."""
    if op not in SAFE_OPS:
        raise ValueError(f"Unknown operator: {op}")
    result = SAFE_OPS[op](num1, num2)
    if isinstance(result, float) and result == int(result):
        return int(result)
    return result

def safe_eval_problem(problem_str):
    """Safely evaluate a basic 'num1 op num2' problem string."""
    parts = problem_str.split()
    if len(parts) != 3:
        raise ValueError(f"Cannot safely evaluate: {problem_str}")
    result = safe_eval_basic(int(parts[0]), parts[1], int(parts[2]))
    if isinstance(result, float) and result == int(result):
        return int(result)
    return result



# Define application data directory
app_data_dir = user_data_dir(appname="fastmath", appauthor="michaelkrauty")
os.makedirs(app_data_dir, exist_ok=True)

# File paths for persistent storage
performance_data_file_path = os.path.join(app_data_dir, "performance.json")  # Stores user performance history
config_file_path = os.path.join(app_data_dir, "config.json")  # Stores user configuration settings

# List to store performance data of the user - loaded from file at startup
performance_data = []

def save_performance_data():
    """
    Save the performance data to a JSON file.
    If the file does not exist, it creates a new file with an empty list.
    
    This function ensures that user progress is preserved between sessions.
    """
    with open(performance_data_file_path, 'w') as f:
        json.dump(performance_data, f, indent=1)

def load_performance_data():
    """
    Load the performance data from a JSON file.
    
    This function retrieves the user's past performance history from persistent
    storage to enable adaptive difficulty, targeted practice, and progress tracking.
    If the file does not exist, initializes the performance_data as an empty list.
    
    Sets the global performance_data variable which is used throughout the program.
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
    
    Returns:
        dict: A dictionary mapping each problem type to its calculated weight.
              Higher weights indicate areas where more practice is needed.
    """
    problem_stats = {}
    current_time = datetime.now()

    for entry in performance_data:
        # Determine problem type based on the problem structure or explicit problem_type field
        problem_type = entry.get('problem_type', None)
        
        if problem_type == 'algebra':
            # Skip algebra problems for the purpose of basic operation weights
            continue
            
        # For basic math problems, extract the operation symbol
        try:
            problem_parts = entry['problem'].split()
            if len(problem_parts) >= 3:  # Make sure the problem has enough parts
                problem_type = problem_parts[1]
                
                # Map operation symbols to their corresponding operation names
                if problem_type == '+':
                    problem = 'addition'
                elif problem_type == '-':
                    problem = 'subtraction'
                elif problem_type == '*':
                    problem = 'multiplication'
                elif problem_type == '/':
                    problem = 'division'
                else:
                    continue  # Skip if not a recognized operation
            else:
                continue  # Skip if problem format is unexpected
        except (KeyError, IndexError):
            # Skip entries that don't have the expected format
            continue

        # Get the difficulty level of the problem, default to 1 if not specified
        difficulty = entry.get('difficulty', 1)  # Default to difficulty level 1 if not specified
        
        # Calculate time difference between now and when the problem was attempted
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
        else:
            # Add default weights for operations with no history
            problem_weights[problem] = 2.5  # Default mid-range weight

    # Ensure all operations have weights
    for operation in ['addition', 'subtraction', 'multiplication', 'division']:
        if operation not in problem_weights:
            problem_weights[operation] = 2.5  # Default weight for operations with no data

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

def log_attempt(problem, correct, time_taken, difficulty, skipped=False):
    """
    Log an attempt, updating performance data and adjusting difficulty based on recent performance.
    This function also handles the logic for adjusting the difficulty level based on user performance.
    """
    global config
    
    # Parse the problem to store its components separately
    problem_parts = problem.split()
    
    # Check if we have enough parts in the problem string
    if len(problem_parts) >= 3:
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
            "typing_time_estimate": estimate_typing_time(str(safe_eval_problem(problem))),
            "difficulty": difficulty,
            "timestamp": datetime.now().isoformat(),
            "skipped": skipped
        }
    else:
        # For problems that don't follow the standard format, create a simpler log entry
        entry = {
            "problem": problem,
            "problem_type": "other",
            "correct": correct,
            "time_taken": time_taken,
            "difficulty": difficulty,
            "timestamp": datetime.now().isoformat(),
            "skipped": skipped
        }
    
    performance_data.append(entry)

    # Only adjust difficulty based on performance if the problem wasn't skipped
    if not skipped:
        # Map operation symbols to names
        operation_map = {'+': 'addition', '-': 'subtraction', '*': 'multiplication', '/': 'division'}
        
        # Only proceed with operation-specific analysis if we have a standard format problem
        if len(problem_parts) >= 3:
            operation_symbol = problem_parts[1]
            if operation_symbol in operation_map:
                operation = operation_map[operation_symbol]
                
                # Analyze recent performance for this operation
                # Safely handle the filtering to avoid index errors
                recent_attempts = []
                for x in performance_data:
                    try:
                        if 'problem' in x and len(x['problem'].split()) >= 3 and x['problem'].split()[1] == operation_symbol:
                            # Don't include skipped problems in performance analysis
                            if not x.get('skipped', False):
                                recent_attempts.append(x)
                    except Exception:
                        # Skip any entry that causes errors
                        continue
                        
                # Take the last 20 entries
                recent_attempts = recent_attempts[-20:]
                
                if recent_attempts:
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
                    if len(recent_attempts) > 0 and recent_correct / len(recent_attempts) > 0.75 and z_score <= high_performance_z:
                        config['difficulties'][operation] += 1  # Increase difficulty
                    elif len(recent_attempts) > 0 and (recent_correct / len(recent_attempts) < 0.6 or z_score >= low_performance_z):
                        config['difficulties'][operation] = max(1, config['difficulties'][operation] - 1)  # Decrease difficulty but not below 1

                    save_config(config)

def estimate_typing_time(answer):
    """
    Estimate the time it takes to type an answer.
    
    This function provides a simple model to account for the mechanical typing time
    when evaluating user performance. It separates thinking/calculation time from
    the physical time needed to enter the result.
    
    Args:
        answer (str): The answer text to be typed
        
    Returns:
        float: Estimated time in seconds it would take to type the answer
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
        'allow_negative': True,
        'algebra': {
            'enabled': False,
            'parentheses': True,
            'exponents': True, 
            'fractions': True,
            'variables': True
        },
        'algebra_difficulties': {
            'parentheses': 1,
            'exponents': 1,
            'fractions': 1,
            'variables': 1
        }
    }
    
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            # Load existing config
            user_config = json.load(f)
            
            # Check if new settings need to be added (for backward compatibility)
            config_updated = False
            
            # Ensure 'algebra' settings exist
            if 'algebra' not in user_config:
                user_config['algebra'] = default_config['algebra']
                config_updated = True
                
            # Ensure 'algebra_difficulties' settings exist
            if 'algebra_difficulties' not in user_config:
                user_config['algebra_difficulties'] = default_config['algebra_difficulties']
                config_updated = True
                
            # Save the updated config if any new keys were added
            if config_updated:
                with open(config_file_path, 'w') as f_write:
                    json.dump(user_config, f_write, indent=4)
                    
            return user_config
    else:
        return default_config

def save_config(config):
    """
    Save the configuration to a JSON file.
    """
    with open(config_file_path, 'w') as f:
        json.dump(config, f, indent=4)

def generate_algebra_problem(algebra_type, difficulty, allow_negative):
    """
    Generate an algebra problem based on the algebra type and difficulty level.
    
    Args:
        algebra_type (str): Type of algebra problem ('parentheses', 'exponents', 'fractions', 'variables')
        difficulty (int): Current difficulty level
        allow_negative (bool): Whether negative results are allowed
    
    Returns:
        tuple: A tuple containing (problem_string, answer_string)
    """
    # Adjusted scaling: use a smaller base for exponential growth
    base_val = 3  # Smaller base value for algebra to start easier
    growth_factor = 1.2  # Slightly larger growth factor for algebra
    
    # Calculate the maximum value based on the difficulty
    adjusted_max_val = int(base_val * (growth_factor ** (difficulty - 1)))
    adjusted_max_val = max(adjusted_max_val, 5)  # Ensure minimum value
    
    if algebra_type == 'parentheses':
        return generate_parentheses_problem(adjusted_max_val, difficulty, allow_negative)
    elif algebra_type == 'exponents':
        return generate_exponents_problem(adjusted_max_val, difficulty, allow_negative)
    elif algebra_type == 'fractions':
        return generate_fractions_problem(adjusted_max_val, difficulty, allow_negative)
    elif algebra_type == 'variables':
        return generate_variables_problem(adjusted_max_val, difficulty, allow_negative)
    
    # Fallback to basic parentheses problem
    return generate_parentheses_problem(adjusted_max_val, 1, allow_negative)

def generate_parentheses_problem(max_val, difficulty, allow_negative):
    """
    Generate a problem involving parentheses.
    
    Examples:
    - (3 + 4) * 2
    - 5 * (8 - 3)
    - (7 + 2) * (6 - 1)
    """
    operations = ['+', '-', '*']
    if difficulty == 1:
        # Simple parentheses with addition/subtraction inside, multiplication outside
        inner_op = random.choice(['+', '-'])
        outer_op = '*'
        
        num1 = random.randint(1, min(max_val, 10))
        num2 = random.randint(1, min(max_val, 10))
        num3 = random.randint(2, min(max_val, 5))  # Small multiplier outside
        
        # Ensure subtraction results in positive (unless negative allowed)
        if inner_op == '-' and not allow_negative and num2 > num1:
            num1, num2 = num2, num1
            
        problem = f"({num1} {inner_op} {num2}) {outer_op} {num3}"
        answer = safe_eval_basic(safe_eval_basic(num1, inner_op, num2), outer_op, num3)

    elif difficulty == 2:
        # More complex operations with larger numbers
        inner_op = random.choice(operations)
        outer_op = random.choice(operations)
        
        num1 = random.randint(1, min(max_val, 20))
        num2 = random.randint(1, min(max_val, 20))
        num3 = random.randint(1, min(max_val, 10))
        
        # Handle inner operation constraints
        if inner_op == '-' and not allow_negative and num2 > num1:
            num1, num2 = num2, num1
        if inner_op == '*':
            # Limit multiplication to avoid very large numbers
            num2 = min(num2, 5)

        # Handle outer operation constraints
        if outer_op == '-' and not allow_negative:
            inner_result = safe_eval_basic(num1, inner_op, num2)
            if num3 > inner_result:
                outer_op = '+'

        problem = f"({num1} {inner_op} {num2}) {outer_op} {num3}"
        answer = safe_eval_basic(safe_eval_basic(num1, inner_op, num2), outer_op, num3)
        
    else:  # difficulty >= 3
        # More complex problems with nested parentheses or multiple operations
        if difficulty >= 4 and random.random() < 0.4:
            # Double parentheses: (a op b) op (c op d)
            op1 = random.choice(operations)
            op2 = random.choice(operations)
            op3 = random.choice(operations)
            
            num1 = random.randint(1, min(max_val, 20))
            num2 = random.randint(1, min(max_val, 20))
            num3 = random.randint(1, min(max_val, 20))
            num4 = random.randint(1, min(max_val, 20))
            
            # Handle operation constraints
            if op1 == '-' and not allow_negative and num2 > num1:
                num1, num2 = num2, num1
            if op2 == '-' and not allow_negative and num4 > num3:
                num3, num4 = num4, num3
            if op1 == '*':
                num2 = min(num2, 5)  # Limit multiplication
            if op2 == '*':
                num4 = min(num4, 5)  # Limit multiplication
                
            problem = f"({num1} {op1} {num2}) {op3} ({num3} {op2} {num4})"

            # Ensure final result is valid
            if op3 == '/' and not allow_negative:
                # Convert to multiplication to avoid division issues
                op3 = '*'
                problem = f"({num1} {op1} {num2}) {op3} ({num3} {op2} {num4})"

            try:
                left = safe_eval_basic(num1, op1, num2)
                right = safe_eval_basic(num3, op2, num4)
                answer = safe_eval_basic(left, op3, right)
            except (ValueError, ZeroDivisionError):
                return generate_parentheses_problem(max_val, difficulty-1, allow_negative)
        else:
            # Three operations with prioritized parentheses: (a op b op c) op d
            op1 = random.choice(operations)
            op2 = random.choice(operations)
            op3 = random.choice(operations)
            
            num1 = random.randint(1, min(max_val, 15))
            num2 = random.randint(1, min(max_val, 15))
            num3 = random.randint(1, min(max_val, 15))
            num4 = random.randint(1, min(max_val, 10))
            
            # Handle specific operations
            if op1 == '-' and not allow_negative and num2 > num1:
                num1, num2 = num2, num1
                
            if op2 == '-' and not allow_negative:
                inner_result = safe_eval_basic(num1, op1, num2)
                if num3 > inner_result:
                    op2 = '+'
            
            if op1 == '*' or op2 == '*':
                # Limit multiplication to avoid large numbers
                num2 = min(num2, 5)
                num3 = min(num3, 5)
            
            problem = f"({num1} {op1} {num2} {op2} {num3}) {op3} {num4}"

            try:
                inner = safe_eval_basic(safe_eval_basic(num1, op1, num2), op2, num3)
                answer = safe_eval_basic(inner, op3, num4)
            except (ValueError, ZeroDivisionError):
                return generate_parentheses_problem(max_val, difficulty-1, allow_negative)
    
    return problem, str(answer)

def generate_exponents_problem(max_val, difficulty, allow_negative):
    """
    Generate a problem involving exponents.
    
    Examples:
    - 2^3
    - 3^2 + 1
    - (2+1)^2
    """
    if difficulty == 1:
        # Simple exponent with small base and power
        base = random.randint(2, min(5, max_val))
        power = random.randint(2, 3)
        
        problem = f"{base}^{power}"
        answer = base ** power
        
    elif difficulty == 2:
        # Exponent with operation
        base = random.randint(2, min(5, max_val))
        power = random.randint(2, 3)
        num = random.randint(1, min(10, max_val))
        
        op = random.choice(['+', '-', '*'])
        if op == '-' and not allow_negative and base**power < num:
            op = '+'

        problem = f"{base}^{power} {op} {num}"
        answer = safe_eval_basic(base**power, op, num)
        
    else:  # difficulty >= 3
        if random.random() < 0.4:
            # Parentheses with exponent: (a op b)^c
            num1 = random.randint(1, min(5, max_val))
            num2 = random.randint(1, min(5, max_val))
            power = random.randint(2, min(difficulty, 3))
            
            op = random.choice(['+', '-'])
            if op == '-' and not allow_negative and num2 > num1:
                num1, num2 = num2, num1
                
            problem = f"({num1} {op} {num2})^{power}"
            
            # Calculate the inner expression
            if op == '+':
                inner = num1 + num2
            else:
                inner = num1 - num2
                
            answer = inner ** power
            
        else:
            # More complex expression with exponents
            base1 = random.randint(2, min(5, max_val))
            power1 = random.randint(2, min(difficulty, 4))
            base2 = random.randint(2, min(5, max_val))
            power2 = random.randint(1, min(difficulty, 3))
            
            op = random.choice(['+', '-', '*'])
            if op == '-' and not allow_negative and base1**power1 < base2**power2:
                op = '+'
                
            problem = f"{base1}^{power1} {op} {base2}^{power2}"
            
            # Calculate the answer correctly
            if op == '+':
                answer = (base1 ** power1) + (base2 ** power2)
            elif op == '-':
                answer = (base1 ** power1) - (base2 ** power2)
            else:  # '*'
                if difficulty < 5:
                    # For lower difficulties, limit multiplication to avoid huge numbers
                    op = random.choice(['+', '-'])
                    if op == '-' and base1**power1 < base2**power2:
                        op = '+'
                    problem = f"{base1}^{power1} {op} {base2}^{power2}"
                    
                    if op == '+':
                        answer = (base1 ** power1) + (base2 ** power2)
                    else:
                        answer = (base1 ** power1) - (base2 ** power2)
                else:
                    answer = (base1 ** power1) * (base2 ** power2)
    
    # Check if the answer is reasonable (not too large)
    if answer > 10000:
        # Fallback to simpler problem
        return generate_exponents_problem(max_val, max(1, difficulty-1), allow_negative)
    
    return problem, str(answer)

def generate_fractions_problem(max_val, difficulty, allow_negative):
    """
    Generate a problem involving fractions.
    
    Examples:
    - 1/2 + 1/4
    - 3/4 - 1/2
    - 2/3 * 3/2
    """
    def gcd(a, b):
        """Find greatest common divisor using Euclidean algorithm"""
        while b:
            a, b = b, a % b
        return a
    
    if difficulty == 1:
        # Simple fractions with addition/subtraction
        # Use common fractions with small denominators
        common_fractions = [(1,2), (1,3), (1,4), (2,3), (3,4)]
        frac1 = random.choice(common_fractions)
        frac2 = random.choice(common_fractions)
        
        op = random.choice(['+', '-'])
        
        # Ensure positive result if negative not allowed
        if op == '-' and not allow_negative:
            frac1_value = frac1[0]/frac1[1]
            frac2_value = frac2[0]/frac2[1]
            if frac2_value > frac1_value:
                frac1, frac2 = frac2, frac1
        
        problem = f"{frac1[0]}/{frac1[1]} {op} {frac2[0]}/{frac2[1]}"
        
        if op == '+':
            num = frac1[0] * frac2[1] + frac2[0] * frac1[1]
            denom = frac1[1] * frac2[1]
        else:  # op == '-'
            num = frac1[0] * frac2[1] - frac2[0] * frac1[1]
            denom = frac1[1] * frac2[1]
        
        # Handle potential negative numerator
        num_sign = 1 if num >= 0 else -1
        num_abs = abs(num)
        
        common_divisor = gcd(num_abs, denom)
        num = (num_sign * num_abs) // common_divisor
        denom = denom // common_divisor
        
        if denom == 1:
            answer = str(num)
        else:
            answer = f"{num}/{denom}"
            
    elif difficulty == 2:
        # Fractions with multiplication/division or mixed operations
        ops = ['+', '-', '*']
        op = random.choice(ops)
        
        # Create fractions with larger denominators
        num1 = random.randint(1, min(9, max_val))
        denom1 = random.randint(num1+1, min(10, max_val+5))
        num2 = random.randint(1, min(9, max_val))
        denom2 = random.randint(num2+1, min(10, max_val+5))
        
        # Ensure not reducing to identical problem types
        if gcd(num1, denom1) != 1:
            num1 = num1 + 1
        if gcd(num2, denom2) != 1:
            num2 = num2 + 1
        
        # Simplify fractions first
        divisor1 = gcd(num1, denom1)
        num1 //= divisor1
        denom1 //= divisor1
        
        divisor2 = gcd(num2, denom2)
        num2 //= divisor2
        denom2 //= divisor2
        
        # Ensure positive result if negative not allowed
        if op == '-' and not allow_negative:
            if num2/denom2 > num1/denom1:
                num1, num2 = num2, num1
                denom1, denom2 = denom2, denom1
        
        problem = f"{num1}/{denom1} {op} {num2}/{denom2}"
        
        if op == '+':
            result_num = num1 * denom2 + num2 * denom1
            result_denom = denom1 * denom2
        elif op == '-':
            result_num = num1 * denom2 - num2 * denom1
            result_denom = denom1 * denom2
        elif op == '*':
            result_num = num1 * num2
            result_denom = denom1 * denom2
        
        # Simplify the result
        num_sign = 1 if result_num >= 0 else -1
        result_num_abs = abs(result_num)
        
        divisor = gcd(result_num_abs, result_denom)
        result_num = (num_sign * result_num_abs) // divisor
        result_denom = result_denom // divisor
        
        if result_denom == 1:
            answer = str(result_num)
        else:
            answer = f"{result_num}/{result_denom}"
            
    else:  # difficulty >= 3
        # Complex fraction operations and mixed numbers
        if random.random() < 0.5 and difficulty >= 4:
            # Mixed numbers or complex operation
            # For higher difficulty, create a problem with 3 fractions
            op1 = random.choice(['+', '-', '*'])
            op2 = random.choice(['+', '-', '*'])
            
            # Ensure reasonable fractions
            num1 = random.randint(1, min(7, max_val))
            denom1 = random.randint(num1+1, min(9, max_val+5))
            num2 = random.randint(1, min(7, max_val))
            denom2 = random.randint(num2+1, min(9, max_val+5))
            num3 = random.randint(1, min(7, max_val))
            denom3 = random.randint(num3+1, min(9, max_val+5))
            
            # Simplify fractions
            divisor1 = gcd(num1, denom1)
            num1 //= divisor1
            denom1 //= divisor1
            
            divisor2 = gcd(num2, denom2)
            num2 //= divisor2
            denom2 //= divisor2
            
            divisor3 = gcd(num3, denom3)
            num3 //= divisor3
            denom3 //= divisor3
            
            # Create problem with parentheses for clarity
            problem = f"({num1}/{denom1} {op1} {num2}/{denom2}) {op2} {num3}/{denom3}"
            
            # Calculate result of the first operation
            if op1 == '+':
                result1_num = num1 * denom2 + num2 * denom1
                result1_denom = denom1 * denom2
            elif op1 == '-':
                result1_num = num1 * denom2 - num2 * denom1
                result1_denom = denom1 * denom2
                # Check if result is negative
                if result1_num < 0 and not allow_negative:
                    result1_num = -result1_num
                    op2 = '+' if op2 == '-' else '-'  # Flip second operation
            elif op1 == '*':
                result1_num = num1 * num2
                result1_denom = denom1 * denom2
            
            # Calculate final result
            if op2 == '+':
                result_num = result1_num * denom3 + num3 * result1_denom
                result_denom = result1_denom * denom3
            elif op2 == '-':
                result_num = result1_num * denom3 - num3 * result1_denom
                result_denom = result1_denom * denom3
                # Check if result is negative
                if result_num < 0 and not allow_negative:
                    # Adjust problem to avoid negative
                    op1, op2 = '+', '+'
                    problem = f"({num1}/{denom1} {op1} {num2}/{denom2}) {op2} {num3}/{denom3}"
                    # Recalculate
                    result1_num = num1 * denom2 + num2 * denom1
                    result1_denom = denom1 * denom2
                    result_num = result1_num * denom3 + num3 * result1_denom
                    result_denom = result1_denom * denom3
            elif op2 == '*':
                result_num = result1_num * num3
                result_denom = result1_denom * denom3
            
            # Simplify the final result
            num_sign = 1 if result_num >= 0 else -1
            result_num_abs = abs(result_num)
            
            divisor = gcd(result_num_abs, result_denom)
            result_num = (num_sign * result_num_abs) // divisor 
            result_denom = result_denom // divisor
            
            if result_denom == 1:
                answer = str(result_num)
            else:
                answer = f"{result_num}/{result_denom}"
                
        else:
            # Mixed numbers or multiple operations with fractions
            whole_num = random.randint(1, min(5, max_val))
            num = random.randint(1, 5)
            denom = random.randint(num+1, 6)
            
            # Combine with another fraction
            num2 = random.randint(1, 5)
            denom2 = random.randint(num2+1, 6)
            
            op = random.choice(['+', '-'])
            if op == '-' and not allow_negative:
                # Ensure result is positive
                # Convert mixed number to improper fraction
                num1_total = whole_num * denom + num
                if num1_total/denom < num2/denom2:
                    op = '+'
            
            problem = f"{whole_num} {num}/{denom} {op} {num2}/{denom2}"
            
            # Convert mixed number to improper fraction
            num1_total = whole_num * denom + num
            
            # Calculate the result
            if op == '+':
                result_num = num1_total * denom2 + num2 * denom
                result_denom = denom * denom2
            else:  # op == '-'
                result_num = num1_total * denom2 - num2 * denom
                result_denom = denom * denom2
            
            # Simplify the result
            num_sign = 1 if result_num >= 0 else -1
            result_num_abs = abs(result_num)
            
            divisor = gcd(result_num_abs, result_denom)
            result_num = (num_sign * result_num_abs) // divisor
            result_denom = result_denom // divisor
            
            # Convert back to mixed number if result is improper fraction
            if abs(result_num) >= result_denom:
                whole_part = result_num // result_denom
                remainder = abs(result_num) % result_denom
                
                if remainder == 0:
                    answer = str(whole_part)
                else:
                    if whole_part == 0:
                        answer = f"{result_num}/{result_denom}"
                    else:
                        sign = "-" if result_num < 0 and whole_part >= 0 else ""
                        answer = f"{sign}{whole_part} {remainder}/{result_denom}"
            else:
                answer = f"{result_num}/{result_denom}"
    
    return problem, answer

def generate_variables_problem(max_val, difficulty, allow_negative):
    """
    Generate a problem involving variables.
    
    Examples:
    - x + 3 = 8
    - 2x + 1 = 7
    - 3x - 5 = 10
    """
    if difficulty == 1:
        # Simple one-step equations: x + a = b or x - a = b
        a = random.randint(1, min(10, max_val))
        
        if random.random() < 0.5:
            # x + a = b
            op = '+'
            x = random.randint(1, min(15, max_val))
            b = x + a
        else:
            # x - a = b
            op = '-'
            x = random.randint(a + 1 if not allow_negative else 1, min(20, max_val))
            b = x - a
        
        problem = f"x {op} {a} = {b}"
        answer = str(x)
        
    elif difficulty == 2:
        # One-step multiplication/division or two-step equations
        if random.random() < 0.5:
            # ax = b or x/a = b
            if random.random() < 0.7:
                # ax = b
                a = random.randint(2, min(5, max_val))
                x = random.randint(1, min(10, max_val))
                b = a * x
                problem = f"{a}x = {b}"
            else:
                # x/a = b
                a = random.randint(2, min(5, max_val))
                b = random.randint(1, min(10, max_val))
                x = a * b
                problem = f"x/{a} = {b}"
        else:
            # ax + b = c or ax - b = c
            a = random.randint(2, min(5, max_val))
            b = random.randint(1, min(10, max_val))
            x = random.randint(1, min(10, max_val))
            
            if random.random() < 0.5:
                op = '+'
                c = a * x + b
            else:
                op = '-'
                c = a * x - b
                if c < 0 and not allow_negative:
                    op = '+'
                    c = a * x + b
            
            problem = f"{a}x {op} {b} = {c}"
            
        answer = str(x)
        
    else:  # difficulty >= 3
        if random.random() < 0.4 and difficulty >= 4:
            # More complex equations with variables on both sides
            a = random.randint(2, min(6, max_val))
            b = random.randint(1, min(10, max_val))
            c = random.randint(1, min(3, a-1)) if a > 1 else 1
            d = random.randint(1, min(10, max_val))
            
            # Create equation ax + b = cx + d
            x = (d - b) / (a - c) if a != c else "No solution"  # Handle special case
            
            # If x is not an integer or negative when not allowed, regenerate
            if x == "No solution" or not isinstance(x, (int, float)) or (isinstance(x, (int, float)) and not float(x).is_integer()) or (isinstance(x, (int, float)) and float(x) < 0 and not allow_negative):
                # Ensure integer solution
                x = random.randint(1, min(10, max_val))
                # Work backwards to create problem
                d = c * x + (b - a * x)
                if d <= 0 and difficulty < 5:
                    d = abs(d) + random.randint(1, 5)
            
            problem = f"{a}x + {b} = {c}x + {d}"
            
            # Format x as integer if it is
            if isinstance(x, (int, float)) and float(x).is_integer():
                answer = str(int(x))
            else:
                answer = str(x)
                
        elif random.random() < 0.3 and difficulty >= 4:
            # Equation with parentheses: a(x + b) = c or a(x - b) = c
            a = random.randint(2, min(5, max_val))
            b = random.randint(1, min(8, max_val))
            
            if random.random() < 0.5:
                op = '+'
            else:
                op = '-'
                
            x = random.randint(1, min(10, max_val))
            
            if op == '+':
                c = a * (x + b)
            else:
                if x < b and not allow_negative:
                    x = b + random.randint(1, 5)
                c = a * (x - b)
            
            problem = f"{a}(x {op} {b}) = {c}"
            answer = str(x)
            
        else:
            # Two-step equation with all operations: ax + b = c
            a = random.randint(2, min(6, max_val))
            x = random.randint(1, min(10, max_val))
            
            # Randomly decide between addition and subtraction
            if random.random() < 0.5:
                op = '+'
                b = random.randint(1, min(20, max_val))
                c = a * x + b
            else:
                op = '-'
                b = random.randint(1, min(20, max_val))
                c = a * x - b
                if c < 0 and not allow_negative:
                    op = '+'
                    c = a * x + b
            
            problem = f"{a}x {op} {b} = {c}"
            answer = str(x)
    
    return problem, answer

def log_algebra_attempt(problem, correct, time_taken, difficulty, algebra_type, skipped=False):
    """
    Log an algebra problem attempt, updating performance data and adjusting difficulty.
    
    Args:
        problem (str): The problem string
        correct (bool): Whether the answer was correct
        time_taken (float): Time taken to solve the problem
        difficulty (int): Current difficulty level
        algebra_type (str): Type of algebra problem
    """
    global config
    
    # Calculate expected answer for typing time estimate
    try:
        if '=' in problem:
            equation_parts = problem.split(' = ')
            answer_str = equation_parts[1].strip()
        else:
            answer_str = str(len(problem))  # rough estimate for typing time
    except Exception:
        answer_str = ""
    
    entry = {
        "problem": problem,
        "problem_type": "algebra",
        "algebra_type": algebra_type,
        "correct": correct,
        "time_taken": time_taken,
        "typing_time_estimate": estimate_typing_time(answer_str),
        "difficulty": difficulty,
        "timestamp": datetime.now().isoformat(),
        "skipped": skipped
    }
    performance_data.append(entry)

    # Analyze recent performance for this algebra type
    recent_attempts = [x for x in performance_data 
                      if x.get('problem_type') == 'algebra' and x.get('algebra_type') == algebra_type][-20:]
                      
    if len(recent_attempts) > 5:  # Need minimum data for adjustment
        recent_correct = sum(1 for x in recent_attempts if x['correct'])
        recent_times = [x['time_taken'] for x in recent_attempts]

        if len(recent_times) > 1:
            mean_time = statistics.mean(recent_times)
            std_dev_time = statistics.stdev(recent_times)
            z_score = (time_taken - mean_time) / std_dev_time if std_dev_time > 0 else 0
        else:
            z_score = 0  # Default to no change if insufficient data

        # Define performance criteria (more forgiving for algebra)
        high_performance_z = -0.3  # Better than 0.3 SD below the mean time
        low_performance_z = 0.7    # Worse than 0.7 SD above the mean time

        # Adjust difficulty based on performance
        if recent_correct / len(recent_attempts) > 0.7 and z_score <= high_performance_z:
            config['algebra_difficulties'][algebra_type] += 1  # Increase difficulty
        elif recent_correct / len(recent_attempts) < 0.5 or z_score >= low_performance_z:
            config['algebra_difficulties'][algebra_type] = max(1, config['algebra_difficulties'][algebra_type] - 1)

        save_config(config)

def algebra_menu(term):
    """
    Display the algebra settings menu and handle user interactions.
    
    This function allows users to:
    1. Toggle algebra mode on/off
    2. Configure individual algebra elements
    3. Adjust algebra difficulty levels
    """
    global config
    while True:
        print(term.clear)
        menu_items = [
            f"Algebra Mode: {'Enabled' if config['algebra']['enabled'] else 'Disabled'}",
            'Configure Algebra Elements',
            'Adjust Algebra Difficulties',
            'Back to Main Menu'
        ]
        current_selection = 0

        with term.cbreak(), term.hidden_cursor():
            while True:
                print(term.clear)
                print(term.bold + "Algebra Settings\n" + term.normal)
                
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
                    if menu_items[current_selection] == 'Back to Main Menu':
                        return
                    elif menu_items[current_selection].startswith('Algebra Mode'):
                        config['algebra']['enabled'] = not config['algebra']['enabled']
                        menu_items[0] = f"Algebra Mode: {'Enabled' if config['algebra']['enabled'] else 'Disabled'}"
                        save_config(config)
                    elif menu_items[current_selection] == 'Configure Algebra Elements':
                        toggle_algebra_operations(term)
                    elif menu_items[current_selection] == 'Adjust Algebra Difficulties':
                        adjust_algebra_difficulties(term)
                elif key.lower() == 'q':
                    return

def toggle_algebra_operations(term):
    """
    Toggle algebra operations and elements on and off.
    
    This function allows the user to enable or disable specific algebra elements
    such as parentheses, exponents, fractions, and variables.
    """
    global config
    
    # List all algebra elements except 'enabled'
    algebra_elements = [element for element in config['algebra'] if element != 'enabled']
    current_selection = 0
    
    with term.cbreak(), term.hidden_cursor():
        while True:
            print(term.clear)
            print(term.bold + "Configure Algebra Elements\n" + term.normal)
            
            for i, element in enumerate(algebra_elements):
                if config['algebra'][element]:
                    status = "Enabled"
                else:
                    status = "Disabled"
                if i == current_selection:
                    print(term.reverse + f"{element.capitalize()}: {status}")
                else:
                    print(term.normal + f"{element.capitalize()}: {status}")

            print("\nPress Enter to toggle, q to return")
            
            key = term.inkey()
            if key.code == term.KEY_UP:
                current_selection = max(0, current_selection - 1)
            elif key.code == term.KEY_DOWN:
                current_selection = min(len(algebra_elements) - 1, current_selection + 1)
            elif key.code == term.KEY_ENTER:
                element = algebra_elements[current_selection]
                config['algebra'][element] = not config['algebra'][element]
                save_config(config)
            elif key.lower() == 'q':
                return

def adjust_algebra_difficulties(term):
    """
    Adjust difficulties for each algebra element.
    This function allows the user to manually adjust the difficulty levels for algebra operations.
    """
    global config
    
    algebra_types = list(config['algebra_difficulties'].keys())
    current_selection = 0
    with term.cbreak(), term.hidden_cursor():
        while True:
            print(term.clear)
            print(term.bold + "Algebra Difficulty Settings\n" + term.normal)
            
            for i, alg_type in enumerate(algebra_types):
                difficulty = config['algebra_difficulties'][alg_type]
                if i == current_selection:
                    print(term.reverse + f"{alg_type.title()}: {difficulty}")
                else:
                    print(term.normal + f"{alg_type.title()}: {difficulty}")

            print("\nUse ← → to adjust difficulty, ↑ ↓ to navigate, Enter/q to return")
            
            key = term.inkey()
            if key.code == term.KEY_UP:
                current_selection = max(0, current_selection - 1)
            elif key.code == term.KEY_DOWN:
                current_selection = min(len(algebra_types) - 1, current_selection + 1)
            elif key.code == term.KEY_LEFT:
                if config['algebra_difficulties'][algebra_types[current_selection]] > 1:
                    config['algebra_difficulties'][algebra_types[current_selection]] -= 1
                    save_config(config)
            elif key.code == term.KEY_RIGHT:
                config['algebra_difficulties'][algebra_types[current_selection]] += 1
                save_config(config)
            elif key.code == term.KEY_ENTER or key.lower() == 'q':
                return

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
            'Algebra', # Add algebra menu option
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
                    elif menu_items[current_selection] == 'Algebra':
                        algebra_menu(term)  # New algebra menu
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

    op_map = {'+': 'addition', '-': 'subtraction', '*': 'multiplication', '/': 'division'}
    operation_counts = {op: {'correct': 0, 'incorrect': 0, 'total_time': 0, 'times': []} for op in ['addition', 'subtraction', 'multiplication', 'division']}
    algebra_counts = {'correct': 0, 'incorrect': 0, 'total_time': 0, 'times': []}
    correct_streaks = []
    current_streak = 0
    last_problems = performance_data[-10:]  # Last 10 problems for recent trend

    for entry in performance_data:
        # Handle algebra problems separately
        if entry.get('problem_type') == 'algebra':
            if entry['correct']:
                algebra_counts['correct'] += 1
                current_streak += 1
            else:
                algebra_counts['incorrect'] += 1
                correct_streaks.append(current_streak)
                current_streak = 0
            algebra_counts['total_time'] += entry['time_taken']
            algebra_counts['times'].append(entry['time_taken'])
            continue

        parts = entry['problem'].split()
        if len(parts) < 3 or parts[1] not in op_map:
            continue
        op = op_map[parts[1]]

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

    # Show algebra stats if any exist
    algebra_total = algebra_counts['correct'] + algebra_counts['incorrect']
    if algebra_total > 0:
        alg_accuracy = (algebra_counts['correct'] / algebra_total) * 100
        alg_avg_time = algebra_counts['total_time'] / algebra_total
        alg_median_time = statistics.median(algebra_counts['times'])
        print(f"Algebra - Accuracy: {alg_accuracy:.2f}%, Average Time: {alg_avg_time:.2f}s, Median Time: {alg_median_time:.2f}s")

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
    Evaluate how difficult a specific problem is for the user.
    
    This function implements a sophisticated algorithm to assess problem difficulty
    based on multiple factors:
    
    1. Previous correctness - problems the user got wrong are prioritized
    2. Time taken to solve - adjusted for typing time
    3. Problem variants - considers commutative variants (e.g., 4+12 vs 12+4)
    4. Spaced repetition principles - optimal timing for review
    
    The resulting score is used to prioritize problems that will be most beneficial
    for the user's learning progression.
    
    Args:
        num1 (int): First operand
        operation (str): Operation symbol (+, -, *, /)
        num2 (int): Second operand
        normalized_typing_time (float): Typing time normalized to 0-1 range
        
    Returns:
        float: A score where higher means the user needs more practice on this problem
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
    recent_answers = [str(safe_eval_basic(entry['num1'], entry['operation'], entry['num2']))
                     for entry in last_five_entries if 'num1' in entry and 'operation' in entry and 'num2' in entry]

    current_answer = str(safe_eval_basic(num1, operation, num2))
    if current_answer in recent_answers:
        # Reduce score for answers we've typed very recently
        score *= 0.7
    
    # Factor 5: Apply spaced repetition principles
    if exact_history or similar_history:
        # Combine histories for spaced repetition analysis
        combined_history = sorted(
            exact_history + similar_history,
            key=lambda x: datetime.fromisoformat(x['timestamp'])
        )
        
        if combined_history:
            latest_timestamp = datetime.fromisoformat(combined_history[-1]['timestamp'])
            current_time = datetime.now()
            days_since_last_seen = (current_time - latest_timestamp).total_seconds() / (24 * 3600)
            
            # Optimal spacing based on performance (simplified Ebbinghaus forgetting curve)
            # The better the performance, the longer optimal spacing
            correct_ratio = sum(1 for x in combined_history if x['correct']) / len(combined_history)
            
            # Calculate optimal interval in days based on performance
            optimal_interval = 1.0 + (correct_ratio * 5.0)  # 1-6 days depending on performance
            
            # Calculate how "due" this problem is (>1 means overdue, <1 means too soon)
            due_factor = days_since_last_seen / optimal_interval
            
            # Adjust score based on due factor
            if due_factor < 0.5:
                # Too soon to review
                score *= 0.5
            elif due_factor > 0.8 and due_factor < 1.2:
                # Optimal time to review
                score *= 1.5
            elif due_factor > 2.0:
                # Overdue for review
                score *= 1.3
    
    # Factor 6: Adjust based on normalized typing time
    score *= (1.0 + normalized_typing_time * 0.3)  # Up to 30% boost for problems with complex answers
    
    return score

def smart_generate_problem(operation, difficulty, allow_negative):
    """
    Generate a math problem using intelligent selection based on user performance.
    
    This sophisticated problem generator uses multiple strategies to create
    problems that are optimally beneficial for the user's learning:
    
    1. User performance history - focuses on areas of weakness
    2. Spaced repetition principles - times review of concepts optimally
    3. Learning curve analysis - gradually increases complexity
    4. Pattern detection in errors - targets specific error patterns
    5. Adaptive difficulty targeting - adjusts to user skill level
    6. Educational value assessment - prioritizes pedagogically important concepts
    
    Args:
        operation (str): The type of operation ('addition', 'subtraction', etc.)
        difficulty (int): The current difficulty level for this operation
        allow_negative (bool): Whether negative results are allowed
        
    Returns:
        tuple: A tuple containing (problem_string, answer_string)
    """
    # Adjusted scaling: use a smaller base for exponential growth
    base_val = 5  # Base value for difficulty scaling
    growth_factor = 1.1  # Growth factor for each difficulty level
    
    # Maximum value based on difficulty
    adjusted_max_val = int(base_val * (growth_factor ** (difficulty - 1)))
    # Ensure minimum value for calculations
    adjusted_max_val = max(adjusted_max_val, 10)
    
    # Check for patterns in recent mistakes
    pattern_detected = check_error_patterns()
    
    # Generate candidate problems and evaluate them
    candidates = []
    # Generate more candidates for a better selection
    max_candidates = 25  # Increased to allow more filtering while still having choices
    
    # Smart problem targeting: focus on detected error patterns
    if pattern_detected and random.random() < 0.7:  # 70% chance to target pattern
        # Generate problems specifically addressing the detected pattern
        for _ in range(max_candidates):
            problem, answer = generate_targeted_problem(pattern_detected, adjusted_max_val, allow_negative)
            if problem is None:  # Fallback if targeted generation fails
                break
            
            # Parse the problem to evaluate difficulty
            problem_parts = problem.split()
            candidate_num1 = int(problem_parts[0])
            candidate_op = problem_parts[1]
            candidate_num2 = int(problem_parts[2])
            
            # Skip trivial problems
            if is_trivial_problem(candidate_num1, candidate_op, candidate_num2):
                continue
            
            # Estimate typing time and normalize it
            answer_str = str(answer)
            typing_time = estimate_typing_time(answer_str)
            normalized_typing_time = min(1.0, typing_time / 5.0)
            
            # Evaluate problem difficulty with higher base score for targeted problems
            score = evaluate_problem_difficulty(candidate_num1, candidate_op, candidate_num2, normalized_typing_time) * 1.5
            
            # Apply educational value adjustment
            score = adjust_problem_score(candidate_num1, candidate_op, candidate_num2, score, difficulty)
            
            candidates.append((problem, str(answer), score))
    
    # Sometimes prioritize educationally valuable problems (independent of error patterns)
    educational_focus = random.random() < 0.25  # 25% of problems should focus on educational value
    
    # Fill remaining candidates with regular problems
    attempts = 0  # Limit attempts to prevent infinite loops
    while len(candidates) < max_candidates and attempts < 50:
        attempts += 1
        
        if operation == 'addition':
            num1 = random.randint(1, adjusted_max_val)
            num2 = random.randint(1, adjusted_max_val)
            
            # Skip trivial problems
            if is_trivial_problem(num1, '+', num2):
                continue
                
            # For educational focus, encourage specific patterns
            if educational_focus:
                # Focus on "make 10" strategies (important for number bonds)
                if random.random() < 0.3 and adjusted_max_val >= 10:
                    target = 10
                    if random.random() < 0.5 and adjusted_max_val >= 100:
                        target = 100  # Sometimes practice making 100
                    
                    # Ensure at least one number is within range
                    if target <= adjusted_max_val:
                        num1 = random.randint(1, min(target - 1, adjusted_max_val))
                        num2 = target - num1
            
            answer = num1 + num2
            
            # Variation 1: Sometimes practice adding to make a round number
            if not educational_focus and random.random() < 0.15 and difficulty > 1:
                # Choose a round number target appropriate for the difficulty level
                possible_targets = [10, 20, 50, 100, 200, 500, 1000]
                suitable_targets = [t for t in possible_targets if t <= adjusted_max_val * 2]
                if suitable_targets:
                    target = random.choice(suitable_targets)
                    num1 = random.randint(1, target-1)
                    num2 = target - num1
                    
                    # Skip if this results in a trivial problem
                    if is_trivial_problem(num1, '+', num2):
                        continue
                        
                    answer = target
            
            problem = f"{num1} + {num2}"
            
            # Sometimes swap operands to ensure we practice different representations
            if random.random() < 0.5:
                problem = f"{num2} + {num1}"
            
        elif operation == 'subtraction':
            num1 = random.randint(1, adjusted_max_val)
            
            # For educational focus, encourage pedagogically important patterns
            if educational_focus:
                # Prioritize subtracting from 10s, 100s (important skill)
                if random.random() < 0.4:
                    base_options = []
                    if adjusted_max_val >= 10:
                        base_options.append(10)
                    if adjusted_max_val >= 20:
                        base_options.append(20)
                    if adjusted_max_val >= 100:
                        base_options.append(100)
                    
                    if base_options:
                        num1 = random.choice(base_options)
                        num2 = random.randint(1, num1 if not allow_negative else min(num1 + 10, adjusted_max_val))
            
            # Variation 1: Practice subtraction from round numbers
            if not educational_focus and random.random() < 0.15 and difficulty > 1:
                # Choose a round number appropriate for the difficulty level
                possible_targets = [10, 20, 50, 100, 200, 500, 1000]
                suitable_targets = [t for t in possible_targets if t <= adjusted_max_val]
                if suitable_targets:
                    num1 = random.choice(suitable_targets)
                    num2 = random.randint(1, num1)
                else:
                    num2 = random.randint(1, num1) if not allow_negative else random.randint(1, adjusted_max_val)
            else:
                num2 = random.randint(1, num1) if not allow_negative else random.randint(1, adjusted_max_val)
            
            # Skip trivial problems
            if is_trivial_problem(num1, '-', num2):
                continue
                
            answer = num1 - num2
            problem = f"{num1} - {num2}"
            
        elif operation == 'multiplication':
            # For educational focus, prioritize multiplication tables and patterns
            if educational_focus:
                # Focus on multiplication tables
                if random.random() < 0.6:
                    num1 = random.randint(2, min(12, adjusted_max_val))
                    num2 = random.randint(2, min(12, adjusted_max_val))
                # Focus on multiplying by 9 (special patterns)
                elif random.random() < 0.5:
                    if adjusted_max_val >= 9:
                        num1 = 9
                        max_factor = adjusted_max_val // 9
                        # Ensure we have a valid range for random.randint
                        if max_factor >= 2:
                            num2 = random.randint(2, min(max_factor, 12))
                        else:
                            num2 = 2
                    else:
                        num1 = random.randint(2, min(adjusted_max_val, 12))
                        num2 = random.randint(2, min(adjusted_max_val, 12))
                # Doubling (×2) and near-doubles (×4, ×8) - important strategies
                else:
                    multiplier = random.choice([2, 4, 8])
                    if adjusted_max_val >= multiplier:
                        num2 = multiplier
                        max_factor = adjusted_max_val // multiplier
                        num1 = random.randint(2, max_factor)
                    else:
                        num1 = random.randint(2, min(adjusted_max_val, 12))
                        num2 = random.randint(2, min(adjusted_max_val, 12))
            # Standard approach
            else:
                # Variation 1: More frequent practice with small numbers, important number pairs
                if random.random() < 0.2:
                    num1 = random.randint(2, min(12, adjusted_max_val))  # Start from 2 to avoid multiplying by 1
                    num2 = random.randint(2, min(12, adjusted_max_val))  # Start from 2 to avoid multiplying by 1
                # Variation 2: Practice multiplication by 10, 100, etc.
                elif random.random() < 0.15 and difficulty > 1:
                    # Determine appropriate multipliers based on the max value
                    possible_multipliers = []
                    if adjusted_max_val >= 10:
                        possible_multipliers.append(10)
                    if adjusted_max_val >= 100:
                        possible_multipliers.append(100)
                    if adjusted_max_val >= 1000:
                        possible_multipliers.append(1000)
                    
                    if possible_multipliers:
                        num2 = random.choice(possible_multipliers)
                        # Make sure we can generate at least one valid num1
                        max_num1 = adjusted_max_val // num2
                        if max_num1 >= 2:  # Start from 2 to avoid multiplying by 1
                            num1 = random.randint(2, max_num1)
                        else:
                            # Fallback to basic multiplication
                            num1 = random.randint(2, adjusted_max_val)
                            # Ensure we don't create an empty range
                            max_divisor = adjusted_max_val // max(1, num1)
                            if max_divisor >= 2:
                                num2 = random.randint(2, max_divisor)
                            else:
                                num2 = 2
                    else:
                        # Fallback to basic multiplication
                        num1 = random.randint(2, adjusted_max_val)
                        # Ensure we don't create an empty range
                        max_divisor = adjusted_max_val // max(1, num1)
                        if max_divisor >= 2:
                            num2 = random.randint(2, max_divisor)
                        else:
                            num2 = 2
                else:
                    # Basic multiplication
                    num1 = random.randint(2, adjusted_max_val)  # Start from 2 to avoid multiplying by 1
                    
                    # Ensure product doesn't exceed adjusted_max_val
                    max_num2 = adjusted_max_val // max(1, num1)
                    # Check if we have a valid range before calling random.randint
                    if max_num2 >= 2:
                        num2 = random.randint(2, max_num2)  # Start from 2 to avoid multiplying by 1
                    else:
                        # If max_num2 is too small, use a fixed value of 2
                        num2 = 2
            
            # Skip trivial problems
            if is_trivial_problem(num1, '*', num2):
                continue
                
            answer = num1 * num2
            problem = f"{num1} * {num2}"
            
            # Sometimes swap operands to ensure we practice different representations
            if random.random() < 0.5:
                problem = f"{num2} * {num1}"
                
        elif operation == 'division':
            # For educational focus, prioritize division patterns
            if educational_focus:
                # Focus on division with single-digit divisors
                if random.random() < 0.4:
                    num2 = random.randint(2, min(9, adjusted_max_val))
                    max_quotient = adjusted_max_val // num2
                    if max_quotient >= 2:
                        answer = random.randint(2, max_quotient)
                    else:
                        answer = 2
                # Focus on division by 2 (halving - important skill)
                elif random.random() < 0.3:
                    if adjusted_max_val >= 2:
                        num2 = 2
                        max_quotient = adjusted_max_val // 2
                        answer = random.randint(2, max_quotient)
                    else:
                        num2 = random.randint(2, adjusted_max_val)
                        answer = 2
                # Division with round numbers (÷10, ÷5, etc.)
                else:
                    divisor_options = []
                    if adjusted_max_val >= 5:
                        divisor_options.append(5)
                    if adjusted_max_val >= 10:
                        divisor_options.append(10)
                    if adjusted_max_val >= 25:
                        divisor_options.append(25)
                    
                    if divisor_options:
                        num2 = random.choice(divisor_options)
                        max_quotient = adjusted_max_val // num2
                        if max_quotient >= 2:
                            answer = random.randint(2, max_quotient)
                        else:
                            answer = 2
                    else:
                        num2 = random.randint(2, adjusted_max_val)
                        answer = 2
            else:
                # Variation 1: More frequent practice with small divisors
                if random.random() < 0.3:
                    num2 = random.randint(2, min(12, adjusted_max_val))  # Start from 2 to avoid division by 1
                    max_answer = adjusted_max_val // num2
                    if max_answer >= 2:  # Make sure we have reasonable answers
                        answer = random.randint(2, max_answer)  # Avoid answer = 1 (too easy)
                    else:
                        # Fallback to basic division with smaller values
                        answer = 2  # Avoid answer = 1 (too easy)
                # Variation 2: Division by 10, 100, etc.
                elif random.random() < 0.15 and difficulty > 2:
                    possible_divisors = []
                    if adjusted_max_val >= 10:
                        possible_divisors.append(10)
                    if adjusted_max_val >= 100:
                        possible_divisors.append(100)
                    
                    if possible_divisors:
                        num2 = random.choice(possible_divisors)
                        max_answer = adjusted_max_val // num2
                        if max_answer >= 2:
                            answer = random.randint(2, max_answer)  # Avoid answer = 1 (too easy)
                        else:
                            answer = 2  # Avoid answer = 1 (too easy)
                    else:
                        # Fallback
                        num2 = random.randint(2, adjusted_max_val)
                        answer = 2  # Avoid answer = 1 (too easy)
                else:
                    # Basic division
                    num2 = random.randint(2, adjusted_max_val)  # Start from 2 to avoid division by 1
                    max_answer = adjusted_max_val // max(1, num2)
                    if max_answer >= 2:
                        answer = random.randint(2, max_answer)  # Avoid answer = 1 (too easy)
                    else:
                        answer = 2  # Avoid answer = 1 (too easy)
            
            num1 = num2 * answer
            
            # Skip trivial problems
            if is_trivial_problem(num1, '/', num2):
                continue
                
            problem = f"{num1} / {num2}"
        
        # Parse the problem to evaluate difficulty
        problem_parts = problem.split()
        candidate_num1 = int(problem_parts[0])
        candidate_op = problem_parts[1]
        candidate_num2 = int(problem_parts[2])
        
        # Estimate typing time and normalize it
        answer_str = str(safe_eval_problem(problem))
        typing_time = estimate_typing_time(answer_str)
        normalized_typing_time = min(1.0, typing_time / 5.0)  # Normalize to 0-1 range, cap at 1.0
        
        # Base problem score from user performance history
        score = evaluate_problem_difficulty(candidate_num1, candidate_op, candidate_num2, normalized_typing_time)
        
        # Apply educational value adjustment
        score = adjust_problem_score(candidate_num1, candidate_op, candidate_num2, score, difficulty)
        
        candidates.append((problem, str(answer), score))
    
    # If we don't have enough candidates after filtering trivial problems, 
    # use the original problem generation as a fallback
    if len(candidates) < 5:
        return generate_problem(operation, difficulty, allow_negative)
        
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

def check_error_patterns():
    """
    Analyze recent errors to identify patterns that need targeted practice.
    
    This function examines the user's recent mistakes and identifies specific
    mathematical concepts where the user is struggling. It uses frequency analysis
    to determine which patterns appear most consistently in errors.
    
    Recognized patterns include:
    - carrying: Addition problems where carrying is required (e.g., 7+8)
    - borrowing: Subtraction problems where borrowing is required (e.g., 52-7)
    - multiplication_tables: Basic multiplication facts (e.g., 6×8)
    - division_remainder: Division problems with remainders
    - large_numbers: Problems with multi-digit numbers
    - zero_handling: Problems involving zero as an operand
    
    Returns:
        str or None: The identified error pattern type or None if no clear pattern exists
    """
    if len(performance_data) < 10:
        return None  # Not enough data to detect patterns
    
    # Focus on recent errors (last 30 entries)
    recent_data = performance_data[-30:]
    recent_errors = [entry for entry in recent_data if not entry['correct']]
    
    if not recent_errors or len(recent_errors) < 3:
        return None  # Not enough errors to detect patterns
    
    # Look for common patterns in errors
    patterns = {
        'carrying': 0,
        'borrowing': 0,
        'multiplication_tables': 0,
        'division_remainder': 0,
        'large_numbers': 0,
        'zero_handling': 0
    }
    
    for entry in recent_errors:
        # Parse problem components
        parts = entry['problem'].split()
        if len(parts) != 3:
            continue
            
        num1 = int(parts[0])
        op = parts[1]
        num2 = int(parts[2])
        
        # Check for specific error patterns
        if op == '+' and (num1 >= 10 or num2 >= 10):
            if num1 % 10 + num2 % 10 >= 10:  # Carrying needed
                patterns['carrying'] += 1
                
        elif op == '-' and num1 >= 10:
            if num1 % 10 < num2 % 10:  # Borrowing needed
                patterns['borrowing'] += 1
                
        elif op == '*':
            if 1 <= num1 <= 12 and 1 <= num2 <= 12:
                patterns['multiplication_tables'] += 1
            if num1 > 100 or num2 > 100:
                patterns['large_numbers'] += 1
                
        elif op == '/':
            if num1 % num2 != 0:  # This shouldn't happen in the current implementation
                patterns['division_remainder'] += 1
                
        # Zero handling problems
        if num1 == 0 or num2 == 0 or (op in ['+', '*'] and (num1 == 0 or num2 == 0)):
            patterns['zero_handling'] += 1
    
    # Find the most common error pattern
    most_common_pattern = max(patterns.items(), key=lambda x: x[1])
    
    # Only return if it appears in at least 20% of errors
    if most_common_pattern[1] >= len(recent_errors) * 0.2:
        return most_common_pattern[0]
    
    return None

def generate_targeted_problem(pattern_type, max_val, allow_negative):
    """
    Generate a problem specifically targeting an identified error pattern.
    
    This function creates tailored problems based on the user's error patterns,
    focusing practice on specific areas of difficulty.
    
    Args:
        pattern_type (str): The type of pattern to target ('carrying', 'borrowing', etc.)
        max_val (int): The maximum value allowed for numbers in the problem
        allow_negative (bool): Whether negative results are allowed
        
    Returns:
        tuple: A tuple containing (problem_string, answer) or (None, None) if generation fails
    """
    if pattern_type == 'carrying':
        # Generate addition problem requiring carrying
        num1 = random.randint(1, min(max_val, 90))
        # Ensure carrying is needed
        num2 = random.randint(10 - num1 % 10, min(max_val, 99))
        return f"{num1} + {num2}", num1 + num2
        
    elif pattern_type == 'borrowing':
        # Generate subtraction problem requiring borrowing
        num1 = random.randint(10, min(max_val, 99))
        # Ensure borrowing is needed
        ones_digit = num1 % 10
        num2 = random.randint(ones_digit + 1, min(num1, 9) + 10)
        if num2 > num1 and not allow_negative:
            # Switch numbers if negative result not allowed
            num1, num2 = num2, num1
        return f"{num1} - {num2}", num1 - num2
        
    elif pattern_type == 'multiplication_tables':
        # Focus on multiplication table entries
        num1 = random.randint(2, min(max_val, 12))
        num2 = random.randint(2, min(max_val, 12))
        return f"{num1} * {num2}", num1 * num2
        
    elif pattern_type == 'large_numbers':
        # Practice with larger numbers
        scale = min(max_val // 10, 100)
        if scale < 10:  # If max_val is small, fallback
            return None, None
            
        num1 = random.randint(scale, min(max_val, scale * 10))
        num2 = random.randint(1, min(max_val, 20))
        
        op = random.choice(['+', '-', '*'])
        if op == '+':
            return f"{num1} + {num2}", num1 + num2
        elif op == '-':
            if num2 > num1 and not allow_negative:
                num1, num2 = num2, num1
            return f"{num1} - {num2}", num1 - num2
        else:  # multiplication
            if num1 * num2 > max_val:
                num1 = max_val // num2
            return f"{num1} * {num2}", num1 * num2
            
    elif pattern_type == 'zero_handling':
        # Practice problems involving zero
        ops = ['+', '-', '*']
        op = random.choice(ops)
        
        if random.random() < 0.5:
            num1 = 0
            num2 = random.randint(1, max_val)
        else:
            num1 = random.randint(1, max_val)
            num2 = 0
            
        if op == '+':
            return f"{num1} + {num2}", num1 + num2
        elif op == '-':
            if num2 > num1 and not allow_negative:
                num1, num2 = num2, num1
            return f"{num1} - {num2}", num1 - num2
        else:  # multiplication
            return f"{num1} * {num2}", num1 * num2
            
    # Division problems with zero require special handling
    elif pattern_type == 'division_remainder':
        # While we don't currently support non-exact division,
        # we can practice division with small numbers
        divisor = random.randint(2, min(max_val, 12))
        quotient = random.randint(1, max_val // divisor)
        dividend = divisor * quotient
        return f"{dividend} / {divisor}", quotient
        
    # If no specific pattern or invalid pattern
    return None, None

def is_trivial_problem(num1, op, num2):
    """
    Check if a problem is trivially easy and should be avoided.
    
    Filters out problems that don't provide meaningful practice, such as
    multiplication by 1 or addition with 0.
    
    Args:
        num1 (int): First operand
        op (str): Operation symbol (+, -, *, /)
        num2 (int): Second operand
        
    Returns:
        bool: True if the problem is considered too basic to be useful
    """
    # Division by 1 (n/1=n)
    if op == '/' and num2 == 1:
        return True
    
    # Multiplication by 1 (n*1=n or 1*n=n)
    if op == '*' and (num1 == 1 or num2 == 1):
        return True
    
    # Addition with 0 (n+0=n or 0+n=n)
    if op == '+' and (num1 == 0 or num2 == 0):
        return True
    
    # Subtraction resulting in 0 (n-n=0)
    if op == '-' and num1 == num2:
        return True
    
    # Subtraction from 0 (0-n)
    # We'll allow this with negative results enabled as it's useful practice
    if op == '-' and num1 == 0:
        return True
    
    # Division resulting in 1 (n/n=1)
    if op == '/' and num1 == num2 and num1 != 0:
        return True
    
    # Division with 0 as dividend (0/n=0)
    if op == '/' and num1 == 0:
        return True
    
    # Very small numbers in higher difficulties (e.g., 2+2 at difficulty > 3)
    # Skip if both numbers are less than 5 in higher difficulties
    global config
    current_op = {'*': 'multiplication', '/': 'division', '+': 'addition', '-': 'subtraction'}[op]
    difficulty = config['difficulties'].get(current_op, 1)
    if difficulty > 3 and max(num1, num2) < 5:
        return True
    
    return False

def is_common_pattern(num1, op, num2):
    """
    Check if a problem falls into a common pattern that should be given priority
    based on educational value.
    
    These patterns are selected based on educational research about which 
    math facts and patterns are most beneficial to practice.
    
    Args:
        num1 (int): First operand
        op (str): Operation symbol (+, -, *, /)
        num2 (int): Second operand
        
    Returns:
        bool: True if the problem represents an important pattern to practice
    """
    # Multiplication table facts - important to master
    if op == '*' and 2 <= num1 <= 10 and 2 <= num2 <= 10:
        return True
    
    # Addition and subtraction with 9s - teaches important patterns
    if op == '+' and (num1 == 9 or num2 == 9):
        return True
    if op == '-' and num1 % 10 == 9:
        return True
    
    # Round number subtraction (e.g., 100-7, 20-8) - important for mental math
    if op == '-' and (num1 in [10, 20, 50, 100, 200, 500, 1000] and num2 < 10):
        return True
        
    # Doubling and halving - important mental math strategy
    if op == '+' and num1 == num2:  # Doubling
        return True
    if op == '/' and num1 / num2 == 2:  # Halving
        return True
        
    # Near multiples - useful for mental math strategies
    if op == '*' and (num1 == 9 or num1 == 11 or num2 == 9 or num2 == 11):
        return True
        
    # Division involving multiples of 10 (fundamental concept)
    if op == '/' and (num1 % 10 == 0 and num2 > 1):
        return True
        
    return False

def adjust_problem_score(num1, op, num2, score, user_difficulty_level):
    """
    Adjust the score of a problem based on its educational value,
    current user level, and math principles.
    
    This function implements an intelligent scoring system that prioritizes
    problems with greater educational benefit and appropriate difficulty.
    
    Args:
        num1 (int): First operand
        op (str): Operation symbol (+, -, *, /)
        num2 (int): Second operand
        score (float): Base score from performance analysis
        user_difficulty_level (int): Current difficulty level for the user
        
    Returns:
        float: Adjusted score - higher scores increase selection probability
    """
    adjusted_score = score
    
    # Boost educationally valuable patterns
    if is_common_pattern(num1, op, num2):
        adjusted_score *= 1.5
    
    # Adjust for difficulty level progression
    if user_difficulty_level <= 3:
        # For beginners, prioritize small numbers and fundamental concepts
        if op in ['+', '-'] and max(num1, num2) <= 10:
            adjusted_score *= 1.2
        if op in ['*', '/'] and max(num1, num2) <= 5:
            adjusted_score *= 1.2
    elif 4 <= user_difficulty_level <= 7:
        # For intermediate learners, focus on teen numbers and basic operations
        if op in ['+', '-'] and (10 <= max(num1, num2) <= 20):
            adjusted_score *= 1.2
        if op == '*' and (5 <= max(num1, num2) <= 12):
            adjusted_score *= 1.2
    else:
        # For advanced learners, prioritize larger numbers and calculations
        if max(num1, num2) >= 20:
            adjusted_score *= 1.1
            
    # Boost problems that build number sense
    if op == '+' and (num1 + num2) == 10:  # Pairs that sum to 10
        adjusted_score *= 1.3
    if op == '+' and (num1 + num2) == 100:  # Pairs that sum to 100
        adjusted_score *= 1.3
    
    # Reduce problems with numbers that are too similar to recent ones
    # This encourages variety in practice
    last_ten_entries = performance_data[-10:] if performance_data else []
    recent_nums = set()
    for entry in last_ten_entries:
        parts = entry.get('problem', '').split()
        if len(parts) == 3:
            recent_nums.add(int(parts[0]))
            recent_nums.add(int(parts[2]))
    
    if num1 in recent_nums and num2 in recent_nums:
        adjusted_score *= 0.7  # Reduce score if both numbers seen recently
    
    return adjusted_score

def main_game(term):
    """
    Main game loop where the user is presented with math problems to solve.
    
    This function:
    1. Selects operations based on weighted probabilities from user performance
    2. Generates appropriate problems using smart selection algorithms
    3. Handles user input with immediate feedback
    4. Records performance metrics for adaptive difficulty
    5. Manages the game flow and exit conditions
    
    Args:
        term: Terminal object from Blessed for handling terminal I/O
    """
    global config
    operations = config['operations']
    allow_negative = config['allow_negative']
    algebra_enabled = config['algebra']['enabled']

    try:
        exit_game = False
        with term.cbreak(), term.hidden_cursor():
            while True:
                # Choose between basic math and algebra
                if algebra_enabled and random.random() < 0.4:  # 40% chance of algebra when enabled
                    # Select an algebra type from enabled ones
                    enabled_algebra_types = [at for at, enabled in config['algebra'].items() 
                                          if enabled and at != 'enabled']
                    
                    if not enabled_algebra_types:  # If no algebra types are enabled
                        problem_type = 'basic'
                    else:
                        problem_type = 'algebra'
                        algebra_type = random.choice(enabled_algebra_types)
                        algebra_difficulty = config['algebra_difficulties'][algebra_type]
                else:
                    problem_type = 'basic'
                
                if problem_type == 'basic':
                    # Standard math problem
                    difficulties = config['difficulties']
                    
                    # Get enabled operations
                    enabled_operations = [op for op, enabled in operations.items() if enabled]
                    if not enabled_operations:
                        print(term.clear + "No operations enabled. Please enable at least one operation.")
                        time.sleep(2)
                        return
                    
                    problem_weights = get_problem_weights()
                    weighted_operations = [(op, problem_weights.get(op, 1)) for op in enabled_operations]
                    operation = random.choices(
                        [op for op, _ in weighted_operations],
                        weights=[weight for _, weight in weighted_operations], 
                        k=1
                    )[0]
                    
                    try:
                        problem, correct_answer = smart_generate_problem(operation, difficulties[operation], allow_negative)
                    except Exception:
                        # Fallback to simple generation if smart generation fails
                        problem, correct_answer = generate_problem(operation, difficulties[operation], allow_negative)
                else:  # algebra problem
                    problem, correct_answer = generate_algebra_problem(algebra_type, algebra_difficulty, allow_negative)

                print(term.clear + term.bright_green + term.move_yx(0, 0) + f"Solve: {term.normal}{problem}", end="", flush=True)
                if "=" not in problem:
                    print(" = ", end="", flush=True)

                user_answer = ""
                start_time = time.time()
                skipped = False
                
                while not skipped and len(user_answer) < len(correct_answer):
                    if exit_game:
                        break
                        
                    inp = term.inkey()
                    
                    # Check for quit
                    if inp == 'q':
                        print(term.clear + "Quitting...")
                        exit_game = True
                        return  # Exit the loop to save data
                        
                    # Check for skip (PGDN)
                    if inp.code == term.KEY_PGDOWN:
                        skipped = True
                        
                        # Print the full answer in green as if the user typed it correctly
                        # First print any characters the user already typed
                        if user_answer:
                            print(term.green + user_answer, end="", flush=True)
                        
                        # Then print the rest of the correct answer
                        remaining_answer = correct_answer[len(user_answer):]
                        print(term.green + remaining_answer, flush=True)
                        
                        # Log the skipped problem as incorrect but mark it as skipped
                        time_taken = time.time() - start_time
                        if problem_type == 'basic':
                            # Parse operation from the problem
                            parts = problem.split()
                            if len(parts) >= 3:
                                op_symbol = parts[1]
                                # Get the operation name
                                op_map = {'+': 'addition', '-': 'subtraction', '*': 'multiplication', '/': 'division'}
                                if op_symbol in op_map:
                                    operation_name = op_map[op_symbol]
                                    # Reduce difficulty for this operation to help user build up to this level
                                    if difficulties[operation_name] > 1:
                                        difficulties[operation_name] -= 1
                                        save_config(config)
                                        
                            log_attempt(problem, False, time_taken, difficulties[operation], skipped=True)
                        else:  # algebra
                            # Reduce difficulty for this algebra type
                            if config['algebra_difficulties'][algebra_type] > 1:
                                config['algebra_difficulties'][algebra_type] -= 1
                                save_config(config)
                                
                            log_algebra_attempt(problem, False, time_taken, algebra_difficulty, algebra_type, skipped=True)
                            
                        # Wait briefly before showing the next problem
                        time.sleep(1)
                        break
                        
                    # Normal input processing
                    if inp == correct_answer[len(user_answer)]:
                        user_answer += inp
                        print(term.green + inp, end="", flush=True)
                    else:
                        print(f"{term.red}{inp}\n{term.bright_green}Problem: {term.normal}{problem}\n{term.bright_green}Answer: {term.normal}{correct_answer}", flush=True)
                        
                        # Log the attempt according to problem type
                        if problem_type == 'basic':
                            log_attempt(problem, False, time.time() - start_time, difficulties[operation])
                        else:  # algebra
                            log_algebra_attempt(problem, False, time.time() - start_time, algebra_difficulty, algebra_type)
                            
                        # Ignore any input during the cooldown period
                        start_cooldown = time.time()
                        while time.time() - start_cooldown < 1.5:
                            term.inkey(timeout=1.5 - (time.time() - start_cooldown))
                        break
                
                # Correct answer completed
                if not skipped and len(user_answer) == len(correct_answer):
                    # Log the attempt according to problem type
                    if problem_type == 'basic':
                        log_attempt(problem, True, time.time() - start_time, difficulties[operation])
                    else:  # algebra
                        log_algebra_attempt(problem, True, time.time() - start_time, algebra_difficulty, algebra_type)
    finally:
        save_performance_data()  # Save data when exiting the game loop

def main():
    """
    Main function to run the application.
    
    This function:
    1. Initializes the terminal interface 
    2. Loads user performance data from persistent storage
    3. Loads configuration settings
    4. Starts the main menu interface
    
    The application follows an MVC-like pattern where data, UI, and 
    logic are reasonably separated.
    """
    term = Terminal()
    load_performance_data()  # Load data once at startup
    global config
    config = load_config()
    main_menu(term)

if __name__ == "__main__":
    main()
