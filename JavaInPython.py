# Java pipeline called from python
import subprocess

JAVA_VERSION = "1.8"
AUTO_INSTALL = True
try:
    import jpype
    import jpype.imports
except (ModuleNotFoundError, ImportError):
    print("JPype not installed, please install JPype to use this feature.")
    if AUTO_INSTALL:
        import pip

        pip.main(['install', 'JPype1'])
        import jpype
        import jpype.imports
    else:
        raise ImportError("JPype not installed, please install JPype to use this feature.")

def toFunctionBlock(func, convert_table: dict = None, required_imports: dict = None):
    """
    Decorator for precompile function.
    func : python function with type annotations.
    If there is missing input / output type, it will be replaced with "Object".
    func() should return a code block for function.
    This function does not return class, it returns public static function that can be attached to class.
    """
    if convert_table is None:
        convert_table = {
            int: "int",
            float: "Double",
            str: "String",
            bool: "boolean",
            #"list": "ArrayList",
            #"dict": "HashMap",
            #"tuple": "Tuple",
            #"set": "HashSet",
            object: "Object",
            None : "void",
            "void" : "void"
        }
    if required_imports is None:
        required_imports = {
            "ArrayList": "java.util.ArrayList",
            "HashMap": "java.util.HashMap",
            "HashSet": "java.util.HashSet",
            "Tuple": "java.util.Tuple"
        }

        # TODO : add required imports

    def wrapper():
        annotations = func.__annotations__
        args = {}
        for argName, argType in annotations.items():
            if argName == "return":
                continue
            if argType is None:
                argType = "Object"
            elif argType not in convert_table:
                raise ValueError(f"Unsupported type {argType}")
            args[argName] = convert_table.get(argType, argType)
        return_type = annotations.get("return", "void")
        if return_type not in convert_table:
            raise ValueError(f"Unsupported type {return_type}")
        return_type = convert_table.get(return_type, return_type)
        code = func()
        return generateFunctionBlock(function_name=func.__name__, args=args, return_type=return_type, code=code)
    return wrapper

def precompile(filename, codeblock):
    # Write your Java code to a file
    with open(filename, 'w') as f:
        f.write(codeblock)
    if not jpype.isJVMStarted():
        jpype.startJVM(jpype.getDefaultJVMPath())
    # Compile your Java code using javac
    subprocess.check_call(['javac', '-source', JAVA_VERSION, '-target', JAVA_VERSION, filename])
    # Load your compiled Java class using JPype
    MyClass = jpype.JClass(filename[:-5])
    # We defined public class, so class defined inside codeblock must match with filename.
    return MyClass

def generateFunctionBlock(function_name: str = "exampleFunction", args: dict = None, return_type: str = "void",
                          code: str = None):
    """
    Generate code block for precompile function.
    :param function_name:
    :param args:
    :param return_type:
    :param code: code block for function
    :return:
    """
    if args is None:
        args = {}
    code_block = f"""
    public static {return_type} {function_name}({", ".join([f"{argType} {argName}" for argName, argType in args.items()])}) {{
        {code}
    }}
"""
    return code_block

def generateCodeBlock(function_name: str = "exampleFunction", args: dict = None, return_type: str = "void",
                      code: str = None, public_clsname: str = "Test", imports: list = None):
    """
    Generate code block for precompile function.
    """
    if args is None:
        args = {}
    code_block = f"""
    {" ".join([f"import {import_};" for import_ in imports])}
    
    public class {public_clsname} {{
        public static {return_type} {function_name}({", ".join([f"{argType} {argName}" for argName, argType in args.items()])}) {{
            {code}
        }}
    }}
    """
    return code_block

def generateClassWithFunctions(functions: list = None, public_clsname: str = "Test", imports: list = None):
    """
    Generate code block for precompile function.
    """
    if functions is None:
        functions = []
    if imports is None:
        imports = []
    code_block = f"""
    {" ".join([f"import {import_};" for import_ in imports])}
    
    public class {public_clsname} {{
        {" ".join(functions)}
    }}
    """
    return code_block

@toFunctionBlock
def countPrimes(start_number : int=0, end_number : int=0) -> int:
    code = f"""
    int count = 0;
    for (int i = start_number; i < end_number; i++) {{
        boolean isPrime = true;
        for (int j = 2; j < i; j++) {{
            if (i % j == 0) {{
                isPrime = false;
                break;
            }}
        }}
        if (isPrime) {{
            count++;
        }}
    }}
    return count;
    """
    return code  # You return string instead of annotated return type

@toFunctionBlock
def isPrime(number : int=0) -> bool:
    code = f"""
    boolean isPrime = true;
    for (int j = 2; j < number; j++) {{
        if (number % j == 0) {{
            isPrime = false;
            break;
        }}
    }}
    return isPrime;
    """
    return code

# TODO : decorator -> Java code block generator
if __name__ == "__main__":
    example_code = """
    public class Test {
        public static String substring(String targetString, int start) {
            return targetString.substring(start);
        }
    }
    """
    testClass = precompile('Test.java', example_code)
    print(testClass.substring("Hello World", 6))
    # prints World

    generatedCode = generateCodeBlock(function_name="substring", args={"targetString": "String", "start": "int"},
                                      return_type="String", code="return targetString.substring(start);",
                                      public_clsname="Test", imports=["java.lang.String"])
    testClass = precompile('Test.java', generatedCode)
    print(testClass.substring("Hello World", 6))
    # prints World
    functionClasses = generateClassWithFunctions(functions=[countPrimes(), isPrime()], public_clsname="TestPrimes")
    testClass = precompile('TestPrimes.java', functionClasses)
    print(testClass.countPrimes(2, 100))  # 25
    print(testClass.isPrime(101))  # True
