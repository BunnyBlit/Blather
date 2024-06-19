from typing import Set, Dict, List, Any, get_args, get_origin
from types import NoneType, UnionType
from .export_code import ExportCode
from .export_function import ExportFunction
from pathlib import Path
import inspect
from pprint import pprint, pformat

class ExportClass(ExportCode):
    """ Class for handling the process of going from Python bytecode to Python source
        so we can import this later
    Attributes:
        inherits: the set of superclass names that this class comes from
        properties: a dictionary of name, type string pairs for the properties on this object
        methods: a list of ExportFunction objects that are the methods on this class
        dummy: a dummy type to identify python-generated parts of a class (we only need the human parts)
    """
    inherits: Set[str]
    properties: Dict[str, str]
    methods: List[ExportFunction]
    dummy: Any

    def __init__(self, code_object):
        """ Constructor
        Params:
            code_object: the class that we're trying to export to a file
        """
        super().__init__(
            src_code=code_object,
        )
        self.inherits = set()
        self.properties = {}
        self.methods = []
        # create a dummy reference to use to filter properties with
        # if its in the dummy, it's python generated and we don't want to write it
        self.dummy = dir(type('dummy', (object,), {}))

    def generate_module(self, export_dir:Path):
        """ Generate source code for a python class that we can import later!
        Params:
            export_dir (Path): directory where all the code from this export is gonna go
        """
        # create required directories
        export_dir.mkdir(parents=True, exist_ok=True)
        # trim a leading dot from the export_module if we need to
        if self.export_module.startswith("."):
            file_name = self.export_module[1:] + ".py"
        else:
            file_name = self.export_module + ".py"
        path = export_dir / file_name #pathin'

        with open(path.resolve(), "w") as f:
            # import statements
            for module, symbols in self.imports.items():
                if module != "__main__":
                    # everything ends up in the same directory so we don't need to think to hard
                    # about execution location for imports
                    f.write(f"from {module} import {', '.join(symbols)}\n")
                else:
                    for symbol in symbols:
                        f.write(f"import {symbol}\n")

            f.write("\n")
            # class declaration
            f.write(f"class {self.name}({', '.join(self.inherits)}):\n")
            # properties
            for prop_name, prop_type in self.properties.items():
                f.write(f"    {prop_name}: {prop_type}\n")
            f.write("\n")
            # methods
            for method_pieces in self.methods:
                source_lines = method_pieces.source.split("\n")
                for line in source_lines:
                    f.write(f"    {line}\n")
                f.write("\n")

        # the module name for importing this class is the stem of the file path... hopefully
        self.export_module = path.stem
        return self
    
    def handle_inheritance(self):
        """ Look at the MRO of the class so we can figure out this class's inheritance,
            generate import statements if required for them, and write out the class declaration correctly
        """
        mro = inspect.getmro(self.src_code)
        # TODO: if I ever dip into multiple inheritance, I'll need to be more complicated here, but roughly, I only care about the first two elements
        if mro[0] != self.src_code: raise Exception(f"Unexpected MRO for {self.src_code}:\n{mro}") 
        superclass = mro[1] if mro[1] != object else None
        # TODO: we actually don't even handle single inheritance yet
        if superclass:
            print(f"Warning! Superclass handling is not completely in yet! Can't handle {superclass}")
        
        return self

    def handle_properties(self):
        """ Figure out the names and types of the properties on this object, so we can generate correct
            property statements later. We look at the class's __annotations__ property and the source code of the
            constructor to figure out what the properties are.
        """
        # TODO: also, one could dynamically assign props in the middle of a method, so we'll probably need to handle
        #       that at some point

        # ok, gameplan-- start with __annotations__ if we have it
        if hasattr(self.src_code, "__annotations__"):
            cls_annotations = self.src_code.__annotations__
            for name, annotated_type in cls_annotations.items():
                imported_name = self.unpack_nested_annotation(annotated_type)
                self.properties[name] = imported_name
        
        # then grab anything we can get from __init__ that isn't initialized
        init_funct = getattr(self.src_code, "__init__", None)
        if init_funct:
            _nonlocals, _globals, _buildin, _unbound = inspect.getclosurevars(init_funct)
            for name in _unbound:
                if name not in self.properties:
                    self.properties[name] = "Any"

        return self
    
    def handle_methods(self):
        """ Find all the methods inside the class and figure out if we have source code for them. Not all methods
            are generable-- some don't have source code, some have references that we can't easily handle.
            For all the methods we can handle, create ExportFunction objects for them and add them to our list of class
            methods
        """
        # TODO: there's a cleaner way to do this where we push a lot of this logic inside ExportFunction
        #        and bubble it up
        method_names = [func for func in dir(self.src_code) if callable(getattr(self.src_code, func)) and func in self.src_code.__dict__]
        #print(f"... {method_names}")
        for method_name in method_names:
            method = getattr(self.src_code, method_name)
            _nonlocals, _globals, _builtins, _unbound = inspect.getclosurevars(method)
            if(not self.can_find_source(method)):
                print(f"skip {method_name}, couldn't get source code for it. May be generated by Python")
                # we can't generate code for this, we're gonna hope Python takes care of it for us
                continue
            if(len(_nonlocals) > 0):
                # there are extra references here that we can't handle. this may be figure-out-able
                # with import ... as syntax but
                print(f"skip {method_name}, source code inside the function has references to symbols we can't track")
                continue
            new_method = ExportFunction(method).handle_references().handle_annotations()
            self.methods.append(new_method)

            # promote references inside ExportFunction back up the the class
            for module_name, symbols in new_method.imports.items():
                self.imports[module_name] |= symbols
            self.differed |= new_method.differed

        return self

    @classmethod
    def export(cls, code_object, path):
        """ The actual export function! Creates all the code references and then prints them out to a file
            under the path provided
        Params:
            code_object: the code object we want to turn back into source code
            path: where we want the code to eventually live in the file system
        """
        return ExportClass(code_object)\
            .handle_inheritance()\
            .handle_properties()\
            .handle_methods()\
            .generate_module(path)
    
