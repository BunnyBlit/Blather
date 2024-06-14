import inspect
import ast
import re
from textwrap import indent
from types import NoneType, UnionType, ModuleType
from typing import Any, List, get_args, get_origin, Union
from collections import defaultdict
from abc import ABC, abstractmethod
from pathlib import Path
from pprint import pformat

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

    def handle_imports_from_ast(self, ast_root:ast.AST) -> List[tuple[str, str]]:
        """ Walk an abstract syntax tree and generate import statements based on what we find.
        Params:
            ast_root: the root of the AST tree we're walking to generate import statements from
        """
        #print(ast.dump(ast_root, indent=4))
        for node in ast.walk(ast_root):
            if isinstance(node, ast.AnnAssign):
                print(ast.dump(node, indent=4))
                print("--------")   
        return []
    
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
        # otherwise,
        if hasattr(symbol_ref, "__module__"):
            # if this comes from a 'builtins' module, don't do any imports
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
        # we're importing a whole ass module
        elif hasattr(symbol_ref, "__package__") and symbol_ref.__package__ is not None:
            # this is a bare import with no alias
            # going to use import ...  syntax
            if symbol_ref.__package__ == "":
                self.imports["__main__"].add(symbol_name)
                return "", symbol_name
            else:
                # this is a module within a module, so split and import with from ... import syntax
                module_name, symbol_name = symbol_ref.__package__.rsplit(".", 1)
                self.imports[module_name].add(symbol_name)
                return module_name, symbol_name
        
        raise RuntimeError(f"Unable to handle import for {symbol_name} / {symbol_ref}") 

    def unpack_nested_annotation(self, kind) -> str:
        """ Annotations can be nested-- think about union types (A | B --> UnionType[A, B])
            or lists (List[A])
            This recurses down through each argument to a sum type (?) and figures out the way to import it
            before bubbling back up with the list of types to use for the annotation
        Params:
            kind: the base type that we're trying to unpack, if it has arguments
        Returns:
            a string that we can use that has all the right fixin's
        """
        # resolve a nested annotation-- we want to import the base at this level of nesting
        # if there is no base, then we want to import this type
        # kinda sorta new plan-- we're trying to import every arg _and_ the base along the way
        #   looking to end up with a string like
        #   base[arg, arg]
        #   or just arg
        imported = list() # we only generate 1 import statement, but maybe need to generate an annotation with float, float, for example
        base_type = get_origin(kind) if get_origin(kind) else kind
        type_args = get_args(kind)
        
        # for handling annotations, the flow here is a little different! if the base type is something like list or tuple
        # then the import name is special-cased out to a particular bit of code in the typing module
        # this also includes things that type to an alias, like Optional, since we need to import the original
        if base_type == list:
            self.imports["typing"].add("List")
            import_name = "List"
        elif base_type == tuple:
            self.imports["typing"].add("Tuple")
            import_name = "Tuple"
        elif base_type == UnionType:
            self.imports["typing"].add("Union")
            import_name = "Union"
        elif base_type == Union and 'Optional' in str(kind):
            self.imports["typing"].add("Optional")
            import_name = "Optional"
        else:
            _, import_name = self.handle_import(base_type.__name__, base_type)

        if len(type_args) == 0:
            # if we have an import name, that's how we reference this down the line
            # otherwise we need to do some shenanigans with nones. Our base is to just use
            # the type's __name__
            if import_name:
                return import_name
            elif base_type == NoneType:
                return "None"
            else:
                return base_type.__name__
            
        for arg in type_args:
            imported.append(self.unpack_nested_annotation(arg))
        return import_name + f"[{', '.join(imported)}]"

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