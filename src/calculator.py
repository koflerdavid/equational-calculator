import equations
import equationparser
import terms

import cmd
import functools
import shlex

class Calculator(cmd.Cmd):
    def __init__(self, stdin, stdout):
        cmd.Cmd.__init__(self, stdin=stdin, stdout=stdout)
        
        # Framework initialization
        self.prompt = "> "
        
        # Contains equations
        # TODO: Also store information about how the equations were generated.
        #  This is necessary to generate and print a proof tree
        self.equations = []
    
    def do_exit(self, arg):
        """Quit the calculator"""
        return True
    
    def do_enter(self, arg):
        """Enter terms to create new equations. Each two consecutive terms will form a new equation.
        
        > enter "*(e, :x)" :x e
        @1: *(e, :x) <=> :x
        -- There was a trailing term which was ignored
        -- Perhaps the right side of the equation is missing?
        > enter "*(-1(:x), :x)" e "*(*(:x, :y), :z)" "*(:x, *(:y, :z))"
        @2: (-1(:x), :x) <=> e
        @3: *(*(:x, :y), :z) <=> *(:x, *(:y, :z))
        """
        p = equationparser.Parser(arg)
        
        try:
            left = p.parseTerm(sourceMayEmpty=True)
            while left:
                right = p.parseTerm(sourceMayEmpty=True)
                if right:
                    self.addEquation((left, right))
                else:
                    self.printError("There was a trailing term which was ignored")
                    self.printError("Perhaps the right side of the equation is missing?")
                    break
                
                left = p.parseTerm(sourceMayEmpty=True)
                
        except equationparser.ParseError as e:
            self.printError(e)
    
    def do_reverse(self, arg):
        """Specify a number of equations which shall be reversed.
        
        > enter "*(e, :x)" ":x"
        @1: *(e, :x) <=> :x
        > reverse 1
        @2: :x <=> *(e, :x)
        > reverse 1 2
        @2: :x <=> *(e, :x)
        @1: *(e, :x) <=> :x
        """
        try:
            p = equationparser.Parser(arg)
            references = p.parseIntegerList(arg)
        except equationparser.ParseError as e:
            self.printError(e)
            return
        
        for index in references:
            equation = self.getEquation(index)
            if equation:
                self.addEquation(equations.employSymmetry(equation))
    
    def do_apply(self, arg):
        """Specify a number of equations and a function symbol. A new equation will be generated using the function symbol and the specified equations.
        
        > enter "*(e, :x)" ":x"
        @1: *(e, :x) <=> :x
        > enter "*(-1(:x), :x)" e
        @2: *(-1(:x), :x) <=> e
        > apply "t" @1 @2
        @3: t(*(e, :x), *(-1(:x), :x)) <=> t(:x, e)
        """
        try:
            p = parser.Parser(arg)
            name = p.parseFunctionSymbol(sourceMayEmpty=False)
            references = self.parseIntegerList()
        except equationparser.ParseError as e:
            self.printError(e)
            return
        
        equations_ = tuple(filter(bool, map(self.getEquation, references)))
        if len(equations_) != len(references):
            # In this case, some equations don't exist
            return
        
        self.addEquation(equations.employCongruence(name, *equations_))
    
    def do_self(self, arg):
        """Enter some terms. Then equations, stating that each of the specified terms is equal to itself, is generated.
        
        > self :x
        @1: :x <=> :x
        > self t(2) t(4)
        @2: t(2) <=> t(2)
        @3: t(4) <=> t(4)
        > enter "*(e, :x)" ":x"
        @4: *(e, :x) <=> :x
        > self @4
        @5: *(e, :x) <=> *(e, :x)
        @1: :x <=> :x
        > self @2
        @2: t(2) <=> t(2)
        """
        try:
            p = equationparser.Parser(arg)
            items = []
            item = p.parseTermOrReference(sourceMayEmpty=True)
            while item:
                items.append(item)
                item = p.parseTermOrReference(sourceMayEmpty=True)
        except equationparser.ParseError as e:
            self.printError(e)
            return
        
        for item in items:
            if isinstance(item, int):
                equation = self.getEquation(item)
                if not equation:
                    continue
                
                self.addEquation(equations.employReflexivity(equation[0]))
                self.addEquation(equations.employReflexivity(equation[1]))
                
            else:
                assert isinstance(item, terms.Term)
                self.addEquation(equations.employReflexivity(item))
    
    def do_subst(self, arg):
        """Select some equations and enter the substitution which shall be applied
        
        > enter "*(*(:x, :y), :z)" "*(:x, *(:y, :z))"
        @1: *(*(:x, :y), :z) <=> *(:x, *(:y, :z))
        > subst @1 x=e y=-(-e)
        @2: *(*(e, -(-e)), :z) <=> *(e, *(-(-e), :z))
        > subst @1 z="*(-(e), e)"
        @3: *(*(:x, :y), *(-(e), e)) <=> *(:x, *(:y, *(-(e), e)))
        > subst @2 z=*(-(e),e)
        @4: *(*(e, -(-e)), *(-(e), e)) <=> *(e, *(-(-e), *(-(e), e)))
        """
        try:
            p = equationparser.Parser(arg)
            references = p.parseReferences()
            equations_ = tuple(filter(bool, tuple(map(self.getEquation, references))))
            
            if len(references) != len(equations_):
                return
            
            pairs = [p.parseSubstitution(True)]
            while pair:
                #print(pair)
                pairs.append(p.parseSubstitution(True))
        
        except equationparser.ParseError as e:
            self.printError(e)
            return
        
        # Build the substitution.
        substitution = dict(pairs)
        
        for equation in equations_:
            equation = equations.employSubstitution(equation, substitution)
            self.addEquation(equation)

    def do_show(self, arg):
        """Display some or all known equations.
        
        > enter "*(e, :x)" :x
        @1: *(e, :x) <=> :x
        > enter "*(-1(:x), :x)" e "*(*(:x, :y), :z)" "*(:x, *(:y, :z))"
        @2: (-1(:x), :x) <=> e
        @3: *(*(:x, :y), :z) <=> *(:x, *(:y, :z))
        > show 1 @2
        @1: *(e, :x) <=> :x
        @2: (-1(:x), :x) <=> e
        > show
        -- Which equations shall be shown?
        -- Hint: > show all
        > show all
        @1: *(e, :x) <=> :x
        @2: (-1(:x), :x) <=> e
        @3: *(*(:x, :y), :z) <=> *(:x, *(:y, :z))"""
        
        if len(arg.strip()) == 0:
            self.printError("Which equations shall be shown?")
            self.printError("Hint: > show all")
            return
        
        indizes = []
        if arg.strip().lower() == 'all':
            indizes = range(1, len(self.equations)+1)
        else:
            try:
                p = equationparser.Parser(arg)
                indizes = p.parseReferences(arg)
            except equationparser.ParseError as e:
                self.printError(e)
                return
        
        for index in indizes:
            self.printEquation(index)
    
    def do_combine(self, arg):
        """Use transitivity to combine a number of equations.
        Adjacent sides of the specified equations have to match each other.
        
        > enter e "*(e, e)"
        @1: e <=> *(e, e)
        @2: *(-(e), e) <=> e
        > combine 2 1
        @3: *(-(e), e) <=> *(e, e)
        
        Future use case:
        > enter s(:y) :z :x 2
        @1: s(:y) <=> :y
        @2: :x <=> 2
        > combine 1 2
        @3: s(:x) <=> 2
        """
        try:
            p = equationparser.Parser(arg)
            references = p.parseReferences()
            if len(references) < 2:
                printError("Expected at least two references to equations")
                return
        except equationparser.ParseError as e:
            self.printError(e)
            return
        
        invalidReferences = filter(lambda i: i >= len(self.equations), references)
        if invalidReferences:
            self.printError("The following references are invalid: %s" % ", ".join(invalidReferences))
            return
        
        def combineEquations(left, right):
            pos, ok, left = left
            pos_plus_1, _, right = right
            
            if e1[1] != e2[0]:
                printError("Equations %d and %d don't have matching adjacent sides" % (pos, pos_plus_1))
                # The matching has to continue to spot other errors
                return (pos_plus_1, False, right)
            
            return pos_plus_1, ok , employTransitivity(left, right)
        
        data = zip(map(getEquation, references), repeat(True), count(1))
        
        # The equations will be combined from left to right.
        # If there are errors because of non-matching adjacent sides, False will be
        # passed through.
        result, ok, pos = functools.reduce(combineEquations, data)
        
        if ok:
            self.addEquation(result)
    
    def getEquation(self, index):
        try:
            return self.equations[index-1]
        except IndexError:
            self.printError("The referenced equation @%i doesn't exist" % index)
            return None
    
    def addEquation(self, equation):
        self.equations.append(equation)
        self.printEquation(len(self.equations))
        return len(self.equations)
    
    def printEquation(self, index):
        left, right = self.getEquation(index)
        print("@%d: %s <=> %s" % (index, left, right), file=self.stdout)
    
    def printError(self, message):
        print("-- %s" % message, file=self.stdout)

if __name__ == '__main__':
    import sys
    intro = """Welcome to the equational calculator. You may enter equations and use the inference rules of equational reasoning on them."""
    Calculator(sys.stdin, sys.stdout).cmdloop(intro)