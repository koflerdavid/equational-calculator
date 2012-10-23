import terms

import re

argumentSeparatorRegex = re.compile(r',\s*')
closingParentheseRegex = re.compile(r'\)\s*')
equalitySignRegex = re.compile(r'\s*=')
intRegex = re.compile(r'\s*(\d+)')
openingParentheseRegex = re.compile(r'\(\s*')
referenceRegex = re.compile(r'\s*@(\d+)')
symbolRegex = re.compile(r'([^,()\[\]\s]+)\s*')
variableRegex = re.compile(r':(\w+)\s*')
whitespaceRegex = re.compile(r'\s*')

class ParseError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class Parser(object):
    def __init__(self, src, begin=0):
        self.src = src
        self.pos = begin

    def parseTerm(self, sourceMayEmpty=False):
        self.pos = whitespaceRegex.match(self.src, self.pos).end()

        variableMatch = variableRegex.match(self.src, self.pos)
        if variableMatch:
            return self.parseVariable(False, variableMatch)
        
        symbolMatch = symbolRegex.match(self.src, self.pos)
        if symbolMatch:
            return self.parseApplication(False, symbolMatch)
        
        openingParentheseMatch = openingParentheseRegex.match(self.src, self.pos)
        if openingParentheseMatch:
            self.pos = openingParentheseMatch.end()
            term = self.parseTerm()
            
            closingParentheseMatch = closingParentheseRegex.match(self.src, self.pos)
            if not closingParentheseMatch:
                raise ParseError("Unexpected symbol at %i, expected a closing parenthese (\")\")" % self.pos)
        
            self.pos = closingParentheseMatch.end()
            return term
        
        if sourceMayEmpty:
            # The fact that there simply is nothing to parse shall be accepted.
            return None
        else:
            raise ParseError("Unexpected symbol at %i, expected a term" % self.pos)

    def parseApplication(self, sourceMayEmpty=False, symbolMatch=None):
        name = self.parseFunctionSymbol(sourceMayEmpty, symbolMatch)
        if not name:
            # The other case won't occur. In this case parseFunctionSymbol would already have thrown a ParseException
            assert sourceMayEmpty
            return None
        
        openingParentheseMatch = openingParentheseRegex.match(self.src, self.pos)
        if not openingParentheseMatch:
            # A function symbol with arity 0 doesn't necessarily has to be followed
            # by an argument list.
            self.pos = symbolMatch.end()
            return terms.Application(name)
        
        self.pos = openingParentheseMatch.end()
        closingParentheseMatch = closingParentheseRegex.match(self.src, self.pos)
        
        arguments = []
        while not closingParentheseMatch:
            term = self.parseTerm(sourceMayEmpty=False)
            arguments.append(term)
            
            # Parse either an argument separator or a closing parenthese.
            # If both cannot be found, raise a syntax error.
            argumentSeparatorMatch = argumentSeparatorRegex.match(self.src, self.pos)
            if not argumentSeparatorMatch:
                closingParentheseMatch = closingParentheseRegex.match(self.src, self.pos)
                if not closingParentheseMatch:
                    raise ParseError("Unexpected symbol at %i, expected either an argument separator (\",\") or a closing parenthese (\")\")" % self.pos)
                else:
                    self.pos = closingParentheseMatch.end()
            else:
                self.pos = argumentSeparatorMatch.end()
        
        return terms.Application(name, *arguments)

    def parseVariable(self, sourceMayEmpty=False, variableMatch=None):
        if not variableMatch:
            variableMatch = variableRegex.match(self.src, self.pos)
            
            if not variableMatch:
                if sourceMayEmpty:
                    return None
                else:
                    raise ParseError("Unexpected symbol at %i, expected a variable (a \":\" followed by some word characters)" % self.pos)

        self.pos = variableMatch.end(1)
        return terms.Variable(variableMatch.group(1))

    def parseFunctionSymbol(self, sourceMayEmpty=False, symbolMatch=None):
        if not symbolMatch:
            symbolMatch = symbolRegex.match(self.src, self.pos)
            
            if not symbolMatch:
                if sourceMayEmpty:
                    return None
                else:
                    raise ParseError("Unexpected symbol at %i, expected a function symbol." % self.pos)
        
        self.pos = symbolMatch.end()
        return symbolMatch.group(1)
    
    def parseReference(self, sourceMayEmpty=False):
        referenceMatch = referenceRegex.match(self.src, self.pos)
        if not referenceMatch:
            if sourceMayEmpty:
                return None
            else:
                raise ParseError("Expected a reference, beginning with an \"@\"")
        
        self.pos = referenceMatch.end()
        return int(referenceMatch.group(1))

    def parseInt(self):
        self.pos = whitespaceRegex.match(self.src, self.pos).end()
        
        intMatch = intRegex.match(self.src, self.pos)
        if not intMatch:
            return None
        else:
            self.pos = intMatch.end()
            return int(intMatch.group(1))
    
    def parseIntegerList(self):
        references = []
        result = self.parseInt()
        while result:
            references.append(result)
            result = self.parseInt()
        
        return references

    def parseSubstitution(self, sourceMayEmpty=False):
        variable = self.parseVariable(sourceMayEmpty)
        if not variable:
            # The other case doesn't occur. parseVariable would already have thrown an exception
            assert sourceMayEmpty
            return None
        
        equalitySignMatch = equalitySignRegex.match(self.src, self.pos)
        if not equalitySignMatch:
            raise ParseError("Expected an equality sign at %i (after the variable name)" % self.pos)
        
        self.pos = equalitySignMatch.end()
        term = terms.parser.parseTerm(False)
        return (variable.name, term)

    def parseTermOrReference(self, sourceMayEmpty=False):
        reference = parseReference(True)
        if not reference:
            return self.parseTerm(sourceMayEmpty)
        return reference