""" Utility for dealing with graphs. Because I insist on being annoying, there's a lot
    of extra stuff here for packing CSS into an SVG file so it'll animate.
    I'm convinced that no one will ever see it, but it'll maybe bring me joy someday
"""
from typing import List, Sequence, Dict
from dataclasses import dataclass
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from io import BytesIO
import xml.etree.ElementTree as ET

# we gotta modify some globals.
# TODO: find a better way to do this
plt.rcParams['svg.fonttype'] = 'none'
ET.register_namespace("", "http://www.w3.org/2000/svg") #avoid NS collisions 

@dataclass
class StyleInstance:
    """A parameterized CSS style string, along with the arguments we're going to apply to it
    Attributes:
        css_fmt (str): a format string of a CSS style class
        args (Dict): the dictionary of arguments to apply to the css style string
    """
    css_fmt: str
    args: Dict

class Graph():
    """ This is a class to represent a graph that'll eventually live as an SVG file! Vroom!
        The trick here is not only a bunch of utility methods to wrap Matplotlib's kinda bullshit API,
        but also apply CSS stylesheets to elements in the graph, which we need to do _after_ matplotlib is done.
    """
    foreground: str
    background: str
    fig: Figure
    axes: List[Axes]
    styles: Dict[str, StyleInstance]

    def __init__(self, background:str, foreground:str, title:str, figures:List[Sequence[int]]):
        """ Constructor
        Arrgs:
            background (str): a #RGB color string, determines the background color of the graph
            foreground (str): a #RGB color string, determines things like the title color and axis color of the graph
            title (str): title of the graph
            figures (List): a list of matplotlib figure sequences (like (1,1,1))-- used for laying out multiple axis on one graph
        """
        self.background = background
        self.foreground = foreground
        self.fig = plt.figure(layout="constrained")
        self.fig.suptitle(title, color=self.foreground)
        self.fig.set_facecolor(self.background)
        self.axes = [self.fig.add_subplot(*fig) for fig in figures]

        for ax in self.axes:
            ax.set_facecolor(self.background)
            ax.xaxis.label.set_color(self.foreground)
            ax.yaxis.label.set_color(self.foreground)
            ax.spines['top'].set_color(self.foreground)
            ax.spines['left'].set_color(self.foreground)
            ax.spines['right'].set_color(self.foreground)
            ax.spines['bottom'].set_color(self.foreground)

            ax.tick_params(axis='x', colors=self.foreground)
            ax.tick_params(axis='y', colors=self.foreground)
        
        self.styles = {}

    def set_axis_labels(self, ax_idx:int, y_label:str, x_label:str):
        """ Add labels to a set of axis on the figure
        Args:
            ax_idx (int): the index of the axis we want to add labels to
            y_label (str): label in the y direction
            x_label (str): label in the x direction
        """
        self.axes[ax_idx].set_xlabel(x_label)
        self.axes[ax_idx].set_ylabel(y_label)

    def plot(self,ax_idx:int, x_data:Sequence, y_data:Sequence, label:str) -> Sequence[str]:
        """ Plot a single line on an axis, given 2D data
        Args:
            ax_idx (int): the index of the axis we want to add a plot to
            x_data (Sequence): the values of the x-dimension of the data to plot
            y_data (Sequence): the values of the y-dimension of the data to plot
            label (str): a label to use as the basis for a unique ID for each element in the plot
        Returns:
            Sequence[str]: a list of IDs for the lines plotted as part of this call to plot, with the form {label}_1, {label}_2, etc
        """
        lines = self.axes[ax_idx].plot(x_data, y_data)
        plotted_ids = []
        for idx, line in enumerate(lines):
            computed_id = f"{label}_{idx + 1}"
            plotted_ids.append(computed_id)
            line.set_gid(computed_id)
        
        return plotted_ids
    
    def add_rectangle(self, ax_idx:int, top_left:Sequence, width:float, height:float, label:str) -> str:
        """ Add a rectangle as a patch to the graph
        Args:
            ax_idx (int): the index of the axis we want to add the rectangle to
            top_left (Sequence): a pair, as (x,y), of the top left of the rectangle
            width (float): width of the rectangle
            height (height): height of the rectangle
            label (str): an ID to use for the rectangle in the plot
        Returns:
            str: the ID to find this rectangle in the plot
        """
        # note the difference here-- plot returns a list of ids that are based on the label, add_rectangle assumes you're already passing in the id
        # kinda sucks from an API perspective, but whatever here we are
        bottom_left = (top_left[0], top_left[1] - height,) #matplotlib wants the bottom left. Whatever
        patch = self.axes[ax_idx].add_patch(Rectangle(bottom_left, width, height))
        patch.set_gid(label)

        return label

    def add_style(self, label:str, css_fmt_str:str, css_fmt_args:Dict):
        """ Add a parameterized style to an element in the graph. We actually apply styles later,
            so instead of something normal, we take in a format string along with the arguments to apply,
            and cash that for now. This is very normal.
        Args:
            label (str): element ID we want to apply this style to
            css_fmt_str (str): a CSS class as a format string
            css_fmt_args (Dict): the arguments to apply to the above format string
        """
        self.styles[label] = StyleInstance(css_fmt=css_fmt_str, args=css_fmt_args)

    def save(self, file_path):
        """ Save the graph as an SVG file! This is also where we realize the CSS style classes and rewrite graph elements to use the css style classes
            we have, instead of whatever inline bullshit matplotlib has decided to use.
        Args:
            file_path (Path): file path to save this here SVG at
        """
        # serialize to SVG, aka save for fake
        f = BytesIO()
        plt.savefig(f, format="svg")

        # reparse as xml
        tree, xmlid = ET.XMLID(f.getvalue())
        defs = tree.find("defs", {"": "http://www.w3.org/2000/svg"})
        # TODO: update the metadata as we're animating this image
        #http://purl.org/dc/dcmitype/MovingImage

        if defs:
            for element_id, style in self.styles.items():
                css = ET.SubElement(defs, "style")
                css.set("type", "text/css")
                css.text = style.css_fmt.format(**style.args)
                el = xmlid[element_id]
                # we actually want to overwrite certain keys on the _child_ path here
                # remove the inline style, use our separate css styling
                for path in el:
                    path.set("class", style.args["style_name"]) # we love hidden constraints! We always need to supply a style name, which should super be in the StyleInstance somewhere
                    path.set("style", "")

        # save for real
        ET.ElementTree(tree).write(file_path)