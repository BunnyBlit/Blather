Title: Taking the Guesswork out of Bouncing Balls
Date: 2023-02-10
Category: Tech
Tags: Simulations, Python
Slug: guesswork-bouncing-balls
Summary: A complicated way to explain game mechanics to a computer
Status: draft

Games are complicated.

They have a lot of stuff you can do! You can [click on things](http://orteil.dashnet.org/cookieclicker/), [crash space ships](https://www.kerbalspaceprogram.com/), [play pinball](https://blogs.windows.com/windowsexperience/2015/10/09/pinball-fx2-windows-10-edition-is-now-available/) or even [bounce a ball back and forth](https://www.ponggame.org/).

Rarely-- and it is a cursed moment when it happens-- I'm called on to design some part of a game. This is really hard because [game design is extremely difficult](https://www.gamedeveloper.com/design/-quot-the-door-problem-quot-of-game-design). But, also, because I am bad at video games. I tune everything to be way too easy, because _I_ have to be the first play tester, and I tend to tune stuff that _I_ find fun.

I was in the middle of one of these struggles when I saw a presentation of Yegeta Zeleke's paper on [analyzing and modeling action games](https://dl.acm.org/doi/pdf/10.1145/3337722.3337757). I didn't really understand the presentation at the time, but I couldn't stop thinking about it. Fast forward years later, and here we are.

I want to be clear: game mechanics modeling and simulation _does not_ replace good design. When the models are good, they can work as a lens to help shine light on certain corner cases. They will not make something good for you. Programs are focused and narrow tools: do not make the [tech bro mistake](https://nypost.com/2022/06/24/suspended-google-engineer-claims-sentient-ai-bot-has-hired-a-lawyer/) and think they are anything more than that.

### So, Let's Dive In

The paper is a case study in applying a math thing called a Hybrid Dynamical System to [Flappy Bird](https://kotaku.com/the-flappy-bird-fiasco-1519938266). What's a Hybrid Dynamical System?

I'm a "learn by doing" kind of person; I wanted to try and implement one to find out. I tend to start with Python and move to lower level languages later. I'm comfortable in Python and most of the time, this means my bugs are logic bugs and not implementation bugs.

The core concept here is that we can break a system (read as: game) into two parts:  

1. **The continuous part**: this part is things like jump arcs, car drifting, and starship thrust. These parts of the game change continuously while they're happening, and are often handled by a physics engine. When a game is operating this way, it's _flowing_, and these changes are called _flows_.  

2. **The discrete part**: this part is sudden, sharp changes in a game, switching from one mode to another. Characters are very often modeled as a collection of sharp switches-- you're not punching, you hit the punch button, and then suddenly you are! When a game is operating this way, it's _jumping_, and these changes are called _jumps_.

It's then just a uh, simple, question of modeling all the flows, modeling all the jumps, and then some logic to say when to jump and which flow to be in.

### Let's start with something more simple than Pong

The proverbial first example with Hybrid Dynamic Systems is a bouncing ball. To start, I need the ball's state, which changes over time. To keep this very simple, I won't even model horizontal position (left / right): let's only care about vertical position (up / down). And, since I want to change vertical position over time, vertical velocity[^1].

[^1]: using `y` as my vertical axis, rather than `z`. This is [A Thing](https://forums.autodesk.com/t5/fusion-360-manufacture/why-is-y-up-instead-of-z-by-default/td-p/7226258), and something I didn't think to hard about-- I can always refactor this to `z` later. If you're much happier with `y` as your depth axis, go for it.

```python
from dataclasses import dataclass
@dataclass
class State:
    y_pos: float # vertical position
    y_vel: float # vertical velocity
```

So, when does a bouncing ball jump? It starts by falling-- seems pretty continuous-- then hits the ground, then suddenly springs back up. That contact with the ground is a jump, a sudden switch in state. The ball's velocity was going down, now in a instant, it's going up!

What might that look like in code? Lets also throw in a constant [restitution coefficient](https://en.wikipedia.org/wiki/Coefficient_of_restitution), so we can lose some energy as we bounce to make it feel a little more real. 
```python
def jump(state:State) -> State:
    # reduce the velocity by multiplying it by a less-than-one restitution coefficient
    # flip the direction by also multiplying by a negative one.
    # the restitution coefficient is 0.5 here
    state.y_vel = -0.5 * state.y_vel
    # return!
    return state
```

"Woah, slow down there cowboy," you say, in my head. "How does the computer know when to trigger a jump?"

Ah! Right. If we flip the velocity before we hit the ground, we'll just go more up. That's not how gravity works. The gamers would be very mad at our lack of attention to realism in Ball Sim 2023[^2]. Well, we can just use another function to tell us if we should jump or not, call it uh, 

[^2]: Gonna need to workshop this title 
```python
def jump_check(state:State) -> bool:
    if state.y_pos <= 0 and state.y_vel < 0:
        # collision detection? What's that? Everyone knows the ground is at position 0 :)
        # hills, like birds, are not real
        # anyway, we be jumpin if we hit the ground and we still have negative velocity (so we'd go more into the ground.
        return True
    else:
        # otherwise keep flowing
        return False
```
That covers jumps-- there's a function, `jump` to say "this is how we do the instantaneous state change" and another function `jump_check` that says "it's time to jump". Flows are similar! There's a function to run to say how we're flowing (`flow`), and a function to say if we should be flowing or not (`flow_check`). The... well, the check function gets a little silly with our ball example:
```python
def flow_check(state: State) -> bool:
    return True
```
I know. This feels like I'm pranking you. I'm not trying to. Sometimes, its just like this. Our system is so simple that it's _always_ flowing. Sure, it jumps sometimes, but that happens in a single instant, and gravity never stops, so. There are times in video games when we want to stop applying constant forces ([coyote time](https://gamerant.com/celeste-coyote-time-mechanic-platforming-impact-hidden-mechanics/)), so this is less silly later. 

Now, to actually calculate flows... well, we're not gonna do it by hand. Remember that a flows are an ever changing, ever evolving thing over time, and math has a tool for that: a derivative. Our flow needs to be a function that takes in our state and returns that state's derivative with respect to time.

Ok, so, the derivative of position is the velocity, right? Velocity describes how position changes over time. The derivative of velocity is acceleration... which we'll pretend is a [negative constant](https://en.wikipedia.org/wiki/Gravitational_acceleration) thanks to gravity of 9.81.

```python
from dataclasses import dataclass
@dataclass
class Derivative:
    derivative_position: float
    derivative_velocity: float
 
def flow(state:State) -> Derivative:
    return Derivative(
        derivative_position=state.y_vel,
        derivative_velocity=-9.81
    )


```

So we have a little system! Four equations that all have the following calling signatures:
```python
def flow(state: State) -> Derivative: #...
def flow_check(state: State) -> bool: #...
def jump(state: State) -> State: #...
def jump_check(state: State) -> bool: #...
```

Tada! That's a model baybee. You heard it here first folks, all action games are just four functions.

### Simulations are how we get useful stuff from models

But uh, how do we use these four equations? We want to simulate the model for a given start state. We can actually do this analytically, no machine learning or complicated statistics required here! Because we're coming up with simulation results deterministically, its sometimes said that we "solve" the model.

Because a `flow` is a function that takes in a state and returns a derivative, it falls under a class known as an Ordinary Differential Equation, or ODE. This is a fairly dense branch of mathematics, but there exist methods to solve for ODEs! If you give an ODE Solver a function like `flow`, a start time, a start state and some constraints like "solve until `end_time`", you can get the states (along with times) for a `flow` from the start time to end time. This is called the "initial value problem" (IVP).

This post isn't going to go into writing your own ODE Solver[^4]. I just used `scipy`'s off the shelf one. I need to tweak the model a little bit-- before we could just say our functions returned whatever, but now they need to work with a third party solver. [The documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) says that (paraphrasing):  

> The ODE function must only have two parameters: `t`, a floating point number for time and `y`, and "array_like" where each element correspond to state property. Also, the function needs to return an "array_like" of the same size as `y` where each element is `y[element]`'s derivative. Fine.  
```python
def flow(time: float, state: Tuple[float]) -> Tuple[float]
    # we'll say that state[0] is position and state[1] is velocity
    return tuple([
        state[1], # remember the derivative of position is velocity, so the derivative of state[0] is state[1]. Not the most intuitive
        -9.81
    ])
```
Then to use this thing:
```python
ode_sol = integrate.solve_ivp(
    flow, # our flow function! It returns a derivative!
    # the current time is the start time! Solve from right now until as far forward as we want to solve
    (cur_time, end_time),
    cur_state,
    # ... a bunch of solver constants to define your error tolerance and step size
)
if ode_sol.status == -1:
    return f"Oh, no, solver failed! {ode_sol.message}"
for time, state in zip(ode_sol.t, ode_sol.y.T):
    # doing a little data translation (get the transpose [T] of the y values [read as state])
    # pair them with a similarly lengthed iterable, t aka times, using zip(...)
    print(f"State at {time}: {state}")
```
[^4]: I kinda want to get into the weeds of ODE solution methods, at least the simple ones that work for this example and Flappy Bird. Maybe look forward too it if you bug me about it enough [on cohost](https://cohost.org/blit)!

There is one wrinkle: our solver doesn't know when to stop. We know that we should stop flowing when `jump_check` is `true`, but our solver, if we only give it our `flow` function, doesn't know that. We can use an event function to help here. Event functions also take in the state and time, like `flow`, but return a single scalar. We can then ask the solver to do some extra work to figure out exactly at what time an event function returns 0. We can ask for the solver to stop solving when this occurs, so we'll stop solving when we're ready to jump! But, it means that our `jump_check` function also needs a little refactor to work like an event function:
```python
def jump_check(time: float, state:tuple) -> int:
    if state.y_pos <= 0 and state.y_vel < 0:
        # stop flowing when we're ready to jump-- it's a "0 crossing" of our flow system
        return 0
    else:
        # otherwise keep flowing
        return 1
```
And since we're changing our API for two functions, we might as well change it for all of them to keep it consistent:
```python
def flow(time: float, state: tuple) -> tuple: #...
def flow_check(time: float, state: tuple) -> bool: #...
def jump(time: float, state: tuple) -> tuple: #...
def jump_check(time float, state: tuple) -> bool: #...
```
Ok, ok, ok. I think we can finally put all the pieces together into a block almost code:
```python
def solve_ball_system(flow, flow_check, jump, jump_check):
    solution:List[Any] = []
    while (cur_time < max_time and number_of_jumps < max_jumps):
        if(flow_check(cur_time, state) == 1):
            ode_sol = integrate.solve_ivp(
                flow,
                (cur_state, max_time),
                cur_state,
                events=[jump_check],
                #... again, solver stuff that we can just rely on the defaults for
            )
            if ode_sol.status == -1:
                print(f"Solver failed with message: {ode_sol.message}")
                return solution
            for time, state in zip(ode_sol.t, ode_sol.y.T):
                solution.append((time, state))

            cur_time, cur_state = solution[-1]
    
        if (jump_check(cur_time, cur_state) == 1):
            cur_state = jump(cur_time, cur_state)
            n_jumps += 1
    return solution
```

And hey, you know, _you can make a graph out of this_:

![Two graphs detailing the ball model we've been talking about. The top one is hight over time, showing smooth bounce arcs. Each arc is colored based on the jump that caused it. The bottom is a bunch of discontinuous slashes, showing the ball's velocity over time. Also colored by which jump caused it]({static}/images/better_ball_picture.png)

This is, more or less, the core loop of the [Hybrid Dynamic System solver I wrote](https://github.com/dot-jpag/PyHyEQGameSim). There's some tricks to make the zero crossing thing faster, and a lot of bookkeeping to get some abstractions so I don't need to work with raw tuples and remember which position was `velocity`.

There is one big bummer though: we had a nice `State` dataclass and lost it to work with `scipy`. What if we could get it back?

Ok, so bouncing balls are fun and all, but what about [flapping birds](https://www.rollingstone.com/culture/culture-news/the-flight-of-the-birdman-flappy-bird-creator-dong-nguyen-speaks-out-112457/)?