package main

import (
	"fmt"
	"math"
	"math/rand"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nsf/termbox-go"
)

const (
	SnakeHeadUp    = '^'
	SnakeHeadDown  = 'v'
	SnakeHeadLeft  = '<'
	SnakeHeadRight = '>'
	SnakeBody      = '■'
	Food           = '•'
)

type Point struct {
	y, x int
}

type Game struct {
	snake         []Point
	food          Point
	direction     termbox.Key
	score         int
	snakeLevel    int
	expToNextLevel int
	currentExp    int
	powerups      map[string]int
	powerupActive map[string]bool
	width, height int
}

func main() {
	err := termbox.Init()
	if err != nil {
		panic(err)
	}
	defer termbox.Close()

	game := initializeGame()

	// Handle terminal resize
	sigwinch := make(chan os.Signal, 1)
	signal.Notify(sigwinch, syscall.SIGWINCH)

	go func() {
		for range sigwinch {
			termbox.Sync()
			w, h := termbox.Size()
			game.width, game.height = w, h
		}
	}()

	eventQueue := make(chan termbox.Event)
	go func() {
		for {
			eventQueue <- termbox.PollEvent()
		}
	}()

	ticker := time.NewTicker(100 * time.Millisecond)

	for {
		select {
		case ev := <-eventQueue:
			if ev.Type == termbox.EventKey {
				switch ev.Key {
				case termbox.KeyArrowUp, termbox.KeyArrowDown, termbox.KeyArrowLeft, termbox.KeyArrowRight:
					game.handleDirection(ev.Key)
				case termbox.KeyEsc:
					return
				default:
					game.handlePowerups(ev.Ch)
				}
			}
		case <-ticker.C:
			if game.update() {
				game.draw()
			} else {
				if game.gameOver() {
					return
				}
				game = initializeGame()
			}
		}
	}
}

func initializeGame() *Game {
	w, h := termbox.Size()
	snake := []Point{
		{y: h / 2, x: w / 4},
		{y: h / 2, x: w/4 - 1},
		{y: h / 2, x: w/4 - 2},
	}

	game := &Game{
		snake:         snake,
		direction:     termbox.KeyArrowRight,
		score:         0,
		snakeLevel:    1,
		expToNextLevel: 5,
		currentExp:    0,
		powerups:      map[string]int{"speed_boost": 0, "invincibility": 0, "double_points": 0},
		powerupActive: map[string]bool{"speed_boost": false, "invincibility": false, "double_points": false},
		width:         w,
		height:        h,
	}

	game.generateFood()
	return game
}

func (g *Game) generateFood() {
	maxDistance := int(math.Min(float64(10+g.snakeLevel), float64(min(g.height, g.width)/2)))

	for {
		angle := rand.Float64() * 2 * math.Pi
		distance := rand.Intn(maxDistance-5+1) + 5

		newX := int(float64(g.snake[0].x) + float64(distance)*math.Cos(angle))
		newY := int(float64(g.snake[0].y) + float64(distance)*math.Sin(angle))

		newX = max(1, min(newX, g.width-2))
		newY = max(1, min(newY, g.height-2))

		if !g.isSnakeCell(Point{y: newY, x: newX}) {
			g.food = Point{y: newY, x: newX}
			return
		}
	}
}

func (g *Game) isSnakeCell(p Point) bool {
	for _, s := range g.snake {
		if s == p {
			return true
		}
	}
	return false
}

func (g *Game) handleDirection(key termbox.Key) {
	switch {
	case key == termbox.KeyArrowUp && g.direction != termbox.KeyArrowDown:
		g.direction = key
	case key == termbox.KeyArrowDown && g.direction != termbox.KeyArrowUp:
		g.direction = key
	case key == termbox.KeyArrowLeft && g.direction != termbox.KeyArrowRight:
		g.direction = key
	case key == termbox.KeyArrowRight && g.direction != termbox.KeyArrowLeft:
		g.direction = key
	}
}

func (g *Game) handlePowerups(key rune) {
	switch key {
	case '1':
		if g.powerups["speed_boost"] > 0 {
			g.powerupActive["speed_boost"] = true
			g.powerups["speed_boost"]--
		}
	case '2':
		if g.powerups["invincibility"] > 0 {
			g.powerupActive["invincibility"] = true
			g.powerups["invincibility"]--
		}
	case '3':
		if g.powerups["double_points"] > 0 {
			g.powerupActive["double_points"] = true
			g.powerups["double_points"]--
		}
	}
}

func (g *Game) update() bool {
	newHead := g.snake[0]
	switch g.direction {
	case termbox.KeyArrowUp:
		newHead.y--
	case termbox.KeyArrowDown:
		newHead.y++
	case termbox.KeyArrowLeft:
		newHead.x--
	case termbox.KeyArrowRight:
		newHead.x++
	}

	if !g.powerupActive["invincibility"] &&
		(newHead.x <= 0 || newHead.x >= g.width-1 || newHead.y <= 0 || newHead.y >= g.height-1 || g.isSnakeCell(newHead)) {
		return false
	}

	g.snake = append([]Point{newHead}, g.snake...)

	if newHead == g.food {
		g.score += 2
		if g.powerupActive["double_points"] {
			g.score++
		}
		g.currentExp++
		if g.currentExp >= g.expToNextLevel {
			g.snakeLevel++
			g.currentExp = 0
			g.expToNextLevel = int(float64(g.expToNextLevel) * 1.2)
		}
		g.generateFood()
	} else {
		g.snake = g.snake[:len(g.snake)-1]
	}

	for powerup := range g.powerupActive {
		g.powerupActive[powerup] = false
	}

	return true
}

func (g *Game) draw() {
	termbox.Clear(termbox.ColorDefault, termbox.ColorDefault)

	// Draw border
	for i := 0; i < g.width; i++ {
		termbox.SetCell(i, 0, '─', termbox.ColorWhite, termbox.ColorDefault)
		termbox.SetCell(i, g.height-1, '─', termbox.ColorWhite, termbox.ColorDefault)
	}
	for i := 0; i < g.height; i++ {
		termbox.SetCell(0, i, '│', termbox.ColorWhite, termbox.ColorDefault)
		termbox.SetCell(g.width-1, i, '│', termbox.ColorWhite, termbox.ColorDefault)
	}

	// Draw snake
	for i, p := range g.snake {
		var ch rune
		if i == 0 {
			switch g.direction {
			case termbox.KeyArrowUp:
				ch = SnakeHeadUp
			case termbox.KeyArrowDown:
				ch = SnakeHeadDown
			case termbox.KeyArrowLeft:
				ch = SnakeHeadLeft
			case termbox.KeyArrowRight:
				ch = SnakeHeadRight
			}
		} else {
			ch = SnakeBody
		}
		termbox.SetCell(p.x, p.y, ch, termbox.ColorGreen, termbox.ColorDefault)
	}

	// Draw food
	termbox.SetCell(g.food.x, g.food.y, Food, termbox.ColorRed, termbox.ColorDefault)

	// Draw status
	status := fmt.Sprintf("Score: %d | Level: %d | EXP: %d/%d | Speed Boosts: %d | Invincibility: %d | Double Points: %d",
		g.score, g.snakeLevel, g.currentExp, g.expToNextLevel,
		g.powerups["speed_boost"], g.powerups["invincibility"], g.powerups["double_points"])
	drawString(1, 0, status)

	termbox.Flush()
}

func (g *Game) gameOver() bool {
	termbox.Clear(termbox.ColorDefault, termbox.ColorDefault)
	gameOverMsg := fmt.Sprintf("Game Over! Score: %d, Level: %d", g.score, g.snakeLevel)
	drawString(g.width/2-len(gameOverMsg)/2, g.height/2-1, gameOverMsg)
	drawString(g.width/2-11, g.height/2+1, "Press 'r' to restart or 'q' to quit")
	termbox.Flush()

	for {
		ev := termbox.PollEvent()
		if ev.Type == termbox.EventKey {
			if ev.Ch == 'r' {
				return false
			} else if ev.Ch == 'q' {
				return true
			}
		}
	}
}

func drawString(x, y int, s string) {
	for i, ch := range s {
		termbox.SetCell(x+i, y, ch, termbox.ColorWhite, termbox.ColorDefault)
	}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}