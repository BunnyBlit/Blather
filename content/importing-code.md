Title: How does `import` work in Python?
Date: 2024-06-28   
Category: Tech   
Tags: Programming Languages   
Slug: importing-in-python  
Summary: No but really, how does Python figure out what code to import when?   
Status: draft

It's remarkable how often importing Python code comes up in my life. It sounds so silly and easy, right? [One of the older XKCDs even makes a joke about it](https://xkcd.com/353/).

And yet, I have yet to meet a person who hasn't seen this while learning Python:


```python
# from some_module_that_is_RIGHT_THERE import do_thing

# do_thing()
```

So, how does Python actually import code? What does the `import` statement even _do_?

I won't be covering any ground that you couldn't figure out by reading [the Python language documentation](https://docs.python.org/3/library/importlib.html), and when we hit interpreter specific behavior, I'll default to how CPython behaves. It's still useful going over all of docs and any relevant `PEP`s if you _really_ want to know things, but hopefully this works as a jumping off point.

## What is the import statement?

I'm going to skip the semantics of `import` and dive right into the heart of the matter: `import bar` is [syntactic sugar over a builtin internal function `__import__(...)`](https://docs.python.org/3/library/functions.html#import__). So, the import statement is a function call. That function imports a *module*, using local and global variables to figure out how to interpret that name. Easy!

Ok, fine.

## ~~What is the import statement~~ What is a Python module?
[Software is always Like This](https://www.stilldrinking.org/programming-sucks). A module is _kinda_ [analogous to a file](https://docs.python.org/3.12/tutorial/modules.html), and contains all the functions, classes and variables you might want to use somewhere else in your codebase. The `import` statement makes these available under the file name from a different module.


```python
import inspect # for looking at live Python objects
from pathlib import Path # I like object-oriented paths, fite me.

# an example function to import
def hi_pikachu() -> str:
    """ Say hi, Pikachu!
    """
    return "Pika, pika!"

# should at least pretend to be tidy, lets make a folder to hold onto our code
Path("tmp/importing_in_python").mkdir(exist_ok=True)

# and write our function down in a file called 'pika.py'
with open("tmp/importing_in_python/pika.py", "w") as f:
    # use inspect to get the Python source code of the live function "hi_pikachu"
    src_string = inspect.getsource(hi_pikachu)

    # tada, we made a module dynamically!
    f.write(src_string)

# and now that we wrote a file, we can import it
import tmp.importing_in_python.pika #type: ignore static typing does not like BS like this
print(tmp.importing_in_python.pika.hi_pikachu())
```

    Pika, pika!


And, yes, there is a fresh new Python module at that path location, this isn't me pulling a fast one. We can open it and read it like any other file:


```python
with open("tmp/importing_in_python/pika.py", "r") as f:
    print(f.read())
```

    def hi_pikachu() -> str:
        """ Say hi, Pikachu!
        """
        return "Pika, pika!"
    


It is kinda fun that documentation comments were preserved when we used `inspect`, no? I think it's fun.

Back on track: I actually have multiple versions of `hi_pikachu` in scope. They're not the same function! A fun [`CPython` implementation detail](https://docs.python.org/3/library/functions.html#id) is that `id(...)` gives you the memory address of that object, so:


```python
print(f"original \"local\" function is at: {id(hi_pikachu)}")
print(f"function from our dynamic module: {id(tmp.importing_in_python.pika.hi_pikachu)}")
```

    original "local" function is at: 4425267008
    function from our dynamic module: 4425266848


But, if we mess with the imports a liiiiiittle bit


```python
from tmp.importing_in_python.pika import hi_pikachu
print(f"function from our dynamic module: \t{id(tmp.importing_in_python.pika.hi_pikachu)}")
print(f"the \"local\" version: \t\t\t{id(hi_pikachu)}")
```

    function from our dynamic module: 	4425266848
    the "local" version: 			4425266848


I "overwrote" the "local" implementation of `hi_pikachu`. Doing crimes in interpreted languages is fun.

Every single Python module is executed in its own _namespace_. This is a mapping of names (like function name `hi_pikachu`) to a thing at a virtual memory address (in this case `4415138816`). Namespaces are useful because they let us scope things and reuse names in more than one part of our program. Two modules can have the same function name and not conflict, which is great if you want to share your code with Steve and his demand to only ever use the function name `apply`. 

We live in a blessed age where we can spread out our names a bit. Python doesn't just parse a file when it imports it, though.


```python
# I don't know a neat trick to wrap statements into a first-order thing in Python
# so no neat inspect tricks here-- gonna just write the module source code as a bare string
# like a monster
module_source = """
sum = 1 + 2
print(__name__)
print(sum)
"""

# same trick as before -- lets write our module source in a .py file
Path("tmp/importing_in_python").mkdir(exist_ok=True)
with open("tmp/importing_in_python/name_and_addition.py", "w") as f:
    f.write(module_source)

import tmp.importing_in_python.name_and_addition #type: ignore static typing does not like this
```

    tmp.importing_in_python.name_and_addition
    3


Oh hey, output.

Importing a file in Python evaluates it-- Python, by default, uses eager evaluation of imports. Most of the time, this is fine, but if you have a massive Python file, having to parse and run that file can be a lot. However...


```python
import tmp.importing_in_python.name_and_addition
import tmp.importing_in_python.name_and_addition

# look ma, no output
```

no output this time -- because Python caches imports. You can litter your codebase with `import foobar` and the import operation will only happen once, for `foobar`. So, roughly, we can think of `import foobar` doing three things:
1. searching for a Python module named `foobar`
2. running the interpreter over that module, putting any created functions or variables under the namespace `foobar`
3. saving that result, so we don't need to rerun the module again.


