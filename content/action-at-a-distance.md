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

TODO: flow set breakdown
    > use bouncing ball flow set as an example
TODO: jump set breakdown
    > use bouncing ball jump set as an example
TODO: flow map breakdown
    > use bouncing ball flow map as an example
TODO: jump map breakdown
    > use bouncing ball jump map as an example

TODO / ASIDE: what about user input

TODO: bringing it all together (solver - user input psudo-code)

TODO: see where that gets me, probably talk about user input next time
