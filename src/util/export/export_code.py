import inspect
import re
from types import NoneType, UnionType
from typing import Any, List, get_args, get_origin
from collections import defaultdict
from abc import ABC, abstractmethod
from pathlib import Path

class ExportCode(ABC):
    """ Abstract base class for generating a file of code given an representation of that code as
        a code object the inspect module can handle
    Attributes:
        src_code: the original inspect code object
        export_module: the name of the module to export this code under
        name: the name of the code object we're attempting to export
        differed: the set of referenced code objects we need to export after exporting this chunk of code
        imports: the map of code objects that this chunk of code wants to import
                    we map module name --> set of things in that module to import
    """
    src_code: Any
    export_module: str
    name:str
    differed:set
    imports: dict[str, set[str]]

    def __init__(self, src_code):
        """ Constructor
        Params:
            src_code: the code object that we want to export to a new file
        """
        self.src_code = src_code
        self.name = src_code.__name__
        self.export_module = self.gen_module_name(src_code)
        self.differed=set()
        self.imports = defaultdict(set)

    def gen_module_name(self, code_object) -> str:
        """ Generate a module name for a given code object
        Params:
            code_object: the bit of python code that we want to export
        """
        return f".{re.sub(r'(?<!^)(?=[A-Z])', '_', code_object.__name__).lower()}"
    
    def can_find_source(self, code_object) -> bool:
        """ Test to see if we can find source for this code object. That's not always possible!
        Params:
            code_object: a bit of python code we want to find the source for
        """
        try:
            inspect.getsource(code_object)
            return True
        except:
            return False

    def handle_import(self, symbol_name, symbol_ref) -> tuple[str, str]:
        """ Handle the need to import a symbol for this code we want to export
            this will eventually be used to generate from module import symbol
            statements
        Params:
            symbol_name: the string name of the symbol we want to generate an import statement for
            symbol_ref: the actual symbol that we eventually want to generate code for and import into this generated code
        Returns:
            the module name, symbol name tuple that we'll use to generate an import statement
        """
        # if this global reference has a __module__ attribute
        if hasattr(symbol_ref, "__module__"):
            # if this comes from a 'builtins' module, skip it
            if symbol_ref.__module__ == "builtins":
                return "", ""
    
            # if that attribute isn't just __main__, this comes from
            #   an external module, and we should import it
            if symbol_ref.__module__ != "__main__":
                self.imports[symbol_ref.__module__].add(symbol_name)
                return symbol_ref.__module__, symbol_name
            else:
                # if it is __main__, we need to export it ourselves, then add
                # it to our import list
                self.differed.add(symbol_ref)
                will_export_under = self.gen_module_name(symbol_ref)
                self.imports[will_export_under].add(symbol_name)
                return will_export_under, symbol_name
        # if this global reference has a __package__ attribute
        # we're importing a whole ass module, but aliasing it, so we need to recover
        # that alias
        # TODO figure out a more general way to do this, I think I'm sniffing at import ... as... syntax 
        elif hasattr(symbol_ref, "__package__"):
            module_name, symbol_name = symbol_ref.__package__.rsplit(".", 1)
            self.imports[module_name].add(symbol_name)
            return module_name, symbol_name
        
        raise RuntimeError(f"Unable to handle import for {symbol_name} / {symbol_ref}") 

    def unpack_nested_annotation(self, kind, imported_names:set=set()) -> set:
        """ Annotations can be nested-- think about union types (A | B --> UnionType[A, B])
            we don't want the final type to be UnionType, we want it to be A | B
            this recurses down through each argument to a sum type (?) and figures out the way to import it
            before bubbling back up with the list of types to use for the annotation
        Params:
            kind: the base type that we're trying to unpack, if it has arguments
            imported_names: the set of symbols we'll generate import statements for, and how
                            to handle that
        """
        # resolve a nested annotation-- we want to import the base at this level of nesting
        # if there is no base, then we want to import this type
        base_type = get_origin(kind) if get_origin(kind) else kind
        if base_type == UnionType or base_type == list:
             # recurse on arguments-- slowly adding more and more to our imported names list
            type_args = get_args(kind)
            for arg in type_args:
                imported_names |= self.unpack_nested_annotation(arg, imported_names)
      
        else:
            module_name, import_name = self.handle_import(base_type.__name__, base_type)
            # do a little conversion to something we'd actually want to use later--
            # if we have an import name, that's how we reference this down the line
            # otherwise we need to do some shenanigans with nones. Our base is to just use
            # the type's __name__
            if import_name:
                imported_names.add(import_name)
            elif base_type == NoneType:
                imported_names.add("None")
            else:
                imported_names.add(base_type.__name__)

        # TODO: potentially, can't really flatten the types to one set here. Keeping track of the tree is important
        #       see, list[type]. This makes a good place to pick back up
        return imported_names


    @abstractmethod
    def generate_module(self, path:Path):
        """ This function actually writes out the python file that we can use for importing later
            should modify the file system at path
        """
        pass

    @classmethod
    @abstractmethod
    def export(cls, code_object, dir:Path):
        """ Abstract wrapper around code exporting that gives us a nice little builder pattern interface
            it's expected that calls to export eventually generate a python file at the Path, but they might not
        """
        pass