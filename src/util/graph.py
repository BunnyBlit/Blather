""" Utility for dealing with graphs. Because I insist on being annoying, there's a lot
    of extra stuff here for packing CSS into an SVG file so it'll animate.
    I'm convinced that no one will ever see it, but it'll maybe bring me joy someday
"""
from typing import List, Sequence, Dict

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from io import BytesIO
import xml.etree.ElementTree as ET

# we gotta modify some globals.
# TODO: find a better way to do this
plt.rcParams['svg.fonttype'] = 'none'
ET.register_namespace("", "http://www.w3.org/2000/svg") #avoid NS collisions 

class Graph():
    foreground: str
    background: str
    fig: Figure
    axes: List[Axes]
    styles: Dict[str, str]

    def __init__(self, background:str, foreground:str, title:str, figures:List[Sequence[int]]):
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
        self.axes[ax_idx].set_xlabel(x_label)
        self.axes[ax_idx].set_ylabel(y_label)

    def plot(self,ax_idx:int, x_data:Sequence, y_data:Sequence, label:str):
        lines = self.axes[ax_idx].plot(x_data, y_data)
        for line in lines:
            line.set_gid(label)

    def add_style(self, label:str, css_str:str):
        self.styles[label] = css_str

    def save(self, file_path):
        # serialize to SVG
        f = BytesIO()
        plt.savefig(f, format="svg")

        # reparse as xml
        tree, xmlid = ET.XMLID(f.getvalue())
        defs = tree.find("defs", {"": "http://www.w3.org/2000/svg"})
        # TODO: update the metadata as we're animating this image
        #http://purl.org/dc/dcmitype/MovingImage

        if defs:
            for style_name, style in self.styles.items():
                css = ET.SubElement(defs, "style")
                css.set("type", "text/css")
                css.text = style
                el = xmlid[style_name]
                # we actually want to overwrite certain keys on the _child_ path here
                # remove the inline style, use our separate css styling
                for path in el:
                    path.set("class", style_name)
                    path.set("style", "")

        # save for real
        ET.ElementTree(tree).write(file_path)