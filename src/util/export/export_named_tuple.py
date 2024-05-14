from typing import Set, Dict, List, Any
from .export_code import ExportCode
from .export_function import ExportFunction
from pathlib import Path
import inspect


class ExportNamedTuple(ExportCode):
    """ Builder pattern for exporting a named tuple
    """
    inherits: Set[str]
    properties: List[str]

    def __init__(self, src_code):
        super().__init__(src_code)
        self.inherits = set()
        self.properties = []

    def generate_module(self, export_dir:Path):
        """ Generate source code for a Python NamedTuple we can import later
        TODO: DOCUMENT THIS BETTER
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
        """ DOCUMENTATION ABOUT HANDLING INHERITANCE FOR NAMED TUPLES
            ITS PRETTY HANDWAVY AND HARDCODED
        """
        self.inherits.add("NamedTuple")
        self.imports["typing"].add("NamedTuple")
        self.dummy = dir(type('dummy', (tuple, object,), {}))
        
        return self
    
    def handle_properties(self):
        """ DOCUMENTATION ABOUT HANDLING PROPERTIES FOR NAMED TUPLES
        """
        # assuming that named tuples always have an _fields attribute that we can use
        prop_names = getattr(self.src_code, "_fields", tuple())
        # TODO: I don't know if this order is enforced or not and I'm not going deep into python internals about it
        #       _but_ in very light introspection of two entire cases, the order of these names is the order we want
        self.properties = list(prop_names)
        self.imports["typing"].add("Any")
        return self
    
    @classmethod
    def export(cls, src_code, path:Path):
        """ DOCUMENTATION ABOUT HOW THIS EXPORT WORKS
        """
        return ExportNamedTuple(src_code)\
                .handle_inheritance()\
                .handle_properties()\
                .generate_module(path)
    
