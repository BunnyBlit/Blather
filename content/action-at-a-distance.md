Title: Action At A Distance
Date: 2023-02-10
Category: Tech
Tags: simulations, Python, How Madeline Jumps
Slug: action-at-a-distance
Summary: A complicated way to explain game mechanics to a computer

Games are complicated.

They have a lot of stuff you can do! You can [click on things](http://orteil.dashnet.org/cookieclicker/), [crash space ships](https://www.kerbalspaceprogram.com/), [play pinball](https://blogs.windows.com/windowsexperience/2015/10/09/pinball-fx2-windows-10-edition-is-now-available/) or even [bounce a ball back and forth](https://www.ponggame.org/).

Very rarely-- and it truly is a cursed moment when it happens-- I'm called on to design some part of a game. Usually a level or a mechanic. And not only is this really hard because [game design is extremely difficult, and we should worship the ground all game developers stand on](https://www.gamedeveloper.com/design/-quot-the-door-problem-quot-of-game-design), _but also_ because I am _really bad at games_. A big chunk of design is play testing, and I really struggle to get out of my own skin to not water down _the heck_ out of everything I design.

I was in the middle of one of these rare struggles when I saw Joseph Osborn[^1] present Yegeta Zeleke's paper on [analyzing and molding simple action games](https://dl.acm.org/doi/pdf/10.1145/3337722.3337757). I didn't really understand the presentation at the time-- but I couldn't stop thinking about it.

I want to be abundantly clear: game mechanics modeling and simulating _does not_ replace good design. When done well, it can work as a lense to help view _some_ aspects of a design. They will not replace you. They will not make something good for you. Programs are extremely focused and narrow tools: do not make the [tech bro mistake](https://nypost.com/2022/06/24/suspended-google-engineer-claims-sentient-ai-bot-has-hired-a-lawyer/) and think they are anything more than that.

[^1]: I know Joseph Osborn in real life-- we were in sister graduate programs. I look up to Joe very highly, I think he's super smart. I do not know Yegeta, who is the primary contributor of the above paper.

Could something like the above model help me?

### So, Let's Dive In

The paper is a case study in applying a math thing called a Hybrid Dynamical System to [Flappy Bird](https://kotaku.com/the-flappy-bird-fiasco-1519938266). I believe in your ability to experience a Flappy Bird clone, so what's a Hybrid Dynamical System?

> We use the following general framework to define hybrid systems as a tuple (C, F, G, D). A closed-loop (i.e., without any input) hybrid system H comprises a flow set C ⊂ R<sup>n</sup>, which is a subset of n-dimensional real numbers denoted R<sup>n</sup>, a jump set D ⊂ R<sup>n</sup>, continuous dynamics given by a flow map F : R<sup>n</sup> ⇒ R<sup>n</sup>, and discrete dynamics given by a jump map G : R<sup>n</sup> ⇒ R<sup>n</sup> , where the symbol ⇒ is used to indicate that points are mapped into sets.

uh. Well, I tried. Let's pack it up folks.

I also struggle with reading the above paragraph. So much so, that I ended up [writing a program about it](https://github.com/dot-jpag/PyHyEQGameSim). I don't blame anyone for writing like this! The audience of the paper isn't my dumb ass, but other academics who can parse the above paragraph. The language is technical and precise-- it means very particular things to it's audience. I'll do my best to break it down into Python-ish psudocode.

We could have a whole debate about programming languages, but I'm comfortable in Python, and like to start here. This is not where we'll end up (eventually).

The core concept here is that we can break a system (read as: game) into two parts:  

1. The continuous part: this part is things like jump arcs and smooth velocity changes. These parts of the game change continuously while they're happening, probably handled by a physics engine. When a game is operating this way, it's _flowing_.  
2. The discrete parts: this part is sudden, sharp changes in a game, like switching from one mode to another. Characters are very often modeled as a collection of sharp switches-- you're not jumping, you hit the jump button, and then suddenly you are! When a game is operating this way, it's _jumping_.

### Let's start with something more simple than Pong

The proverbial first example with Hybrid Systems is a bouncing ball, which I'll use because having a grounded example keeps my brain focused. Speaking of brain focused, I also want to talk about jumping first-- it's a little easier to wrap my head around. Let's also make this as simple as possible: don't worry about horizontal position, just vertical. The ball has a state that's something like:
```python
# just pretend this is a struct
# also, pretend that python has structs
class State:
    y_pos: float # vertical position
    y_vel: float # vertical velocity
    y_accel: float # vertical acceleration
```

So, when does a bouncing ball jump? It starts by falling-- seems pretty continuous-- then hits the ground, then suddenly springs back up. It's that contact with the ground that's a jump, a sudden switch in state. The ball's velocity was going down, now in a instant, it's going up![^2]

[^2]: I actually know almost no physics, but I'm sure that in reality, this is all a continuous system and there are some mind bending equations to calculate how potential energy flows. Thinking about it as a jump works well for this, though, even if it's not technically correct. Models very rarely are.

What might that look like in code?
```python
def jump(state:State) -> State:
    new_state:State = state.copy() # I am so not thinking about copy semantics of psudocode
    # flip the velocity
    new_state.vel = -state.vel
    # return!
    return new_state
```

"Woah, slow down there cowboy," you say, in my head. "How does that function know _when_ to jump?"

Ah! Right. If we flip the velocity while we're still falling, for example, we'll just go more up. That's not how gravity works. The gamers would be very mad at our lack of attention to realism in Ball Sim 2023.[^3] This is where the _jump map_ comes into play. It's a function we can run [^4] to say if we should be jumping or not.

[^3]: Gonna need to workshop this title
[^4]: It's right while I was writing this sentence that I came up with an idea on how to parallelize solving the entire Hybrid Dynamic System, which I'm gonna capture in a footnote for all of time: "don't make the CPU predict which part of the flow set we're in with an if-statement, _solve every single one in parallel at every time step_. If this works, I'm going to vomit. 
```python
def jump_check(state:State) -> bool:
    if (state.y_pos == 0):
        # collision detection? What's that? Everyone knows the ground is 0 :)
        # anyway, we be jumpin if we hit the ground
        return True
    else:
        # otherwise don't state transition
        return False
```
That covers jumps-- there's a function to say "hey, we need to transition states and this is how we're gonna do it" and another function that says when it's time to do that transition". Flows are mostly similar. There's a function to run to say how we're flowing (`flow`), and a function to say if we should be flowing or not `flow_check`. The.. well, the check function gets a little silly with our ball example:
```python
def flow_check(state: State) -> bool:
    return True
```
I know. This feels like I'm pranking you. I'm not trying to. Sometimes it's just like that. Jumps are instantaneous moments in time, so _for an instant_ we jump, but it's not like we stop flowing while that's happening. Its just an instant. We're always flowing here, there's no point in our system where we would just... hang out. That leaves us with one function-- `flow`, and uh, well, there's no great way to say this: it's needs to calculate the derivative of the state with respect to time. `flow`, is, as they say, a differential equation.

But they aren't hard derivatives! Calculus gives us a bunch of analytical tools to solve these.
The derivative of position is the velocity, right? and the derivative of velocity is acceleration! And... we'll just pretend acceleration is constant. Plenty of video games do. So, because it doesn't change, it's derivative is 0!
TODO: check this, I've already worked out this example. DAccel might just be gamma.

And this is all with respect to time-- we care how position, velocity and acceleration change over time.
```python
def flow(time: float, state:State) -> Derivative:
    return Derivative(
        derivative_position=state.y_vel,
        derivative_velocity=state.y_accel,
        derivative_acceleration=0
    )
```

I was _terrified_ when I started that the flow part was gonna be super gnarly, but it's not that bad! We just need to describe how values change, usually in terms of other values. We can do that! To make this a little easier on ourselves, we actually parameterize every function by time, as well as number of jumps, giving us the following signatures:
```python
def flow(time: float, state: State, jumps: int) -> Derivative: #...
def flow_check(time: float, state: State, jumps: int) -> bool: #...
def jump(time: float, state: State, jumps: int) -> State: #...
def jump_check(time float, state: State, jumps: int) -> bool: #...
```

### A Simulation is a Solution to a System

But uh, how do we use these four equations? Well, we write a little solver for them, of course! Very much abstracted here to not handle edge cases:
```python
while (cur_time < max_time or n_jumps < max_jumps):
    if(flow_check(cur_time, state, n_jumps)):
        # uh, ok, look, I did hand wave a big part and that part is
        # using an ODE solver to get how the state changes over
        # a time interval, given the flow function
        # maybe we can get into the Runge-Kutta method
        # in another post? It's got wonky numbers!
        ode_solution = ODESolver.solve(
            flow,
            (cur_time, max_time),
            cur_state
        )
        # the solution is how the state evolves over the interval
        # so it has a lot of intermediate states in it, and you'd want all of those
        # but technically we only need the last one
        cur_time, cur_state = ode_solution[-1]
    if (jump_check(cur_time, cur_state, n_jumps)):
        cur_state = jump(cur_time, cur_state, n_jumps)
        n_jumps += 1
```

And that's kinda it! We just use an ODE solver to shift forward according to our flow equation until we hit something that forces us to stop, see if we should jump, and jump accordingly. Repeat until we're bored (hit as far forward as we want to look, or as many jumps as we want to deal with). We've solved video games!

ah

right

I forgot about players again. Tune in for another part!