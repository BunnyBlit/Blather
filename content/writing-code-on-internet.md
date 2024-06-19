Title: I just wanted to write code on the internet
Date: 2024-06-19
Category: Tech
Tags: Python, Interpreters
Slug: draft-draft-draft
Summary: Notes on what to eventually write about this process
Status: draft

# STEPS
1. go "oh hey, I want to export live python objects"
* * talk about my work flow from Jupyter notebooks -> markdown -> html
2. start with `inspect`
3. go over all the special cases required, make note that sometimes source code is not available
* * particularly for classes???
4. show where `inspect` falls apart (type hints in function source, as well as external references inside of function source)
5. show that codegen is extremely alive and well in Python, and that this _never_ works for generated code
* * RIP to dataclasses
6. open the dark pit of decompiling python byte code
