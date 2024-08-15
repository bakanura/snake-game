import random
import curses
import signal
import math

def init_screen():
    global screen, sh, sw, w, game_h, game_w
    screen = curses.initscr()
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    screen.keypad(1)
    
    sh, sw = screen.getmaxyx()
    w = curses.newwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(100)
    
    game_h, game_w = sh - 2, sw - 2

    # Enable resizing
    signal.signal(signal.SIGWINCH, handle_resize)

def initialize_game():
    global snake, food, key, score, snake_level, exp_to_next_level, current_exp, powerups, powerup_active
    
    snake = [
        [sh//2, sw//4],
        [sh//2, sw//4-1],
        [sh//2, sw//4-2]
    ]
    key = curses.KEY_RIGHT
    score = 0
    snake_level = 1
    exp_to_next_level = 5
    current_exp = 0
    powerups = {"speed_boost": 0, "invincibility": 0, "double_points": 0}
    powerup_active = {"speed_boost": False, "invincibility": False, "double_points": False}
    food = generate_food()

def generate_food():
    global snake, sh, sw
    
    # Use snake_level if defined, otherwise use 1 or others
    current_level = snake_level if 'snake_level' in globals() else 1
    
    # Calculate the maximum distance based on the current level
    max_distance = min(10 + current_level, min(sh, sw) // 2)
    
    while True:
        # Generate a random angle
        angle = random.uniform(0, 2 * math.pi)
        
        # Calculate the distance, which increases with the level but is capped
        distance = random.randint(5, max_distance)
        
        # Calculate new food position
        new_x = int(snake[0][1] + distance * math.cos(angle))
        new_y = int(snake[0][0] + distance * math.sin(angle))
        
        # Ensure the food is within the game boundaries
        new_x = max(1, min(new_x, sw - 2))
        new_y = max(1, min(new_y, sh - 2))
        
        # Check if the new position is not occupied by the snake
        if [new_y, new_x] not in snake:
            return [new_y, new_x]

def draw_status():
    status = f"Score: {score} | Level: {snake_level} | EXP: {current_exp}/{exp_to_next_level} | Speed Boosts: {powerups['speed_boost']} | Invincibility: {powerups['invincibility']} | Double Points: {powerups['double_points']}"
    w.addstr(0, 1, status[:sw-2])
    w.addstr(sh-1, 1, "Press 'P' to open store")

def show_store():
    store_text = [
        "Welcome to the Snake Store!",
        f"1. Speed Boost (1 level): {powerups['speed_boost']}",
        f"2. Invincibility (2 levels): {powerups['invincibility']}",
        f"3. Double Points (1 level): {powerups['double_points']}",
        "4. Exit Store",
        "Enter your choice (1-4):"
    ]
    h, w = 8, 40
    y, x = (sh - h) // 2, (sw - w) // 2
    store_win = curses.newwin(h, w, y, x)
    store_win.box()
    for i, text in enumerate(store_text):
        store_win.addstr(i + 1, 1, text)
    store_win.refresh()
    return store_win

def game_over_screen():
    h, w = 6, 40
    y, x = (sh - h) // 2, (sw - w) // 2
    game_over_win = curses.newwin(h, w, y, x)
    game_over_win.box()
    game_over_win.addstr(1, 1, f"Game Over! Score: {score}, Level: {snake_level}")
    game_over_win.addstr(2, 1, "Press 'R' to restart or 'Q' to quit")
    game_over_win.refresh()
    while True:
        key = game_over_win.getch()
        if key in [ord('r'), ord('R')]:
            return True
        elif key in [ord('q'), ord('Q')]:
            return False

def handle_resize(signum, frame):
    global sh, sw, w, game_h, game_w
    curses.endwin()
    screen = curses.initscr()
    sh, sw = screen.getmaxyx()
    w = screen.subwin(sh, sw, 0, 0)
    w.keypad(1)
    w.timeout(100)
    
    game_h, game_w = sh - 2, sw - 2
    
    # Redraw the screen
    w.clear()
    w.refresh()

def draw_snake():
    w.addch(snake[0][0], snake[0][1], SNAKE_HEAD[key])
    for i in range(1, len(snake)):
        if snake[i-1][0] == snake[i][0]:  # horizontal
            w.addch(snake[i][0], snake[i][1], SNAKE_BODY_HORIZONTAL)
        elif snake[i-1][1] == snake[i][1]:  # vertical
            w.addch(snake[i][0], snake[i][1], SNAKE_BODY_VERTICAL)
        else:  # corner
            w.addch(snake[i][0], snake[i][1], SNAKE_BODY_CORNER)

# Snake body parts and food
SNAKE_HEAD = {
    curses.KEY_UP: '^', curses.KEY_DOWN: 'v',
    curses.KEY_LEFT: '<', curses.KEY_RIGHT: '>'
}
SNAKE_BODY_HORIZONTAL = '═'
SNAKE_BODY_VERTICAL = '║'
SNAKE_BODY_CORNER = '╬'
FOOD = '•'

# Define powerup prices
powerup_prices = {"speed_boost": 1, "invincibility": 2, "double_points": 1}

# Initialize the screen and game
init_screen()
initialize_game()

# Main game loop
while True:
    try:
        w.clear()
        w.border(0)
        draw_status()
        w.addch(food[0], food[1], FOOD)
        draw_snake()
        w.refresh()
        
        next_key = w.getch()
        
        if next_key == curses.KEY_RESIZE:
            handle_resize(None, None)
            continue
        
        if next_key == ord('p') or next_key == ord('P'):  # Open store
            store_win = show_store()
            curses.echo()
            choice = store_win.getstr(6, 26, 1).decode('utf-8')
            curses.noecho()
            if choice in '123':
                powerup = list(powerups.keys())[int(choice) - 1]
                if snake_level >= powerup_prices[powerup]:
                    snake_level -= powerup_prices[powerup]
                    powerups[powerup] += 1
            continue

        # Handle snake movement
        if next_key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            # Prevent the snake from reversing direction
            if (key == curses.KEY_DOWN and next_key != curses.KEY_UP) or \
               (key == curses.KEY_UP and next_key != curses.KEY_DOWN) or \
               (key == curses.KEY_LEFT and next_key != curses.KEY_RIGHT) or \
               (key == curses.KEY_RIGHT and next_key != curses.KEY_LEFT):
                key = next_key

        # Determine the new head of the snake
        new_head = [snake[0][0], snake[0][1]]

        if key == curses.KEY_DOWN:
            new_head[0] += 1
        if key == curses.KEY_UP:
            new_head[0] -= 1
        if key == curses.KEY_LEFT:
            new_head[1] -= 1
        if key == curses.KEY_RIGHT:
            new_head[1] += 1

        snake.insert(0, new_head)

        # Check if snake has hit the wall or itself
        if not powerup_active["invincibility"] and (
            snake[0][0] in [0, sh-1] or 
            snake[0][1] in [0, sw-1] or 
            snake[0] in snake[1:]
        ):
            if game_over_screen():
                initialize_game()
                continue
            else:
                break

        # Check if snake has eaten the food
        if snake[0] == food:
            food = generate_food()
            score += 2 if powerup_active["double_points"] else 1
            current_exp += 1
            if current_exp >= exp_to_next_level:
                snake_level += 1
                current_exp = 0
                exp_to_next_level = int(exp_to_next_level * 1.2)  # Increase exp needed for next level
        else:
            tail = snake.pop()

        # Handle powerups
        if powerup_active["speed_boost"]:
            w.timeout(50)  # Faster game speed
        else:
            w.timeout(100)  # Normal game speed

        # Deactivate powerups after some time
        for powerup in powerup_active:
            if powerup_active[powerup]:
                powerup_active[powerup] = False

        # Activate powerups
        if next_key == ord('1') and powerups["speed_boost"] > 0:
            powerup_active["speed_boost"] = True
            powerups["speed_boost"] -= 1
        elif next_key == ord('2') and powerups["invincibility"] > 0:
            powerup_active["invincibility"] = True
            powerups["invincibility"] -= 1
        elif next_key == ord('3') and powerups["double_points"] > 0:
            powerup_active["double_points"] = True
            powerups["double_points"] -= 1

    except curses.error:
        # This can happen if the terminal is resized to a very small size
        # We'll just ignore these errors and continue
        pass

curses.endwin()
print("Thanks for playing Snake!")