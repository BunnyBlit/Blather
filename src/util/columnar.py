"""Column-like serialization for data
"""
from abc import ABC
from typing import Dict, List
import csv
from pathlib import Path
import re

import attr

class Columnar(ABC):
    """ Base class for holding onto some simple ops for doing data manipulation
        Allows for dynamic lookup with Serializable[key] syntax
        Data gets serialized as:
        class.attr = [value, value, value], where type(value) == self.taxonomy[attr]
    """
    taxonomy: Dict
    __hidden_attr_regex: re.Pattern
    
    def __init__(self, taxonomy):
        """ Constructor! You also need to pass a taxonomy of types
            so we can serialize data correctly. We also check that the 
            provided class attributes are all lists
        Args:
            taxonomy: Dict[str, class] a dictionary of string keys to types,
                tells us what the type of each column is, and provides a way to
                serialize to that type
        """
        self.__hidden_attr_regex = re.compile(r"^_")
        self.__check_taxonomy(taxonomy)
        self.taxonomy = taxonomy
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
            self.__check_data(key, value)
            value_type = self.taxonomy[key]
            self[key].append(value_type(value))

    @classmethod
    def from_csv(cls, csv_path:Path, taxonomy:Dict):
        """ Given a CSV file (with column names) and a taxonomy,
            built out a Columnar dataclass
        Args:
            csv_path (Path): path to a csv file (with column names) on the file system
            taxonomy (Dict[str, class]): the types of each value in the csv
        """
        instance = cls(taxonomy)
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                instance.append_from_dict(row)
    
        return instance

    def __check_taxonomy(self, taxonomy:Dict):
        """ Given a taxonomy (str -> type mapping), check to make sure that
            each of its keys is in our attribute list
        Args:
            taxonomy (Data[str, type]): a dictionary that tells us what type each of our columns has
        """
        
        attrs_set = set(self.__extract_attribute_names())
        taxonomy_set = set(taxonomy.keys())
        # the venn diagram should be a perfect circle
        if len(attrs_set) != len(attrs_set.union(taxonomy_set)):
            print(f"Attributes: {attrs_set}")
            print(f"Taxonomy: {taxonomy_set}")
            assert False
    
    def __extract_attribute_names(self) -> List:
        """Pull out attribute names for the class.

        Returns:
            List: a list of all the attribute names defined on this class
                subclasses 
        """
        cls_ref_keys = [key for key in vars(type(self)).keys()]
        attrs = [key for key in cls_ref_keys if not self.__hidden_attr_regex.match(key)]
        return attrs

    def __check_data(self, key:str, value):
        """ For a particular column name and value, check that the column exists and
            that the type of the taxonomy lines up with the type of the value
        Args:
            key (str): column name
            value (Any): the value to add to that column
        """
        attrs = self.__extract_attribute_names()
        assert key in attrs
        assert key in self.taxonomy
    
    def __check_dim(self, data:Dict):
        """ Check the dimensionality (cardinality?) of the row of data coming in--
            the new "row" of data needs to have the same number of columns as the number
            we're tracking
        Args:
            data (Dict[str, Any]): a "row" of data, as a dictionary. For example:
                {"name": "sam", "number": 5, ...}
        """
        attrs = self.__extract_attribute_names()
        assert len(attrs) == len(data.keys())
    
    def __check_init(self):
        """ Check that we've initialized a subclass correctly. All attributes must have
            the 'list' type
        """
        attrs = self.__extract_attribute_names()
        for name in attrs:
            assert type(self[name]) == list
        
    def __getitem__(self, key):
        """ Get an item from the serializable. Lets us use class[name] syntax to get the
            list, which is nice
        """
        return getattr(self, key)