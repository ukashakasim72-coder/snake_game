"""
Professional Snake Game Architecture
Built with Python Turtle, Standard Libraries, and Object-Oriented Design.
"""

from dataclasses import dataclass
from enum import Enum, auto
import os
import random
import turtle
from typing import List, Tuple, Optional


# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================

@dataclass(frozen=True)
class Config:
    SCREEN_WIDTH: int = 600
    SCREEN_HEIGHT: int = 600
    GRID_SIZE: int = 20
    BORDER_LIMIT: int = 280  # Playable boundary extent
    INITIAL_SPEED: float = 0.10
    SPEED_ACCELERATION: float = 0.002
    MIN_SPEED: float = 0.03
    DATA_FILE: str = "high_score.txt"
    FONT_FAMILY: str = "Courier"

    # Color Palette (Modern Dark Theme)
    COLOR_BG: str = "#0F172A"       # Slate 900
    COLOR_BORDER: str = "#334155"   # Slate 700
    COLOR_SNAKE_HEAD: str = "#10B981"# Emerald 500
    COLOR_SNAKE_BODY: str = "#34D399"# Emerald 400
    COLOR_FOOD: str = "#F59E0B"      # Amber 500
    COLOR_TEXT: str = "#F8FAFC"      # Slate 50
    COLOR_OVERLAY: str = "#EF4444"   # Red 500


class Direction(Enum):
    UP = 90
    DOWN = 270
    LEFT = 180
    RIGHT = 0


class GameState(Enum):
    START = auto()
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


# ==========================================
# GAME COMPONENTS
# ==========================================

class Snake:
    """Manages snake body segments, movement, and direction queuing."""

    def __init__(self) -> None:
        self.segments: List[turtle.Turtle] = []
        self.direction_queue: List[Direction] = []
        self.current_direction: Direction = Direction.RIGHT
        self.create_snake()
        self.head: turtle.Turtle = self.segments[0]

    def create_snake(self) -> None:
        """Initializes a 3-segment snake centered horizontally."""
        starting_positions = [(0, 0), (-Config.GRID_SIZE, 0), (-Config.GRID_SIZE * 2, 0)]
        for index, position in enumerate(starting_positions):
            self._add_segment(position, is_head=(index == 0))

    def _add_segment(self, position: Tuple[float, float], is_head: bool = False) -> None:
        segment = turtle.Turtle("square")
        segment.penup()
        segment.speed("fastest")
        segment.color(Config.COLOR_SNAKE_HEAD if is_head else Config.COLOR_SNAKE_BODY)
        segment.goto(position)
        self.segments.append(segment)

    def extend(self) -> None:
        """Appends a new segment to the tail position."""
        self._add_segment(self.segments[-1].position())

    def move(self) -> None:
        """Updates segment positions and applies queued direction changes."""
        # Process input queue (prevents instant 180-degree self-collision)
        if self.direction_queue:
            next_direction = self.direction_queue.pop(0)
            if not self._is_opposite(next_direction, self.current_direction):
                self.current_direction = next_direction
                self.head.setheading(self.current_direction.value)

        # Move segments from tail to head
        for i in range(len(self.segments) - 1, 0, -1):
            new_x = self.segments[i - 1].xcor()
            new_y = self.segments[i - 1].ycor()
            self.segments[i].goto(new_x, new_y)

        self.head.forward(Config.GRID_SIZE)

    def queue_direction(self, new_dir: Direction) -> None:
        """Queues a direction change if valid."""
        last_dir = self.direction_queue[-1] if self.direction_queue else self.current_direction
        if not self._is_opposite(new_dir, last_dir):
            self.direction_queue.append(new_dir)

    @staticmethod
    def _is_opposite(dir1: Direction, dir2: Direction) -> bool:
        return abs(dir1.value - dir2.value) == 180

    def reset(self) -> None:
        """Clears existing segments off-screen and recreates snake."""
        for seg in self.segments:
            seg.goto(1000, 1000)
            seg.hideturtle()
        self.segments.clear()
        self.direction_queue.clear()
        self.current_direction = Direction.RIGHT
        self.create_snake()
        self.head = self.segments[0]


class Food(turtle.Turtle):
    """Manages food placement snapped strictly to the grid."""

    def __init__(self) -> None:
        super().__init__()
        self.shape("circle")
        self.penup()
        self.shapesize(stretch_len=0.7, stretch_wid=0.7)  # Slightly smaller than grid block
        self.color(Config.COLOR_FOOD)
        self.speed("fastest")

    def refresh(self, occupied_positions: List[Tuple[float, float]]) -> None:
        """Spawns food at a random grid coordinate not occupied by the snake."""
        grid_bounds = Config.BORDER_LIMIT // Config.GRID_SIZE
        while True:
            rand_x = random.randint(-grid_bounds + 1, grid_bounds - 1) * Config.GRID_SIZE
            rand_y = random.randint(-grid_bounds + 1, grid_bounds - 1) * Config.GRID_SIZE

            # Check if any occupied position is too close (distance < 10)
            collision = False
            for pos in occupied_positions:
                dx = rand_x - pos[0]
                dy = rand_y - pos[1]
                if (dx * dx + dy * dy) < 100:   # squared distance < 100 => distance < 10
                    collision = True
                    break

            if not collision:
                self.goto(rand_x, rand_y)
                break


class Scoreboard(turtle.Turtle):
    """Handles HUD rendering, persistent high score I/O, and UI overlays."""

    def __init__(self) -> None:
        super().__init__()
        self.score: int = 0
        self.high_score: int = self._load_high_score()
        self.penup()
        self.hideturtle()
        self.color(Config.COLOR_TEXT)
        self.goto(0, Config.BORDER_LIMIT + 5)
        self.update_score()

    def _load_high_score(self) -> int:
        if os.path.exists(Config.DATA_FILE):
            try:
                with open(Config.DATA_FILE, "r") as file:
                    return int(file.read().strip())
            except (ValueError, IOError):
                return 0
        return 0

    def save_high_score(self) -> None:
        try:
            with open(Config.DATA_FILE, "w") as file:
                file.write(str(self.high_score))
        except IOError as e:
            print(f"Error saving high score: {e}")

    def update_score(self) -> None:
        self.clear()
        self.goto(0, Config.BORDER_LIMIT + 5)
        self.color(Config.COLOR_TEXT)
        self.write(
            f"SCORE: {self.score}   HIGH SCORE: {self.high_score}",
            align="center",
            font=(Config.FONT_FAMILY, 14, "bold")
        )

    def increment_score(self) -> None:
        self.score += 1
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        self.update_score()

    def reset_score(self) -> None:
        self.score = 0
        self.update_score()

    def show_start_screen(self) -> None:
        self.goto(0, 0)
        self.color(Config.COLOR_TEXT)
        self.write(
            "S N A K E\n\nPress [SPACE] to Play\nPress [P] to Pause",
            align="center",
            font=(Config.FONT_FAMILY, 18, "bold")
        )

    def show_pause_screen(self) -> None:
        self.goto(0, 0)
        self.color(Config.COLOR_FOOD)
        self.write(
            "PAUSED\n\nPress [P] or [SPACE] to Resume",
            align="center",
            font=(Config.FONT_FAMILY, 18, "bold")
        )

    def show_game_over_screen(self) -> None:
        self.goto(0, 20)
        self.color(Config.COLOR_OVERLAY)
        self.write(
            "GAME OVER",
            align="center",
            font=(Config.FONT_FAMILY, 24, "bold")
        )
        self.goto(0, -30)
        self.color(Config.COLOR_TEXT)
        self.write(
            "Press [SPACE] to Restart",
            align="center",
            font=(Config.FONT_FAMILY, 14, "normal")
        )


# ==========================================
# GAME ENGINE
# ==========================================

class SnakeGameEngine:
    """Main Orchestrator for window, input events, and game loop execution."""

    def __init__(self) -> None:
        self.screen = turtle.Screen()
        self._setup_window()
        self._draw_boundary()

        self.snake = Snake()
        self.food = Food()
        self.scoreboard = Scoreboard()

        self.state = GameState.START
        self.game_speed = Config.INITIAL_SPEED

        self._bind_inputs()
        self.food.refresh([seg.position() for seg in self.snake.segments])
        self.scoreboard.show_start_screen()

    def _setup_window(self) -> None:
        self.screen.setup(Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT)
        self.screen.bgcolor(Config.COLOR_BG)
        self.screen.title("Python Snake - Professional Architecture")
        self.screen.tracer(0)  # Disable auto-animation for custom loop rendering

    def _draw_boundary(self) -> None:
        """Draws a visual border line defining active play field."""
        border = turtle.Turtle()
        border.hideturtle()
        border.penup()
        border.color(Config.COLOR_BORDER)
        border.pensize(3)
        limit = Config.BORDER_LIMIT + 10
        border.goto(-limit, limit)
        border.pendown()
        for _ in range(4):
            border.forward(limit * 2)
            border.right(90)

    def _bind_inputs(self) -> None:
        self.screen.listen()
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.UP), "Up")
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.DOWN), "Down")
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.LEFT), "Left")
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.RIGHT), "Right")

        # Secondary WASD controls
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.UP), "w")
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.DOWN), "s")
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.LEFT), "a")
        self.screen.onkey(lambda: self.snake.queue_direction(Direction.RIGHT), "d")

        # Action Keys
        self.screen.onkey(self._handle_spacebar, "space")
        self.screen.onkey(self._toggle_pause, "p")

    def _handle_spacebar(self) -> None:
        if self.state in (GameState.START, GameState.GAME_OVER):
            self.restart_game()
        elif self.state == GameState.PAUSED:
            self.state = GameState.RUNNING
            self.scoreboard.update_score()

    def _toggle_pause(self) -> None:
        if self.state == GameState.RUNNING:
            self.state = GameState.PAUSED
            self.scoreboard.show_pause_screen()
        elif self.state == GameState.PAUSED:
            self.state = GameState.RUNNING
            self.scoreboard.update_score()

    def restart_game(self) -> None:
        """Resets instances cleanly without altering screen setup."""
        self.snake.reset()
        self.scoreboard.reset_score()
        self.food.refresh([seg.position() for seg in self.snake.segments])
        self.game_speed = Config.INITIAL_SPEED
        self.state = GameState.RUNNING

    def game_loop(self) -> None:
        """Event-driven game tick loop via Turtle's ontimer."""
        if self.state == GameState.RUNNING:
            self._game_tick()

        self.screen.update()
        delay_ms = int(self.game_speed * 1000)
        self.screen.ontimer(self.game_loop, delay_ms)

    def run(self) -> None:
        """Starts the event loop and enters the Tkinter main loop."""
        self.game_loop()
        self.screen.mainloop()

    def _game_tick(self) -> None:
        self.snake.move()

        # 1. Food Collision
        if self.snake.head.distance(self.food) < 15:
            self.food.refresh([seg.position() for seg in self.snake.segments])
            self.snake.extend()
            self.scoreboard.increment_score()
            # Slightly increase speed on food eaten
            self.game_speed = max(Config.MIN_SPEED, self.game_speed - Config.SPEED_ACCELERATION)

        # 2. Wall Collision
        x, y = self.snake.head.xcor(), self.snake.head.ycor()
        if abs(x) > Config.BORDER_LIMIT or abs(y) > Config.BORDER_LIMIT:
            self._trigger_game_over()

        # 3. Tail Collision
        for segment in self.snake.segments[1:]:
            if self.snake.head.distance(segment) < 10:
                self._trigger_game_over()
                break

    def _trigger_game_over(self) -> None:
        self.state = GameState.GAME_OVER
        self.scoreboard.show_game_over_screen()



if __name__ == "__main__":
    engine = SnakeGameEngine()
    engine.run()