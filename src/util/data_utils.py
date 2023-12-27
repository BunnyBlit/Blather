"""Column-like serialization for data
"""
from abc import ABC
from typing import Dict
import csv
from pathlib import Path

class Columnar(ABC):
    """ Base class for holding onto some simple ops for doing data manipulation
        Allows for dynamic lookup with Serializable[key] syntax
        Data gets serialized as:
        class.attr = [value, value, value], where type(value) == self.taxonomy[attr]
    """
    taxonomy: Dict
    
    def __init__(self, taxonomy):
        """ Constructor! You also need to pass a taxonomy of types
            so we can serialize data correctly. We also check that the 
            provided class attributes are all lists
        Args:
            taxonomy: Dict[str, class] a dictionary of string keys to types,
                tells us what the type of each column is, and provides a way to
                serialize to that type
        """
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
        for key, value in data:
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
        attrs = vars(self)
        for key in taxonomy.keys():
            assert key in attrs
    
    def __check_data(self, key:str, value):
        """ For a particular column name and value, check that the column exists and
            that the type of the taxonomy lines up with the type of the value
        Args:
            key (str): column name
            value (Any): the value to add to that column
        """
        attrs = vars(self)
        assert key in attrs

        assert key in self.taxonomy
        assert type(self.taxonomy[key]) == type(value)
    
    def __check_dim(self, data:Dict):
        """ Check the dimensionality (cardinality?) of the row of data coming in--
            the new "row" of data needs to have the same number of columns as the number
            we're tracking
        Args:
            data (Dict[str, Any]): a "row" of data, as a dictionary. For example:
                {"name": "sam", "number": 5, ...}
        """
        assert len(vars(self).keys()) == len(data.keys())
    
    def __check_init(self):
        """ Check that we've initialized a subclass correctly. All attributes must have
            the 'list' type
        """
        attrs = vars(self)
        for value in attrs.values():
            assert type(value) == list
        
    def __getitem__(self, key):
        """ Get an item from the serializable. Lets us use class[name] syntax to get the
            list, which is nice
        """
        return getattr(self, key)