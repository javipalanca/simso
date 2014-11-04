# -*- coding: utf-8 -*-
# Copyright (C) 2013, the codeeditor development team
#
# IEP is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

"""
Code editor extensions that change its appearance
"""

from ..qt import QtGui,QtCore
Qt = QtCore.Qt

from ..misc import ce_option
from ..manager import Manager

# todo: what about calling all extensions. CE_HighlightCurrentLine, 
# or EXT_HighlightcurrentLine?

class HighlightCurrentLine(object):
    """
    Highlight the current line
    """
    
    # Register style element
    _styleElements = [  (   'Editor.Highlight current line',
                            'The background color of the current line highlight.',
                            'back:#ffff99', 
                        ) ]
    
    def highlightCurrentLine(self):
        """ highlightCurrentLine()
        
        Get whether to highlight the current line.
        
        """
        return self.__highlightCurrentLine
    
    @ce_option(True)
    def setHighlightCurrentLine(self,value):
        """ setHighlightCurrentLine(value)
        
        Set whether to highlight the current line.  
        
        """
        self.__highlightCurrentLine = bool(value)
        self.viewport().update()
    
    
    def paintEvent(self,event):
        """ paintEvent(event)
        
        Paints a rectangle spanning the current block (in case of line wrapping, this
        means multiple lines)
        
        Paints behind its super()
        """
        if not self.highlightCurrentLine():
            super(HighlightCurrentLine, self).paintEvent(event)
            return
        
        # Get color
        color = self.getStyleElementFormat('editor.highlightCurrentLine').back
        
        #Find the top of the current block, and the height
        cursor = self.textCursor()
        cursor.movePosition(cursor.StartOfBlock)
        top = self.cursorRect(cursor).top()
        cursor.movePosition(cursor.EndOfBlock)
        height = self.cursorRect(cursor).bottom() - top + 1
        
        margin = self.document().documentMargin()
        painter = QtGui.QPainter()
        painter.begin(self.viewport())
        painter.fillRect(QtCore.QRect(margin, top, 
            self.viewport().width() - 2*margin, height),
            color)
        painter.end()
        
        super(HighlightCurrentLine, self).paintEvent(event)
        
        # for debugging paint events
        #if 'log' not in self.__class__.__name__.lower():
        #    print(height, event.rect().width())


class IndentationGuides(object):
    
    # Register style element
    _styleElements = [  (   'Editor.Indentation guides',
                            'The color and style of the indentation guides.',
                            'fore:#DDF,linestyle:solid', 
                        ) ]
    
    def showIndentationGuides(self):
        """ showIndentationGuides()
        
        Get whether to show indentation guides. 
        
        """
        return self.__showIndentationGuides
    
    @ce_option(True)
    def setShowIndentationGuides(self, value):
        """ setShowIndentationGuides(value)
        
        Set whether to show indentation guides.
        
        """
        self.__showIndentationGuides = bool(value)
        self.viewport().update() 
    
    
    def paintEvent(self,event):
        """ paintEvent(event)
        
        Paint the indentation guides, using the indentation info calculated
        by the highlighter.
        """ 
        super(IndentationGuides, self).paintEvent(event)

        if not self.showIndentationGuides():
            return
        
        # Get doc and viewport
        doc = self.document()
        viewport = self.viewport()
        
        # Get multiplication factor and indent width
        indentWidth = self.indentWidth()
        if self.indentUsingSpaces():
            factor = 1 
        else:
            factor = indentWidth
        
        # Init painter
        painter = QtGui.QPainter()
        painter.begin(viewport)
        
        # Prepare pen
        format = self.getStyleElementFormat('editor.IndentationGuides')
        pen = QtGui.QPen(format.fore)
        pen.setStyle(format.linestyle)
        painter.setPen(pen)
        offset = doc.documentMargin() + self.contentOffset().x()
        
        def paintIndentationGuides(cursor):
            y3=self.cursorRect(cursor).top()
            y4=self.cursorRect(cursor).bottom()            
            
            bd = cursor.block().userData()            
            if bd and hasattr(bd, 'indentation') and bd.indentation:
                for x in range(indentWidth, bd.indentation * factor, indentWidth):
                    w = self.fontMetrics().width('i'*x) + offset
                    w += 1 # Put it more under the block
                    if w > 0: # if scrolled horizontally it can become < 0
                        painter.drawLine(QtCore.QLine(w, y3, w, y4))
 
        self.doForVisibleBlocks(paintIndentationGuides)
        
        # Done
        painter.end()



class FullUnderlines(object):
    
    def paintEvent(self,event):
        """ paintEvent(event)
        
        Paint a horizontal line for the blocks for which there is a
        syntax format that has underline:full. Whether this is the case
        is stored at the blocks user data.
        
        """ 
        super(FullUnderlines, self).paintEvent(event)
   
        painter = QtGui.QPainter()
        painter.begin(self.viewport())
 
        margin = self.document().documentMargin()
        w = self.viewport().width()
   
        def paintUnderline(cursor):
            y = self.cursorRect(cursor).bottom() 

            bd = cursor.block().userData()            
            try:
                fullUnderlineFormat = bd.fullUnderlineFormat
            except AttributeError:
                pass  # fullUnderlineFormat may not be an attribute
            else:
                if fullUnderlineFormat is not None:
                    # Apply pen
                    pen = QtGui.QPen(fullUnderlineFormat.fore)
                    pen.setStyle(fullUnderlineFormat.linestyle)
                    painter.setPen(pen)
                    # Paint
                    painter.drawLine(QtCore.QLine(margin, y, w - 2*margin, y))            
        
        self.doForVisibleBlocks(paintUnderline)
        
        painter.end()



class CodeFolding(object):
    def paintEvent(self,event):
        """ paintEvent(event)
        
        """ 
        super(CodeFolding, self).paintEvent(event)
   
        return # Code folding code is not yet complete
   
        painter = QtGui.QPainter()
        painter.begin(self.viewport())
 
        margin = self.document().documentMargin()
        w = self.viewport().width()
   
   
        def paintCodeFolders(cursor):
            y = self.cursorRect(cursor).top() 
            h = self.cursorRect(cursor).height()
            rect = QtCore.QRect(margin, y, h, h)
            text = cursor.block().text()           
            if text.rstrip().endswith(':'):
                painter.drawRect(rect)
                painter.drawText(rect, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter, "-")
                # Apply pen
                
                # Paint
                #painter.drawLine(QtCore.QLine(margin, y, w - 2*margin, y))            
            
        self.doForVisibleBlocks(paintCodeFolders)
        
        painter.end()
        


class LongLineIndicator(object):
    
    # Register style element
    _styleElements = [  (   'Editor.Long line indicator',
                            'The color and style of the long line indicator.',
                            'fore:#BBB,linestyle:solid', 
                        ) ]
    
    def longLineIndicatorPosition(self):
        """ longLineIndicatorPosition()
        
        Get the position of the long line indicator (aka edge column).
        A value of 0 or smaller means that no indicator is shown.
        
        """
        return self.__longLineIndicatorPosition
    
    @ce_option(80)
    def setLongLineIndicatorPosition(self, value):
        """ setLongLineIndicatorPosition(value)
        
        Set the position of the long line indicator (aka edge column).
        A value of 0 or smaller means that no indicator is shown.
        
        """ 
        self.__longLineIndicatorPosition = int(value)
        self.viewport().update()
    
    
    def paintEvent(self, event):    
        """ paintEvent(event)
        
        Paint the long line indicator. Paints behind its super()
        """    
        if self.longLineIndicatorPosition()<=0:
            super(LongLineIndicator, self).paintEvent(event)
            return
            
        # Get doc and viewport
        doc = self.document()
        viewport = self.viewport()

        # Get position of long line
        fm = self.fontMetrics()
        # width of ('i'*length) not length * (width of 'i') b/c of
        # font kerning and rounding
        x = fm.width('i' * self.longLineIndicatorPosition())
        x += doc.documentMargin() + self.contentOffset().x()
        x += 1 # Move it a little next to the cursor
        
        # Prepate painter
        painter = QtGui.QPainter()
        painter.begin(viewport)
        
        # Prepare pen
        format = self.getStyleElementFormat('editor.LongLineIndicator')
        pen = QtGui.QPen(format.fore)
        pen.setStyle(format.linestyle)
        painter.setPen(pen)
        
        # Draw line and end painter
        painter.drawLine(QtCore.QLine(x, 0, x, viewport.height()) )
        painter.end()
        
        # Propagate event
        super(LongLineIndicator, self).paintEvent(event)




class ShowWhitespace(object):
    
    def showWhitespace(self):
        """Show or hide whitespace markers"""
        option=self.document().defaultTextOption()
        return bool(option.flags() & option.ShowTabsAndSpaces)
    
    @ce_option(False)
    def setShowWhitespace(self,value):
        option=self.document().defaultTextOption()
        if value:
            option.setFlags(option.flags() | option.ShowTabsAndSpaces)
        else:
            option.setFlags(option.flags() & ~option.ShowTabsAndSpaces)
        self.document().setDefaultTextOption(option)


class ShowLineEndings(object):
    
    @ce_option(False)
    def showLineEndings(self):
        """ Get whether line ending markers are shown. 
        """
        option=self.document().defaultTextOption()
        return bool(option.flags() & option.ShowLineAndParagraphSeparators)
    
    
    def setShowLineEndings(self,value):
        option=self.document().defaultTextOption()
        if value:
            option.setFlags(option.flags() | option.ShowLineAndParagraphSeparators)
        else:
            option.setFlags(option.flags() & ~option.ShowLineAndParagraphSeparators)
        self.document().setDefaultTextOption(option)



class LineNumbers(object):
    
    # Margin on both side of the line numbers
    _LineNumberAreaMargin = 3
    
    # Register style element
    _styleElements = [  (   'Editor.Line numbers',
                            'The text- and background-color of the line numbers.',
                            'fore:#222,back:#DDD', 
                        ) ]
    
    class __LineNumberArea(QtGui.QWidget):
        """ This is the widget reponsible for drawing the line numbers.
        """
        
        def __init__(self, codeEditor):
            QtGui.QWidget.__init__(self, codeEditor)
            self.setCursor(QtCore.Qt.PointingHandCursor)
            self._pressedY = None
            self._lineNrChoser = None
        
        def _getY(self, pos):
            tmp = self.mapToGlobal(pos)
            return self.parent().viewport().mapFromGlobal(tmp).y()
        
        def mousePressEvent(self, event):
            self._pressedY = self._getY(event.pos())
        
        def mouseReleaseEvent(self, event):
            self._handleWholeBlockSelection( self._getY(event.pos()) )
        
        def mouseMoveEvent(self, event):
            self._handleWholeBlockSelection( self._getY(event.pos()) )
            
        def _handleWholeBlockSelection(self, y2):
            # Get y1 and sort (y1, y2)
            y1 = self._pressedY
            if y1 is None: y1 = y2
            y1, y2 = min(y1, y2), max(y1, y2)
            
            # Get cursor and two cursors corresponding to selected blocks
            editor = self.parent()
            cursor = editor.textCursor()
            c1 = editor.cursorForPosition(QtCore.QPoint(0,y1))
            c2 = editor.cursorForPosition(QtCore.QPoint(0,y2))
            
            # Make these two cursors select the whole block
            c1.movePosition(c1.StartOfBlock, c1.MoveAnchor)
            c2.movePosition(c2.EndOfBlock, c2.MoveAnchor)
            
            # Apply selection
            cursor.setPosition(c1.position(), cursor.MoveAnchor)
            cursor.setPosition(c2.position(), cursor.KeepAnchor)
            editor.setTextCursor(cursor)
        
        def mouseDoubleClickEvent(self, event):
            self.showLineNumberChoser()
        
        def showLineNumberChoser(self):
            # Create line number choser if needed
            if self._lineNrChoser is None:
                self._lineNrChoser = LineNumbers.LineNumberChoser(self.parent())
            # Get editor and cursor
            editor = self.parent()
            cursor = editor.textCursor()
            # Get (x,y) pos and apply
            x, y = self.width()+4, editor.cursorRect(cursor).y()
            self._lineNrChoser.move(QtCore.QPoint(x,y))
            # Show/reset line number choser
            self._lineNrChoser.reset(cursor.blockNumber()+1)
        
        def paintEvent(self, event):
            editor = self.parent()
            
            if not editor.showLineNumbers():
                return
            
            # Get doc and viewport
            doc = editor.document()
            viewport = editor.viewport()
            
            # Get format and margin
            format = editor.getStyleElementFormat('editor.LineNumbers')
            margin = editor._LineNumberAreaMargin
            
            # Init painter
            painter = QtGui.QPainter()
            painter.begin(self)
            
            # Get which part to paint. Just do all to avoid glitches
            w = editor.getLineNumberAreaWidth()
            y1, y2 = 0, editor.height()
            #y1, y2 = event.rect().top()-10, event.rect().bottom()+10
    
            # Get offset        
            tmp = self.mapToGlobal(QtCore.QPoint(0,0))
            offset = viewport.mapFromGlobal(tmp).y()
            
            #Draw the background        
            painter.fillRect(QtCore.QRect(0, y1, w, y2), format.back)
            
            # Get cursor
            cursor = editor.cursorForPosition(QtCore.QPoint(0,y1))
            
            # Prepare fonts
            font1 = editor.font()
            font2 = editor.font()
            font2.setBold(True)
            currentBlockNumber = editor.textCursor().block().blockNumber()
            
            # Init painter with font and color
            painter.setFont(font1)
            painter.setPen(format.fore)
            
            #Repainting always starts at the first block in the viewport,
            #regardless of the event.rect().y(). Just to keep it simple
            while True:
                blockNumber = cursor.block().blockNumber()
                
                y = editor.cursorRect(cursor).y()
                
                # Set font to bold if line number is the current
                if blockNumber == currentBlockNumber:
                    painter.setFont(font2)
                
                painter.drawText(0, y-offset, w-margin, 50,
                    Qt.AlignRight, str(blockNumber+1))
                
                # Set font back
                if blockNumber == currentBlockNumber:
                    painter.setFont(font1)
                
                if y>y2:
                    break #Reached end of the repaint area
                if not cursor.block().next().isValid():
                    break #Reached end of the text
                
                cursor.movePosition(cursor.NextBlock)
            
            # Done
            painter.end()
    
    class LineNumberChoser(QtGui.QSpinBox):
        def __init__(self, parent):
            QtGui.QSpinBox.__init__(self, parent)
            
            self._editor = parent
            
            ss = "QSpinBox { border: 2px solid #789; border-radius: 3px; padding: 4px; }"
            self.setStyleSheet(ss)
            
            self.setPrefix('Go to line: ')
            self.setAccelerated (True)
            self.setButtonSymbols(self.NoButtons)
            self.setCorrectionMode(self.CorrectToNearestValue)
            
            # Signal for when value changes, and flag to disbale it once
            self._ignoreSignalOnceFlag = False
            self.valueChanged.connect(self.onValueChanged)
        
        def reset(self, currentLineNumber):
            # Set value to (given) current line number
            self._ignoreSignalOnceFlag = True
            self.setRange(1, self._editor.blockCount())
            self.setValue(currentLineNumber)
            # Select text and focus so that the user can simply start typing
            self.selectAll()
            self.setFocus()
            # Make visible
            self.show()
            self.raise_()
        
        def focusOutEvent(self, event):
            self.hide()
        
        def keyPressEvent(self, event):
            if event.key() in [QtCore.Qt.Key_Escape, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
                self._editor.setFocus() # Moves focus away, thus hiding self
            else:
                QtGui.QSpinBox.keyPressEvent(self, event)
        
        def onValueChanged(self, nr):
            if self._ignoreSignalOnceFlag:
                self._ignoreSignalOnceFlag = False
            else:
                self._editor.gotoLine(nr)
    
    def __init__(self, *args, **kwds):
        self.__lineNumberArea = None
        super(LineNumbers, self).__init__(*args, **kwds)
        # Create widget that draws the line numbers
        self.__lineNumberArea = self.__LineNumberArea(self)
        # Issue an update when the font or amount of line numbers changes
        self.blockCountChanged.connect(self.__onBlockCountChanged)
        self.fontChanged.connect(self.__onBlockCountChanged)
        self.__onBlockCountChanged()
        self.addLeftMargin(LineNumbers, self.getLineNumberAreaWidth)
    
    
    def gotoLinePopup(self):
        """ Popup the little widget to quickly goto a certain line.
        Can also be achieved by double-clicking the line number area.
        """
        self.__lineNumberArea.showLineNumberChoser()
    
    def showLineNumbers(self):
        return self.__showLineNumbers
    
    @ce_option(True)
    def setShowLineNumbers(self, value):
        self.__showLineNumbers = bool(value)
        # Note that this method is called before the __init__ is finished,
        # so that the __lineNumberArea is not yet created.
        if self.__lineNumberArea:
            if self.__showLineNumbers:
                self.__onBlockCountChanged()
                self.__lineNumberArea.show()
            else:
                self.__lineNumberArea.hide()
            self.updateMargins()
    
    
    def getLineNumberAreaWidth(self):
        """
        Count the number of lines, compute the length of the longest line number
        (in pixels)
        """
        if not self.__showLineNumbers:
            return 0
        lastLineNumber = self.blockCount() 
        margin = self._LineNumberAreaMargin
        return self.fontMetrics().width(str(lastLineNumber)) + 2*margin
    
    
    def __onBlockCountChanged(self,count=None):
        """
        Update the line number area width. This requires to set the 
        viewport margins, so there is space to draw the linenumber area
        """
        if self.__showLineNumbers:
            self.updateMargins()
    
    
    def resizeEvent(self,event):
        super(LineNumbers, self).resizeEvent(event)
        
        #On resize, resize the lineNumberArea, too
        rect=self.contentsRect()
        m = self.getLeftMargin(LineNumbers)
        w = self.getLineNumberAreaWidth()
        self.__lineNumberArea.setGeometry(  rect.x()+m, rect.y(),
                                            w, rect.height())
    
    def paintEvent(self,event):
        super(LineNumbers, self).paintEvent(event)
        #On repaint, update the complete line number area
        w = self.getLineNumberAreaWidth()
        self.__lineNumberArea.update(0, 0, w, self.height() )



class BreakPoints(object):
    
    _breakPointWidth = 11  # With of total bar, actual points are smaller
    
    # Register style element
    _styleElements = [  (   'Editor.BreakPoints',
                            'The fore- and background-color of the breakpoints.',
                            'fore:#F66,back:#EEE', 
                        ) ]
    
    class __BreakPointArea(QtGui.QWidget):
        """ This is the widget reponsible for drawing the break points.
        """
        
        def __init__(self, codeEditor):
            QtGui.QWidget.__init__(self, codeEditor)
            self.setCursor(QtCore.Qt.PointingHandCursor)
        
        def _getY(self, pos):
            tmp = self.mapToGlobal(pos)
            return self.parent().viewport().mapFromGlobal(tmp).y()
        
        def mousePressEvent(self, event):
            self._toggleBreakPoint( self._getY(event.pos()))
        
        def _toggleBreakPoint(self, y):
            # Get breakpoint corresponding to pressed pos
            editor = self.parent()
            cursor = editor.textCursor()
            c1 = editor.cursorForPosition(QtCore.QPoint(0,y))
            linenr = c1.blockNumber() + 1
            
            # Toggle
            bps = self.parent()._breakPoints
            if linenr in bps:
                bps.discard(linenr)
            else:
                bps.add(linenr)
            
            # Emit signal
            editor.breakPointsChanged.emit(editor)
            self.update()
        
        def paintEvent(self, event):
            editor = self.parent()
            
            if not editor.showBreakPoints():
                return
            
            # Get doc and viewport
            doc = editor.document()
            viewport = editor.viewport()
            
            # Get format and margin
            format = editor.getStyleElementFormat('editor.breakpoints')
            margin = 1
            w = editor._breakPointWidth
            bulletWidth = w - 2*margin
            
            # Init painter
            painter = QtGui.QPainter()
            painter.begin(self)
            
            # Get which part to paint. Just do all to avoid glitches
            y1, y2 = 0, editor.height()
            
            # Get offset        
            tmp = self.mapToGlobal(QtCore.QPoint(0,0))
            offset = viewport.mapFromGlobal(tmp).y()
            
            #Draw the background        
            painter.fillRect(QtCore.QRect(0, y1, w, y2), format.back)
            
            # Get debug indicator and list of sorted breakpoints
            debugBlockIndicator = editor._debugLineIndicator-1
            blocknumbers = [i-1 for i in sorted(self.parent()._breakPoints)]
            if not (blocknumbers or debugBlockIndicator > 0):
                return
            if not blocknumbers:  blocknumbers.append(-1)  # Safes a test below
            
            # Get cursor
            cursor = editor.cursorForPosition(QtCore.QPoint(0,y1))
            
            # Init painter with font and color
            painter.setPen(QtGui.QColor('#777'))
            painter.setBrush(format.fore)
            painter.setRenderHint(painter.Antialiasing)
            
            
            #Repainting always starts at the first block in the viewport,
            #regardless of the event.rect().y(). Just to keep it simple
            while True:
                blockNumber = cursor.block().blockNumber()
                
                # Done?
                if blockNumber > blocknumbers[-1] and blockNumber > debugBlockIndicator:
                    break
                if not cursor.block().next().isValid():
                    break #Reached end of the text
                
                # Draw
                if blockNumber in blocknumbers:
                    y = editor.cursorRect(cursor).center().y()
                    y -= bulletWidth * 0.5
                    painter.drawEllipse(margin, y, bulletWidth, bulletWidth)
                if blockNumber == debugBlockIndicator:
                    y = editor.cursorRect(cursor).center().y()
                    y -= bulletWidth * 0.25
                    painter.setBrush(QtGui.QColor('#6F6'))
                    #painter.drawRect(margin, y, bulletWidth, 0.5*bulletWidth)
                    painter.drawEllipse(margin, y, bulletWidth, 0.5*bulletWidth)
                    painter.setBrush(format.fore)
                
                cursor.movePosition(cursor.NextBlock)
            
            # Done
            painter.end()
    
    
    def __init__(self, *args, **kwds):
        self.__breakPointArea = None
        super(BreakPoints, self).__init__(*args, **kwds)
        # Create widget that draws the breakpoints
        self.__breakPointArea = self.__BreakPointArea(self)
        self.addLeftMargin(BreakPoints, self.getBreakPointAreaWidth)
        self._breakPoints = set()
        self._debugLineIndicator = 0
    
    
    def breakPoints(self):
        """ A list of breakpoints for this editor.
        """
        return list(sorted(self._breakPoints))
    
    
    def clearBreakPoints(self):
        """ Remove all breakpoints for this editor.
        """
        self._breakPoints = set()
        self.breakPointsChanged.emit(self)
    
    
    def setDebugLineIndicator(self, linenr):
        """ Set the debug line indicator to the given line number.
        If None or 0, the indicator is hidden.
        """
        linenr = int(linenr or 0)
        if linenr != self._debugLineIndicator:
            self._debugLineIndicator = linenr
            self.__breakPointArea.update()
    
    
    def getBreakPointAreaWidth(self):
        if not self.__showBreakPoints:
            return 0
        else:
            return self._breakPointWidth
    
    
    def showBreakPoints(self):
        return self.__showBreakPoints
    
    @ce_option(True)
    def setShowBreakPoints(self, value):
        self.__showBreakPoints = bool(value)
        # Note that this method is called before the __init__ is finished,
        # so that the area is not yet created.
        if self.__breakPointArea:
            if self.__showBreakPoints:
                self.__breakPointArea.show()
            else:
                self.__breakPointArea.hide()
                self.clearBreakPoints()
            self.updateMargins()
    
    
    def resizeEvent(self,event):
        super(BreakPoints, self).resizeEvent(event)
        
        #On resize, resize the breakpointArea, too
        rect=self.contentsRect()
        m = self.getLeftMargin(BreakPoints)
        w = self.getBreakPointAreaWidth()
        self.__breakPointArea.setGeometry(  rect.x()+m, rect.y(),
                                            w, rect.height())
    
    def paintEvent(self,event):
        super(BreakPoints, self).paintEvent(event)
        #On repaint, update the complete breakPointArea
        w = self.getBreakPointAreaWidth()
        self.__breakPointArea.update(0, 0, w, self.height() )



class Wrap(object):
    
    def wrap(self):
        """Enable or disable wrapping"""
        option=self.document().defaultTextOption()
        return not bool(option.wrapMode() == option.NoWrap)
    
    @ce_option(True)
    def setWrap(self,value):
        option=self.document().defaultTextOption()
        if value:
            option.setWrapMode(option.WrapAtWordBoundaryOrAnywhere)
        else:
            option.setWrapMode(option.NoWrap)
        self.document().setDefaultTextOption(option)


# todo: move this bit to base class? 
# This functionality embedded in the highlighter and even has a designated
# subpackage. I feel that it should be a part of the base editor.
# Note: if we do this, remove the hasattr call in the highlighter.
class SyntaxHighlighting(object):
    """ Notes on syntax highlighting.

    The syntax highlighting/parsing is performed using three "components".
    
    The base component are the token instances. Each token simply represents
    a row of characters in the text the belong to each-other and should
    be styled in the same way. There is a token class for each particular
    "thing" in the code, such as comments, strings, keywords, etc. Some
    tokens are specific to a particular language.
    
    There is a function that produces a set of tokens, when given a line of
    text and a state parameter. There is such a function for each language.
    These "parsers" are defined in the parsers subpackage.
    
    And lastly, there is the Highlighter class, that applies the parser function
    to obtain the set of tokens and using the names of these tokens applies
    styling. The styling can be defined by giving a dict that maps token names
    to style representations.
    
    """
    
    # Register all syntax style elements
    _styleElements = Manager.getStyleElementDescriptionsForAllParsers() 
    
    def parser(self):
        """ parser()
        
        Get the parser instance currently in use to parse the code for 
        syntax highlighting and source structure. Can be None.
        
        """
        try:
            return self.__parser
        except AttributeError:
            return None
    
    
    @ce_option(None)
    def setParser(self, parserName=''):
        """ setParser(parserName='')
        
        Set the current parser by giving the parser name.
        
        """
        # Set parser
        self.__parser = Manager.getParserByName(parserName)

        # Restyle, use setStyle for lazy updating
        self.setStyle()
        
