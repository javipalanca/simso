# -*- coding: utf-8 -*-
# Copyright (C) 2013, the codeeditor development team
#
# IEP is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

import re
from . import tokens, Parser, BlockState
from .tokens import ALPHANUM


# Import tokens in module namespace
from .tokens import (CommentToken, StringToken,
    UnterminatedStringToken, IdentifierToken, NonIdentifierToken,
    KeywordToken, NumberToken, FunctionNameToken, ClassNameToken,
    TodoCommentToken)

# Keywords sets

# Source: import keyword; keyword.kwlist (Python 2.6.6)
python2Keywords = set(['and', 'as', 'assert', 'break', 'class', 'continue',
        'def', 'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
        'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'not', 'or',
        'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield'])

# Source: import keyword; keyword.kwlist (Python 3.1.2)
python3Keywords = set(['False', 'None', 'True', 'and', 'as', 'assert', 'break',
        'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
        'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try', 'while',
        'with', 'yield'])

# Merge the two sets to get a general Python keyword list
pythonKeywords = python2Keywords | python3Keywords


def qstring_to_unicode(s):
    try:
        return unicode(s)
    except NameError:
        return s


class MultilineStringToken(StringToken):
    """ Characters representing a multi-line string. """
    defaultStyle = 'fore:#7F0000'

class CellCommentToken(CommentToken):
    """ Characters representing a cell separator comment: "##". """
    defaultStyle = 'bold:yes, underline:yes'



# This regexp is used to find special stuff, such as comments, numbers and
# strings.
tokenProg = re.compile(
    '#|' +						# Comment or
    '([' + ALPHANUM + '_]+)|' +	# Identifiers/numbers (group 1) or
    '(' +  						# Begin of string group (group 2)
    '([bB]|[uU])?' +			# Possibly bytes or unicode (py2.x)
    '[rR]?' +					# Possibly a raw string
    '("""|\'\'\'|"|\')' +		# String start (triple qoutes first, group 4)
    ')'							# End of string group
    )


#For a given type of string ( ', " , ''' , """ ),get  the RegExp
#program that matches the end. (^|[^\\]) means: start of the line
#or something that is not \ (since \ is supposed to escape the following
#quote) (\\\\)* means: any number of two slashes \\ since each slash will
#escape the next one
endProgs = {
    "'": re.compile(r"(^|[^\\])(\\\\)*'"),
    '"': re.compile(r'(^|[^\\])(\\\\)*"'),
    "'''": re.compile(r"(^|[^\\])(\\\\)*'''"),
    '"""': re.compile(r'(^|[^\\])(\\\\)*"""')
    }


class PythonParser(Parser):
    """ Parser for Python in general (2.x or 3.x).
    """
    _extensions = ['.py' , '.pyw']
    #The list of keywords is overridden by the Python2/3 specific parsers
    _keywords = pythonKeywords


    def _identifierState(self, identifier=None):
        """ Given an identifier returs the identifier state:
        3 means the current identifier can be a function.
        4 means the current identifier can be a class.
        0 otherwise.

        This method enables storing the state during the line,
        and helps the Cython parser to reuse the Python parser's code.
        """
        if identifier is None:
            # Explicit get/reset
            try:
                state = self._idsState
            except Exception:
                state = 0
            self._idsState = 0
            return state
        elif identifier == 'def':
            # Set function state
            self._idsState = 3
            return 3
        elif identifier == 'class':
            # Set class state
            self._idsState = 4
            return 4
        else:
            # This one can be func or class, next one can't
            state = self._idsState
            self._idsState = 0
            return state


    def parseLine(self, line, previousState=0):
        """ parseLine(line, previousState=0)

        Parse a line of Python code, yielding tokens.
        previousstate is the state of the previous block, and is used
        to handle line continuation and multiline strings.

        """

        # Init
        pos = 0 # Position following the previous match

        # identifierState and previousstate values:
        # 0: nothing special
        # 1: multiline comment single qoutes
        # 2: multiline comment double quotes
        # 3: a def keyword
        # 4: a class keyword

        #Handle line continuation after def or class
        #identifierState is 3 or 4 if the previous identifier was 3 or 4
        if previousState == 3 or previousState == 4:
            self._identifierState({3:'def',4:'class'}[previousState])
        else:
            self._identifierState(None)

        if previousState in [1,2]:
            token = MultilineStringToken(line, 0, 0)
            token._style = ['', "'''", '"""'][previousState]
            tokens = self._findEndOfString(line, token)
            # Process tokens
            for token in tokens:
                yield token
                if isinstance(token, BlockState):
                    return
            pos = token.end


        # Enter the main loop that iterates over the tokens and skips strings
        while True:

            # Get next tokens
            tokens = self._findNextToken(line, pos)
            if not tokens:
                return
            elif isinstance(tokens[-1], StringToken):
                moreTokens = self._findEndOfString(line, tokens[-1])
                tokens = tokens[:-1] + moreTokens

            # Process tokens
            for token in tokens:
                yield token
                if isinstance(token, BlockState):
                    return
            pos = token.end


    def _findEndOfString(self, line, token):
        """ _findEndOfString(line, token)

        Find the end of a string. Returns (token, endToken). The first
        is the given token or a replacement (UnterminatedStringToken).
        The latter is None, or the BlockState. If given, the line is
        finished.

        """

        # Set state
        self._identifierState(None)

        # Find the matching end in the rest of the line
        # Do not use the start parameter of search, since ^ does not work then
        style = token._style
        endMatch = endProgs[style].search(line[token.end:])

        if endMatch:
            # The string does end on this line
            tokenArgs = line, token.start, token.end + endMatch.end()
            if style in ['"""', "'''"]:
                token = MultilineStringToken(*tokenArgs)
            else:
                token.end += endMatch.end()
            return [token]
        else:
            # The string does not end on this line
            tokenArgs = line, token.start, token.end + len(line)
            if style == "'''":
                return [MultilineStringToken(*tokenArgs), BlockState(1)]
            elif style == '"""':
                return [MultilineStringToken(*tokenArgs), BlockState(2)]
            else:
                return [UnterminatedStringToken(*tokenArgs)]


    def _findNextToken(self, line, pos):
        """ _findNextToken(line, pos):

        Returns a token or None if no new tokens can be found.

        """

        line = qstring_to_unicode(line)

        # Init tokens, if pos too large, were done
        if pos > len(line):
            return None
        tokens = []

        # Find the start of the next string or comment
        match = tokenProg.search(line, pos)

        # Process the Non-Identifier between pos and match.start()
        # or end of line
        nonIdentifierEnd = match.start() if match else len(line)

        # Return the Non-Identifier token if non-null
        # todo: here it goes wrong (allow returning more than one token?)
        token = NonIdentifierToken(line,pos,nonIdentifierEnd)
        strippedNonIdentifier = str(token).strip()
        if token:
            tokens.append(token)

        # Do checks for line continuation and identifierState
        # Is the last non-whitespace a line-continuation character?
        if strippedNonIdentifier.endswith('\\'):
            lineContinuation = True
            # If there are non-whitespace characters after def or class,
            # cancel the identifierState
            if strippedNonIdentifier != '\\':
                self._identifierState(None)
        else:
            lineContinuation = False
            # If there are non-whitespace characters after def or class,
            # cancel the identifierState
            if strippedNonIdentifier != '':
                self._identifierState(None)

        # If no match, we are done processing the line
        if not match:
            if lineContinuation:
                tokens.append( BlockState(self._identifierState()) )
            return tokens

        # The rest is to establish what identifier we are dealing with

        # Comment
        if match.group() == '#':
            matchStart = match.start()
            if ( line[matchStart:].startswith('##') and
                    not line[:matchStart].strip() ):
                tokens.append( CellCommentToken(line,matchStart,len(line)) )
            elif self._isTodoItem(line[matchStart+1:]):
                tokens.append( TodoCommentToken(line,matchStart,len(line)) )
            else:
                tokens.append( CommentToken(line,matchStart,len(line)) )
            if lineContinuation:
                tokens.append( BlockState(self._identifierState()) )
            return tokens

        # If there are non-whitespace characters after def or class,
        # cancel the identifierState (this time, also if there is just a \
        # since apparently it was not on the end of a line)
        if strippedNonIdentifier != '':
            self._identifierState(None)

        # Identifier ("a word or number") Find out whether it is a key word
        if match.group(1) is not None:
            identifier = match.group(1)
            tokenArgs = line, match.start(), match.end()

            # Set identifier state
            identifierState = self._identifierState(identifier)

            if identifier in self._keywords:
                tokens.append( KeywordToken(*tokenArgs) )
            elif identifier[0] in '0123456789':
                self._identifierState(None)
                tokens.append( NumberToken(*tokenArgs) )
            else:
                if (identifierState==3 and
                        line[match.end():].lstrip().startswith('(') ):
                    tokens.append( FunctionNameToken(*tokenArgs) )
                elif identifierState==4:
                    tokens.append( ClassNameToken(*tokenArgs) )
                else:
                    tokens.append( IdentifierToken(*tokenArgs) )

        else:
            # We have matched a string-start
            # Find the string style ( ' or " or ''' or """)
            token = StringToken(line, match.start(), match.end())
            token._style = match.group(4) # The style is in match group 4
            tokens.append( token )

        # Done
        return tokens


class Python2Parser(PythonParser):
    """ Parser for Python 2.x code.
    """
     # The application should choose whether to set the Py 2 specific parser
    _extensions = []
    _keywords = python2Keywords

class Python3Parser(PythonParser):
    """ Parser for Python 3.x code.
    """
    # The application should choose whether to set the Py 3 specific parser
    _extensions = []
    _keywords = python3Keywords


if __name__=='__main__':
    print(list(tokenizeLine('this is "String" #Comment')))
    print(list(tokenizeLine('this is "String\' #Comment')))
    print(list(tokenizeLine('this is "String\' #Commen"t')))
    print(list(tokenizeLine(r'this "test\""')))

    import random
    stimulus=''
    expect=[]
    for i in range(10):
        #Create a string with lots of ' and "
        s=''.join("'\"\\ab#"[random.randint(0,5)] for i in range(10)  )
        stimulus+=repr(s)
        expect.append('S:'+repr(s))
        stimulus+='test'
        expect.append('I:test')
    result=list(tokenizeLine(stimulus))
    print (stimulus)
    print (expect)
    print (result)

    assert repr(result) == repr(expect)
