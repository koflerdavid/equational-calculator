"""An equation is represented by a pair of terms"""

import terms

def unzip(iterable):
    def firsts():
        for t in iterable:
            yield t[0]
    
    def seconds():
        for t in iterable:
            yield t[1]

    return firsts(), seconds()

class EqualityError(Exception):
    def __init__(self):
        Exception.__init__(self, "The terms are not equal")

def employReflexivity(term):
    return (term, term)

def employSymmetry(equation):
    return (equation[1], equation[0])

def employTransitivity(equation1, equation2):
    term1, left = equation1
    right, term2 = equation2

    if left == right:
        return (term1, term2)
    else:
        raise EqualityError()

def employCongruence(function_name, *equations):
    firsts, seconds = unzip(equations)
    
    left = terms.Applications(function_name, *firsts)
    rights = terms.Applications(function_name, *seconds)
    
    return left, right

def employSubstitution(equation, substitution):
    return equation[0].substitute(substitution), equation[1].substitute(substitution)