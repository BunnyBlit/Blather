from typing import Set, Dict, List, Any
from .export_code import ExportCode
from pathlib import Path
import inspect


class ExportNamedTuple(ExportCode):
    """ Builder pattern for exporting a named tuple-- holds onto all the code required to handle a special
        case of a class
    Attributes:
        inherits: the set of superclasses for this namedtuple. "tuple" should always be a member!
        properties: the properties on this namedtuple. This kinda turns it into a dataclass with style
    """
    inherits: Set[str]
    properties: List[str]

    def __init__(self, src_code):
        """ Constructor
        Params:
            src_code: the source code of this namedtuple, the code object we're trying to turn back into
                        legible source
        """
        super().__init__(src_code)
        self.inherits = set()
        self.properties = []

    def generate_module(self, export_dir:Path):
        """ Generate source code for a Python NamedTuple we can import later
        Params:
            export_dir: the location on the local file system where this will eventually get exported to
        """
        # TODO: move this to superclass
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
            for prop in self.properties:
                f.write(f"    {prop}: Any\n")
            f.write("\n")

        # the module name for importing this class is the stem of the file path... hopefully
        self.export_module = path.stem
        return self
     
    def handle_inheritance(self):
        """ Handle the inheritance for named tuples-- add the correct superclasses to this class
            so we'll generate the right python statements later
        TODO: this is pretty hardcoded! It'd be cooler to be able to special case this as a part of how classes work
        """
        self.inherits.add("NamedTuple")
        self.imports["typing"].add("NamedTuple")
        
        return self
    
    def handle_properties(self):
        """ Convert the _fields attribute of our old named tuple to properties that we can export
        """
        # assuming that named tuples always have an _fields attribute that we can use
        prop_names = getattr(self.src_code, "_fields", tuple())
        # TODO: I don't know if this order is enforced or not and I'm not going deep into python internals about it
        #       _but_ in very light introspection of two entire cases, the order of these names is the order we want
        self.properties = list(prop_names)
        self.imports["typing"].add("Any") # TODO: I think named tuples can be typed-- and I might want to add that in
        return self
    
    @classmethod
    def export(cls, src_code, path:Path):
        """ Given our named tuple in code, generate a python file someone could import to use that same named tuple
        Params:
            src_code: the actual code object we're trying to export as python source
            path: where we want to export this code object
        """
        return ExportNamedTuple(src_code)\
                .handle_inheritance()\
                .handle_properties()\
                .generate_module(path)
    
