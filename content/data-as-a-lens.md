Title: Lenses, not Fences: Computer Memory Edition
Date: 2023-03-17
Category: Tech
Tags: Simulations, Python, Data Structures
Slug: data-as-a-lens
Summary: Organizing data to make it easy to remember

([With some apologies to Stacey Mason](https://cerebralarcade.com/2015/08/29/lenses-not-boxes/))

[Previously]({filename}/bouncing-balls.md), I wrote a lot about [Hybrid Dynamic Systems]({https://dl.acm.org/doi/pdf/10.1145/3337722.3337757}) and simulating a simple bouncing ball. I started with grand ambitions: a nice set of data classes that mapped out properties with sensible, readable names. And then ~~fire nation attacked~~ I had to make my dreams work in the real world, and they died.

To writ-- I started with this nice `dataclass` to track the state of a bouncing ball:
```python
@dataclass
class State:
    y_pos: float # vertical position
    y_vel: float # vertical velocity
```

which eventually became nothing more than a `tuple()` to work with `scipy`'s `integrate.solve_ivp` method. This was rough, because now instead of doing something nice like `state.y_pos`, I needed to remember that `state[0]` was the vertical position.

Boo.

I want nice abstractions. I want the code to be readable by people, not computers. I want you, dear reader, do need to hold as little information about the system in your head at a time.

Can we do better? And along the way, can we go from Python-ish near code to something that runs and we're happy to maintain?

### Lenses, not Fences

Data structures is very little more than the art of applying some labels to memory. Label some memory the right way, and then you can quickly access elements of that memory [without needing to search around for what you want](https://en.wikipedia.org/wiki/Hash_table). We want to label things that make it easy for the computer: this speeds up our programs.

But, also, we want to label stuff so its easy for the person working with the computer. Most of the time, its better for the labels to be decipherable than the program fast. Setting up the article like this, its easy to make it sound like, "oh, well, you need to sacrifice speed for readability!"

[The rustaceans teach us: you (mostly) do not](https://doc.rust-lang.org/beta/embedded-book/static-guarantees/zero-cost-abstractions.html). The dichotomy is false. We can have our cake and eat it too. People work very hard to compile our code to be fast for the computer, so we can write it for our fellow people. When we hit something annoying like needing to remember the order of arguments in a `tuple`, it's time to grab a new lens and look at the world a little differently.

Let's step into the sun.

### Transformation Functions

I want to focus on how state is going to be used. When we last looked at this system, the state of the ball was a `tuple`. Let's pull it back to being a `State` dataclass, and look at where we touch it:

```python
# when we last looked at these functions, I had converted
# state to a tuple. Let's pull back to having them be a class again.

def jump(time:float, state:State) -> State:
    state.y_vel = -0.5 * state.y_vel
    # ~~~~~~~~~           ~~~~~~~~~~
    return state

def jump_check(time:float, state:State) -> int:
    if state.y_pos <= 0 and state.y_vel < 0:
    #  ~~~~~~~~~~~          ~~~~~~~~~~~
        return 0
    else:
        return 1

def flow(time:float, state:State) -> tuple:
    return tuple([state.y_vel, -9.81])
    #             ~~~~~~~~~~~~

# ... within our solving near code
while solving_model:
    # ...
    ode_sol = integrate.solve_ivp(
        flow, # a Callable
        (cur_time, end_time), # tuple
        cur_state, # State as an "array_like"
        #~~~~~~~~~
        events=[jump_check] # list of callable
        # ... 
    )
    if ode_sol.status == -1:
        print(f"Solver failed with message: {ode_sol.message}")
        return solution
    for time, state_from_solver in zip(ode_sol.t, ode_sol.y.T):
        solution.append((time, State(*state_from_solver)))
        #                      ~~~~~~~~~~~~~~~~~~~~~~~~
    # ...
```

Most of the time, the `dataclass` works fine! It's just that one annoying spot as part of `scipy`. What if we just write a function that transforms our class to a list just for this one method, and then the rest of the time, it can be a class.

```python
@dataclass
class State:
    y_pos: float
    y_vel: float 

    def to_list(self):
        return [self.y_pos, self.x_pos]
```

And then to use it:
```python
while ...:
    # everything else around it is the same
    ode_sol = integrate.solve_ivp(
        flow,
        (cur_time, end_time),
        # ✨ new ✨
        cur_state.to_list(),
        events=[jump_check]
    )
```

And then everyone's happy. Wrap up the blog post, lets go home.

Well,

It's a bit of a bummer that we need to make an entire new `list` every time we call the solver to solve for another chunk of flow. We call `solve_ivp` _a lot_. What we really want is a *lens*: sometimes we view the data like properties of a class, other times we view the data like a list.

### Protocols

In Python, the way we look at data is mostly just trying to do stuff to it-- if we access it like `data[0]`, and nothing crashes, well then, it must be a thing that supports access by a key (the key is the number 0). [Duck typing](https://en.wikipedia.org/wiki/Duck_typing) is kinda a chaotic gremlin-- you just gotta try and see what happens.

It's also a little rough for our tools: my IDE can't check me if it also doesn't know if something will succeed or fail until we do it.

[Protocols](https://peps.python.org/pep-0544/) are a way to announce, beforehand, that you support certain ways of being interacted with. If we want our `State` class to announce, "hey, I can be interacted with like a list-ish thing called a [Sequence](https://docs.python.org/3/glossary.html#term-sequence)", we extend the [Sequence abstract class](https://docs.python.org/3/library/collections.abc.html#collections.abc.Sequence) and promise that this means we'll behave and follow the `Sequence` protocol. If we look at which methods aren't implemented for us when we inherent from `Sequence`, we can see what the protocol asks us to implement: `__len__` and `__getitem__`.

Well, let's do it!
```python
from collections.abc import Sequence

@dataclass
class State(Sequence):
    #     ✨ ☝️ new ✨
    y_pos: float
    y_vel: float

    # time for the new functions we need to implement!
    def __len__(self) -> int:
        # we need to return the size of our sequence, which will always have two elements
        # why are you booing, I'm right!
        return 2
    
    def __getitem__(self, key:int) -> float:
        # and we can just treat the "indexes" that'll get used to access the sequence as a pattern to match and return the right attribute
        # Python doesn't have match syntax, so we if... else it
        if key == 0:
            return self.y_pos
        elif key == 1:
            return self.y_vel
        else:
            raise IndexError()
```

This... works! We no longer need to create a `list` to make our `State` class work. But, it has bad vibes. In particular, this pattern is very brittle: when we move away from this ball and onto something else, this will stop working: we need to redefine `__len__` and  `__getitem__`. Adding a new property-- dynamic `y_acceleration` maybe?-- requires us to change the implementation of the `__len__` and `__getitem__`.

There must be another way.

### Moving up the Abstraction Chain

