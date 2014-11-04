# -*- coding: utf-8 -*-
# Copyright (C) 2013, the codeeditor development team
#
# Codeeditor is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

""" Module manager

This module contains a static class that can be used for some
management tasks.

"""

import os, sys

from .qt import QtGui, QtCore
Qt = QtCore.Qt

from . import parsers


class Manager:
    """ Manager
    
    Static class to do some management tasks:
      * It manages the parsers
      * Getting style element descriptions of all parsers
      * Linking file extensions to parsers
      * Font information
    
    """
    
    _defaultFontFamily = 'dummy_font_family_name'
    
    # Static dict of all parsers
    _parserInstances = {}
    _fileExtensions = {}
    
    ## Parsers
    
#     @classmethod
#     def collectParsersDynamically(cls):
#         """ insert the function is this module's namespace.
#         """
#         
#         # Get the path of this subpackage
#         path = __file__
#         path = os.path.dirname( os.path.abspath(path) )
#         
#         # Determine if we're in a zipfile
#         i = path.find('.zip')
#         if i>0:
#             # get list of files from zipfile
#             path = path[:i+4]
#             z = zipfile.ZipFile(path)
#             files = [os.path.split(i)[-1] for i in z.namelist() 
#                         if 'codeeditor' in i and 'parsers' in i]
#         else:
#             # get list of files from file system
#             files = os.listdir(path)
#         
#         # Extract all parsers
#         parserModules = []
#         for file in files:            
#             
#             # Only python files
#             if file.endswith('.pyc'):
#                 if file[:-1] in files:
#                     continue # Only try import once
#             elif not file.endswith('.py'):
#                 continue    
#             # Only syntax files
#             if '_parser.' not in file:
#                 continue
#             
#             # Import module
#             fullfile = os.path.join(path, file)
#             modname = os.path.splitext(file)[0]
#             print('modname', modname)
#             mod = __import__("codeeditor.parsers."+modname, fromlist=[modname])
#             parserModules.append(mod)
#         
#         print(parserModules)
    

    
    @classmethod
    def _collectParsers(cls):
        """ _collectParsers()
        
        Collect all parser classes. This function is called on startup.
        
        """
        
        # Prepare (use a set to prevent duplicates)
        foundParsers = set()
        G = parsers.__dict__
        ModuleClass = os.__class__
        
        # Collect parser classes
        for module_name in G:
            # Check if it is indeed a module, and if it has the right name
            if not isinstance(G[module_name], ModuleClass):
                continue
            if not module_name.endswith('_parser'):
                continue
            # Collect all valid classes from the module
            moduleDict = G[module_name].__dict__
            for name_in_module in moduleDict:
                ob = moduleDict[name_in_module]                    
                if isinstance(ob, type) and issubclass(ob, parsers.Parser):
                    foundParsers.add(ob)
        
        # Put in list with the parser names as keys
        parserInstances = {}
        for parserClass in foundParsers:
            name = parserClass.__name__
            if name.endswith('Parser') and len(name)>6:
                
                # Get parser identifier name
                name = name[:-6].lower()
                
                # Try instantiating the parser
                try:
                    parserInstances[name] = parserInstance = parserClass()
                except Exception:
                    # We cannot get the exception object in a Python2/Python3
                    # compatible way
                    print('Could not instantiate parser "%s".'%name)
                    continue
                
                # Register extensions for this parser
                for ext in parserInstance.filenameExtensions():
                    cls._fileExtensions[ext] = name
        
        # Store
        cls._parserInstances = parserInstances
    
    
    @classmethod
    def getParserNames(cls):
        """ getParserNames()
        
        Get a list of all available parsers.
        
        """
        return list(cls._parserInstances.keys())
    
    
    @classmethod
    def getParserByName(cls, parserName):
        """ getParserByName(parserName)
        
        Get the parser object corresponding to the given name.
        If no parser is known by the given name, a warning message
        is printed and None is returned.
        
        """
        if not parserName:
            return parsers.Parser() #Default dummy parser
            
        # Case insensitive
        parserName = parserName.lower()
        
        # Return instantiated parser object.
        if parserName in cls._parserInstances:
            return cls._parserInstances[parserName]
        else:
            print('Warning: no parser known by the name "%s".'%parserName)
            print('I know these: ', cls._parserInstances.keys())
            return parsers.Parser() #Default dummy parser
    
    
    @classmethod
    def getStyleElementDescriptionsForAllParsers(cls):
        """ getStyleElementDescriptionsForAllParsers()
        
        Get all style element descriptions corresponding to 
        the tokens of all parsers.
        
        This function is used by the code editor to register all syntax
        element styles to the code editor class.
        
        """
        descriptions = {}
        for parser in cls._parserInstances.values():
            for token in parser.getUsedTokens():
                description = token.description
                descriptions[description.key] = description
        
        return list(descriptions.values())
    
    
    ## File extensions
    
    
    @classmethod
    def suggestParserfromFilenameExtension(cls, ext):
        """ suggestParserfromFilenameExtension(ext)
        
        Given a filename extension, rerurns the name of the suggested
        parser corresponding to the language of the file.
        
        See also registerFilenameExtension()
        """
        
        # Normalize ext
        ext = '.' + ext.lstrip('.').lower()
        
        # Get parser
        if ext in cls._fileExtensions:
            return cls._fileExtensions[ext]
        else:
            return ''
    
    
    @classmethod
    def registerFilenameExtension(cls, ext, parser):
        """ registerFilenameExtension(ext, parser)
        
        Registers the given filename extension to the given parser.
        The parser can be a Parser instance or its name.
        
        This function can be used to register extensions to parsers
        that are not registered by default.
        
        """
        # Normalize ext
        ext = '.' + ext.lstrip('.').lower()
        # Check parser
        if isinstance(parser, parsers.Parser):
            parser = parser.name()
        # Register
        cls._fileExtensions[ext] = parser
    
    
    ## Fonts
    
    
    @classmethod
    def fontNames(cls):
        """ fontNames()
        
        Get a list of all monospace fonts available on this system.
        
        """
        db = QtGui.QFontDatabase()
        QFont, QFontInfo = QtGui.QFont, QtGui.QFontInfo
        # fn = font_name (str)
        return [fn for fn in db.families() if QFontInfo(QFont(fn)).fixedPitch()]
    
    
    @classmethod
    def setDefaultFontFamily(cls, name):
        """ setDefaultFontFamily(name)
        
        Set the default (monospace) font family name for this system. 
        This should be set only once during startup.
        
        """
        cls._defaultFontFamily = name
    
    
    @classmethod
    def defaultFont(cls):
        """ defaultFont()
        
        Get the default (monospace) font for this system. Returns a QFont
        object. 
        
        """
    
        # Get font size that makes sense for this system
        f = QtGui.QFont()
        size = f.pointSize()
        
        # Get font family 
        f = QtGui.QFont(cls._defaultFontFamily)
        f.setStyleHint(f.TypeWriter, f.PreferDefault)
        fi = QtGui.QFontInfo(f)
        family = fi.family()
        
        # Done
        return QtGui.QFont(family, size)


# Init
try:
    Manager._collectParsers()
except Exception as why:
    print('Error collecting parsers')
    print(why)
