from typing import Iterable, Callable, Sequence

def blog_print(data:Sequence, fmt:Callable):
    """Helper function to print out a chunk of data for the blog, automatically
        truncates if there are more than lines, printing just the top and bottom
        of data
    Args:
        data (Sequence): something we can iterate over, we do need to be able to know the full
            length.
        fmt (Callable): something we can call on each element of data to get a thing to print
    """
    # print three lines before the dot dot dots and three lines at the very end
    lead = 3
    tail = 3
    if len(data) > 6:
        for elem in data[0:lead]:
            print(fmt(elem))
        print("...")
        for elem in data[-tail:]:
            print(fmt(elem))
    else:
        #otherwise just print it normal
        for elem in data:
            print(fmt(data))