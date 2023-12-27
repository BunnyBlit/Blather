Title: What Makes The Flappy Bird Flap?
Date: 2023-03-17
Category: Tech
Tags: Simulations, Python
Slug: modeling-flappy-bird
Summary: If we can model a [bouncing ball]({filename}/bouncing-balls.md), what about a flapping bird?
Status: draft

[Previously]({filename}/bouncing-balls.md), I wrote a lot about [Hybrid Dynamic Systems]({https://dl.acm.org/doi/pdf/10.1145/3337722.3337757}) and simulating a simple bouncing ball.

I wrote a bunch of something adjacent to Python code about it. What about a real video game? Can we use this framework to simulate a video game?

### The Model of Flappy Bird
Ok, I need four functions:  

* ```flow(...)``` tells me how the game changes over time, by taking in the current time and the state, and giving me the derivative of the state with respect to time  

* ```jump(...)``` tells me how the game changes instantly, snapping from one state to another. It takes in a time and a state and returns a different state.  

* ```flow_check(...)``` tells me if the game should be flowing or not. It takes in a time and a state and returns an integer (0 for not flowing, 1 for flowing). It's gotta be an int to work with other libraries to use this model.  

* ```jump_check(...)``` tells me if the game should jump or not. It takes in a time and a state and returns an integer (0 for do not jump, 1 for jump). It's gotta be an int for the same reasons ```flow_check``` does.  

All these functions deal with state... so what state does flappy bird need? Well, we'll need both vertical and horizontal position because those will change. We'll need vertical velocity because the bird both rises (on flap) and falls. Oh! And something to track if the player is pushing the flap button or not.

```python
@dataclass
class FlappyState():
    """ State of Flappy the bird! Changes over solve time.
    Args:
        x_pos (float): x position
        y_pos (float): y position
        y_vel (float): y velocity.
                       x_vel is constant and doesn't need to be part of state.
        pressed (int): if the button is pressed or not
    """
    x_pos: float
    y_pos: float
    y_vel: float
    pressed: int
```

Rad.

Well, wait. I'm forgetting something: I'll eventually need to pass this state to an ODE Solver, and it needs state as an `array_like`. This is not an `array_like`.

What if we just write down how to turn this into an array?

```python 
@dataclass
class FlappyState():
    # SNIP its the same as above

    def to_list(self) -> List:
        """Convert state to a list for use with the solver.
           The order is [x_pos, y_pos, y_vel, pressed]
        """
        return [self.x_pos, self.y_pos, self.y_vel, self.pressed]
```

This isn't perfect-- ideally, I'd want two "views" on state: the "list" view, for when it needs to act like an array-like, and the "class" view, for when I want to access properties by nice, human readable names[^1]. This could probably be handled by using [properties](https://docs.python.org/3/library/functions.html?highlight=property#property), along with having our state class follow the [sequence protocol](https://docs.python.org/3/glossary.html#term-sequence).

Well

Let's just do that

```python
```


[^1]: In my C days, I'd do some dangerous casting to get this effect. I'm not really sure how to do this in Python.