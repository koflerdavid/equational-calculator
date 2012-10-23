import functools
import itertools

def termsEqual(term1, term2):
    if not isinstance(term1, Term) or not isinstance(term2, Term):
        #raise TypeError("This function is only defined for terms")
        return False

    if isinstance(term1, Variable) and isinstance(term2, Variable):
        return term1.name == term2.name
    
    if isinstance(term1, Application) and isinstance(term2, Application):
        name_matches = term1.function_name == term1.function_name
        arguments_match = all(itertools.starmap(termsEqual(t1, t2),
                                        zip(term1.arguments, term2.arguments)))
    
        return name_matches and arguments_match
    
    return False

class Term(object):
    """Abstract base class for terms"""
    
    __eq__ = termsEqual
    
    def __init(self):
        pass
    
    def variables(self):
        raise NotImplementedError()
    
    def substitute(self, substitution):
        raise NotImplementedError()
    
    def __str__(self):
        raise NotImplementedError()

class Application(Term):
    """A class representing function symbols applied to a number of arguments"""

    def __init__(self, function_name, *arguments):
        self.function_name = function_name
        self.arguments = arguments
    
    def variables(self):
        return functool.reduce(set.update, self.arguments, set())
    
    def substitute(self, substitution):
        newArguments = map(lambda t: t.substitute(substitution), self.arguments)
        return Application(self.function_name, *newArguments)
    
    def __str__(self):
        if len(self.arguments) == 0:
            return self.function_name
        
        return "%s(%s)" % (self.function_name, ", ".join(map(str, self.arguments)))

class Variable(Term):
    """A class representing variables in terms."""
    
    def __init__(self, name):
        self.name = name
    
    def variables(self):
        return self.name
    
    def substitute(self, substitution):
        if self.name in substitution:
            return substitution[self.name]
        
        return Variable(self.name)
    
    def __str__(self):
        return ":%s" % self.name

def matchesSignature(term, signature):
    """A signature is a mapping from function symbols to their respective arities.
    An application consists of a function symbol applicated on some argument terms.
    This function checks whether all applications in a term take the right number of 
    arguments, as determined by the ."""

    if not isinstance(term, Term):
        raise TypeError("The term has to be a subclass of the class `Term`")

    if isinstance(term, Application):
        arity_right = len(term.arguments) == signature[term.function_name]
        return arity_right and all(map(lambda t: matchesSignature(t, signature), term.arguments))
    
    return True

