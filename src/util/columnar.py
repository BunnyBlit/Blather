"""Column-like serialization for data
"""
from abc import ABC
from typing import Dict, List, get_origin, get_args
import csv
from pathlib import Path
import re
import inspect

class Columnar():
    """ Base class for holding onto some simple ops for doing data manipulation
        Allows for dynamic lookup with Serializable[key] syntax
        Data gets serialized as:
        class.attr = [value, value, value], where 
            type(value) == get_args(__annotations__[key])[0]
        In English, data is converted to the correct type given the annotations on the subclass
    """
    
    def __init__(self):
        """ Constructor! You also need to pass a taxonomy of types
            so we can serialize data correctly. We also check that the 
            provided class attributes are all lists
        """
        self.__check_init()

    def append_from_dict(self, data:Dict):
        """ Append a new element to the serializable lists, checking to ensure
            that it fits constraints.
        Args:
            data (Dict[str, type]): a single "row" of data, as a dictionary. For example:
                {"name": "sam", "number": 5, ...}
        """
        self.__check_dim(data)
        for key, value in data.items():
            self.__append_and_convert(key, value)

    @classmethod
    def from_csv(cls, csv_path:Path):
        """ Given a CSV file (with column names) and a taxonomy,
            built out a Columnar dataclass
        Args:
            csv_path (Path): path to a csv file (with column names) on the file system
            taxonomy (Dict[str, class]): the types of each value in the csv
        """
        instance = cls()
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                instance.append_from_dict(row)
    
        return instance

    def __append_and_convert(self, key:str, value:str):
        """ Convert the value to the type in the annotations under key, and add it to the
            appropriate list
        Args:
            key (str): the name of the column to add this value to
            value (str): the stringified value we want to add to the column
        """
        annotations = inspect.get_annotations(type(self))
        assert key in annotations

        to_type = get_args(annotations[key])[0]
        if to_type == str: 
            self[key].append(value) # value's already a string
        elif to_type == int:
            self[key].append(to_type(float(value))) # absolutely should have more checks here
        else:
            self[key].append(to_type(value))
    
    def __check_dim(self, data:Dict):
        """ Check the dimensionality (cardinality?) of the row of data coming in--
            the new "row" of data needs to have the same number of columns as the number
            we're tracking
        Args:
            data (Dict[str, Any]): a "row" of data, as a dictionary. For example:
                {"name": "sam", "number": 5, ...}
        """
        attrs_set = set(inspect.get_annotations(type(self)).keys())
        assert len(attrs_set) == len(data.keys())
    
    def __check_init(self):
        """ Check that we've initialized a subclass correctly. All attributes must have
            the 'list' type
        """
        annotations = inspect.get_annotations(type(self))
        for key, value in annotations.items():
            assert type(value) == list
        
    def __getitem__(self, key):
        """ Get an item from the serializable. Lets us use class[name] syntax to get the
            list, which is nice
        """
        return getattr(self, key)