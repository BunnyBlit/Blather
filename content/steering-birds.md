Title: Controlling How Flappy Bird Flaps
Date: 2024-01-18   
Category: Tech
Tags: Simulations   
Slug: steering-flappy-bird   
Summary: We [make a bird flap]({filename}/flapping-birds.md), but can we steer that bird towards life?   
Status: draft 

Previously, I built and ran Flappy Bird as a [hybrid dynamic system](https://dl.acm.org/doi/pdf/10.1145/3337722.3337757). However, I haven't done a very good job of controlling when Flappy should flap. I wanna do better.

As most of the articles in this series, I'm leaning extremely heavily on Yegeta Zeleke et al's paper about doing this exact thing, along with a [reference Matlab implementation](https://github.com/HybridSystemsLab/FlappyBirdReachability).

## The current state of things
Currently, when Flappy should flap is hardcoded in a function, which isn't the most extendable method on the planet.


```python
def _jump_check(self, time:float, state:State) -> int:
    #... snipping out a collision check...

    # look at this horrifyingly hardcoded logic: start pressing the jump button
    # between 0.5 and 0.6, and then stop pressing it at and after 0.6. Oof.
    if time >= 0.5 and \
        time < 0.6 and \
        state[3] != 1:
        return 0
    elif time >= 0.6 and \
        state[3] != 0:
        return 0
    else:
        return 1
```

That's not great! It shouldn't come as a huge surprise that this isn't very flexible, and as soon as we got some real-ish levels together for Flappy to flap through, Flappy died instantly.

![A much longer and more drawn out level of flappy bird, where flappy eats shit immediately]({static}/images/flapping_birds_single_flap_gen_level.svg)

Tough break. There must be something we can do that's better than this.

## Input as a Signal

What I really want is how input changes through time. We can think about input as a signal-- it's at 0 when a button is up, and 1 when a button is pressed. Our system can sample this: every so often, we check it. If the signal is different than when we last checked it, then we know a button press has happened and we have to jump.

This adds a new parameter to `State`: a running "counter" for how close we are to the next check.


```python
# State gets a new fifth term that represents time since the last input check as a simple counter-- it'll go up
# every simulation step, and as when it hits a certain check interval, we'll check the input signal and it'll reset
State = namedtuple(
    'State',
    [
        'x_pos',
        'y_pos',
        'y_vel',
        'pressed',
        'input_check' # ✨ New! ✨
    ]
)
# and it's derivative also gets a new term in the same place, for how that "counter"
# changes over time-- it just simple 1:1 change with time, as time passes, our "counter"
# increments
StateDerivative = namedtuple(
    'StateDerivative',
    [
        'delta_x_pos',
        'delta_y_pos',
        'delta_y_vel',
        'delta_pressed',
        'delta_input_check' # ✨ New! ✨
    ]
)
```

Why not just check the input signal at every simulation step? I'll get there, but minor spoilers: eventually we'll want to look at all possible input sequences and search for special ones. This is a very big space and a tricky needle to find. Sampling at a rate slower than our simulation time step is a way to help reduce this space.

It does mean that we're not accounting for frame-perfect inputs from speed runners, which is a bummer.

But, we've unfortunately updated some core data structures to make this whole thing work-- we're gonna have to also update our four hybrid dynamic system functions: `flow`, `flow_check`, `jump` and `jump_check`. Everyone loves a refactor!


```python
# ✨ New! ✨-- we return a tuple of five elements now
def _flow(self, time:float, state:State) -> Tuple[float, float, float, int, float]:
    if state[3] == 0:
        return StateDerivative(
            delta_x_pos=self.pressed_velocity,
            delta_y_pos=state[2],
            delta_y_vel=self.falling_acceleration,
            delta_pressed=0,
            delta_input_check=1 # ✨ New! ✨-- this should just change along with time, nothing special
        )
    elif state[3] == 1: #pressed
        return StateDerivative(
            delta_x_pos=self.pressed_velocity, 
            delta_y_pos=self.pressed_velocity,
            delta_y_vel=0,
            delta_pressed=0,
            delta_input_check=1 # ✨ New! ✨
        )
    else:
        raise RuntimeError(f"Invalid state! {state}, pressed != 0 or 1")

# this is, how you say, some bullshit. Pylance very correctly points out that
# I'm changing the signature of the function here, which is... bad. Don't do this at your day job
# I'm hoping this is a little more legible that rewriting out the FlappyHybridSim class again
FlappyHybridSim._flow = _flow # type: ignore

# test = FlappyHybridSim()
```


```python
# ✨ New! ✨ hey this does something now! 
def _flow_check(self, time:float, state:State) -> int:
    # if we're past time for checking the input signal, we should stop flowing
    # we need to test to see if we need to jump!
    if state[4] >= self.input_check_frequency:
        return 1
    else:
        return 0

# see above
FlappyHybridSim._flow_check = _flow_check # type: ignore
```


```python
# ✨ New! ✨ returning a tuple of five elements now
def _jump(self, time:float, state:State) -> Tuple[float, float, float, int, float]:
    
    # my check functions work slightly differently now, so 
    # I need to check for collisions here
    if self._check_collision(state):
        # ✨ New! ✨ what if we didn't need to run the check_collision function twice?
        # adding an argument to stop early
        self.stop = True

    #✨ New! ✨ sample our input signal
    input_val = self._get_next_input()

    if input_val == 1:
        return State(
            x_pos=state[0],
            y_pos=state[1],
            y_vel=self.pressed_velocity,
            pressed=input_val,
            input_check=state[4]
        )
    else:
        return State(
            x_pos=state[0],
            y_pos=state[1],
            y_vel=state[2],
            pressed=input_val,
            input_check=state[4]
        )

# same deal
FlappyHybridSim._jump = _jump # type: ignore
```


```python
# ✨ New! ✨ collision handling is now in jump
#  so all this has to do is see if its time to check input
def _jump_check(self, time:float, state:State) -> int:
    # rather than hardcoding when to jump, we check the counter!
    if state[4] >= self.input_check_frequency:
        return 0
    else:
        return 1 
_jump_check.terminal = True

# same deal
FlappyHybridSim._jump_check = _jump_check # type: ignore
```

I've made a subtle change in what it means to be flowing or jumping in the hybrid system-- did you catch it?

Before, we only ever jumped if we were going to go to a new state, but here, we can jump back to the same state. A jump, in this formalization, is synonymous with testing the input signal. This version regularly jumps at the input sample rate, and sometimes just jumps back to the same state it was just in [^1].

That can be a little hard to wrap your head around, let's use some graphs.

[^1]: I'll cover optimization later, but at least at first brush, this _feels_ like a step backwards. This new version interrupts the solver regularly, and sometimes just goes back to what it was just doing. That's a bummer!



```python
# TODO: write some graphs in dot here, and if I hate those, switch over to draw.io to Do The Thing.
# ultimately, there's gonna be some SVGs.
```

Ok!

But, sadly, the refactoring is not done yet. I snuck a new `FlappyHybridSim` attribute in there (`input_check_frequency`), and a new method (`_get_next_input(...)`)-- so whole class doesn't, ya know, work. Let's finish this refactor-- `_get_next_input(...)` should get the next sample of an input signal, which the sim class wants to hold onto.

This probably wants to be a parameter of `FlappyHybridSim.solve_system`, just like the `start_state` and `params` are. As I spoiled above, where this is all building up to is the ability to search for specific input signals given a certain Flappy Bird level. I want to test a fixed level against many input signals, so this becomes a parameter of our `solve_system` function.


```python
# TODO look into generating descriptors or modifying descriptor classes as a way to modify how the class behaves at runtime?
#       I could add another bit of blog magic?
#       really, I'm just trying to set it up such that pylance won't yell at me
```


```python

```
