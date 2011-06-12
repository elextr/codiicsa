#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  untitled.py
#  
#  Copyright 2011 Lex Trotman <lex@fred5>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

from xml.etree.ElementTree import ElementTree
import sys

_title_ul = [ '=', '-', '~', '^', '+' ]

class Out( object ) :
	""" Extendable list using + as operator, never extends with None """
	def __init__( self, i = None ) :
		""" If i is a list initial value is the list otherwise it is [ i ] """
		if i is None : self.lst = []
		elif isinstance( i, list ) : self.lst = i
		else : self.lst = [ i ]
	
	def __add__( self, i ) :
		""" if i is a list extend self, else append i """
		if i is None : return self
		elif isinstance( i, list ) : self.lst.extend( i )
		elif isinstance( i, Out ) : self.lst.extend( i.lst )
		else : self.lst.append( i )
		return self
	
	def __radd__( self, i ) :
		""" if i is a list prepend each element, else prepend i """
		if i is None : return self
		elif isinstance( i, list ) :
			for a in i[:].reverse() : self.lst.insert( 0, a )
		else : self.lst.insert( 0, i )
		return self
	
	def __iter__( self ) : return self.lst.__iter__()
	
	def __len__( self ) : return len( self.lst )
	
	def __getitem__( self, i ) : return self.lst[ i ]
			
class docbook_common ( object ) :
	def __init__( self, tree, all_ids ) :
		self.all_ids = all_ids
		self._section_level = -1
		self._list_level = 0
		self._var_list_level = 1
		self._ordered_list_level = 0
		self.Parent = dict( ( c, p ) for p in tree.getiterator() for c in p)

	def Pre( self, elem, inline = False, attrs = [] ) :
		out = Out()
		i = elem.get( 'id' )
		if i is not None and ( self.all_ids or not i.startswith( '_' ) ) :
			out += ( '' if inline else '\n\n') + '[[' + i + ']]' + ( '' if inline else '\n' )
		r = elem.get( 'role' )
		if r or attrs :
			a = ', '.join( attrs )
			out += '[' + a
			if a and r : out += ', '
			if r : out += 'role=' + r
			out +=  ']' + ( '' if inline else '\n' )
		return out
	
	def Process( self, elem ) :
		""" process the specified element, returns list of strings """
		p = getattr( self, elem.tag, None )
		if p is None :
			out = self.Pre( elem ) +  "<" + elem.tag + ">" + elem.text + self.Children( elem ) \
					+ "</" + elem.tag + ">" + elem.tail
		else : out = p( elem )
		return out

	def Children( self, elem, do = None, dont = set() ) :
		""" Process children, return resulting string list
		    elem = element whose children are processed
		    do = set of strings naming tags of children to process, default None = all children
		    dont = set of strings naming tags of children to not process, default = empty set
		    tag names in both do and dont sets will be processed, ie explicit do overrides dont
		    a single tag name can be passed to do and dont as a string """
		out = Out()
		doset = do; dontset = dont
		if isinstance( do, str ) : doset = set( [ do ] )
		if isinstance( dont, str ) : dontset = set( [ dont ] )
		for e in elem.getchildren() :
			if do is None :
				if e.tag not in dont : out += self.Process( e )
			else :
				if e.tag in do : out += self.Process( e )
		return out
		
	def Strip( self, lst, ch = None ) :
		""" Strip the characters in string ch from both sides of the string 
		    resulting from the iterable of strings lst.
		    Returns an Out containing a single string """
		if not lst : return Out()
		return Out( ''.join( lst ).lstrip( ch ).rstrip( ch ) )
	
	def Stripl( self, lst, ch = None ) :
		""" Strip the characters in string ch from the left side of the string
		    resulting from the iterable of strings lst.
		    Returns an Out containing a single string """
		if not lst : return Out()
		return Out( ''.join( lst ).lstrip( ch ) )
		
	def Stripr( self, lst, ch = None ) :
		""" Strip the characters in string ch from the right side of the string
		    resulting from the iterable of strings lst.
		    Returns an Out containing a single string """
		if not lst : return Out()
		return Out( ''.join( lst ).rstrip( ch ) )
		
	def Underline_title( self, elem ) :
		""" If elem contains <title> create an underlined title for the current section level """
		out = self.Strip( self.Children( elem, 'title' ), None )
		l = len( out[0] )
		return  out + '\n' + ( _title_ul[ self._section_level ] * l ) + '\n\n'
		
	def Block_title( self, elem ) :
		""" If elem contains a <title> tag generate a block title """
		out = self.Children( elem, do = 'title' )
		if out : out = '\n\n.' + out
		else : out = Out( '\n\n' )
		return out
	
	def section( self, elem ) :
		self._section_level += 1
		out = self.Pre( elem ) + self.Underline_title( elem ) + elem.text + self.Children( elem, dont = 'title' )
		self._section_level -= 1
		return out
		
	def simpara( self, elem ) :
		return self.Pre( elem ) + '\n\n' + elem.text + self.Children( elem ) + '\n\n'
	
	def sidebar( self, elem ) :
		return self.Pre( elem ) + self.Block_title( elem ) + '\n********' + elem.text \
			+ self.Children( elem, dont = 'title' ) + '\n********\n\n' + elem.tail
	
	def literal( self, elem ) :
		return Out( '`' ) + elem.text + self.Children( elem ) + '`' + elem.tail
	
	def emphasis( self, elem ) :
		return Out( "'" ) + elem.text + self.Children( elem ) + "'" + elem.tail
		
	def itemizedlist( self, elem ) :
		self._list_level += 1
		out = self.Pre( elem ) + self.Block_title( elem ) + self.Children( elem, dont = 'title' )
		self._list_level -= 1
		return out
	
	def listitem( self, elem ) :
		if self.Parent[ elem ].tag == 'itemizedlist' :
			return '\n' + '*' * self._list_level + ' ' + self.Stripl( self.Children( elem ) )
		if self.Parent[ elem ].tag == 'varlistentry' :
			return self.Stripl( self.Children( elem ), '\n' )
		if self.Parent[ elem ].tag == 'orderedlist' :
			return '\n' + '.' * self._ordered_list_level + ' ' + self.Stripl( self.Children( elem ) )
		return Out()
		
	def link( self, elem ) :
		return Out( '<<' ) + elem.get( 'linkend' ) + ',' + elem.text + self.Children( elem ) + '>>' + elem.tail
	
	def variablelist( self, elem ) :
		self._var_list_level += 1
		out = self.Pre( elem ) + self.Block_title( elem ) + self.Children( elem, dont = 'title' )
		self._var_list_level -= 1
		return out
		
	def varlistentry( self, elem ) :
		return self.Pre( elem ) + self.Children( elem )
	
	def term( self, elem ) :
		return self.Pre( elem ) + self.Stripr( elem.text + self.Children( elem ) ) + ( ':' * self._var_list_level )
	
	def important( self, elem ) :
		return self.Pre( elem, attrs = [ 'IMPORTANT' ] ) + '\n========' + self.Children( elem ) + '========\n'
		
	def footnote( self, elem ) :
		return 'footnote:[' + self.Strip( self.Children( elem ) ) + ']'
		
	def literallayout( self, elem ) :
		return Out( '\n ' ) + elem.text.replace( '\n', '\n ' ) + '\n'
		
	def orderedlist( self, elem ) :
		self._ordered_list_level += 1
		out = self.Pre( elem ) + self.Block_title( elem ) + self.Children( elem, dont = 'title' )
		self._ordered_list_level -= 1
		return out
		
	def note( self, elem ) :
		return self.Pre( elem, attrs = [ 'NOTE' ] ) + '\n========' + self.Children( elem ) + '========\n'

	def screen( self, elem ) :
		return self.Pre( elem ) + '\n--------\n' + elem.text + self.Children( elem ) + '\n--------\n'
		
	def anchor( self, elem ) :
		return self.Pre( elem, True )
		
	def title( self, elem ) :
		return Out( elem.text ) + self.Children( elem )
		
	def blockquote( self, elem ) :
		return self.Pre( elem ) + self.Children( elem )

class docbook_article ( docbook_common ) :
	def __init__( self, tree, all_ids = False ) : docbook_common.__init__( self, tree, all_ids )
		
	def article( self, elem ) :
		self._section_level = 0
		return self.Children( elem )
	
	def articleinfo( self, elem ) :
		return self.Underline_title( elem ) + self.Children( elem, dont = 'title' )

_defaults = { 'article' : docbook_article }

def convert( infile, outfile, dbob = None, cwsl = True ) :
	""" convert the infile in docbook to the outfile in asciidoc
	    using the specified docbook convert object or a default one for the type of document """
	t = ElementTree( file = infile )
	root = t.getroot()
	if dbob is None :
		dt = root.tag
		dts = _defaults.get( dt, None )
		if dts : db = dts( t )
		else :
			print "Error: Unknown document type", dt
			return
	else : db = dbob( t )
	out = db.Process( root )
	nn = 0
	with open( outfile, "w" ) as f :
#		print out.lst
		for i in out :
#			print i
			if cwsl :
				l = i.lstrip( '\n' ); ln = len( i ) - len( l )
				r = l.rstrip( '\n' ); rn = len( l ) - len( r )
				b = min( ln, 2 - nn ); nn += b
				f.write( ( '\n' * b ).encode( 'utf-8' ) )
				if r : f.write( r.encode( 'utf-8' ) ); nn = 0
				b = min( rn, 2 - nn ); nn += b
				f.write( ( '\n' * b ).encode( 'utf-8' ) )
			else : f.write( i.encode( 'utf-8' ) )


def main():
	if len( sys.argv ) != 3 :
		print "Usage: codiicsa infile outfile"
	else :
		convert( sys.argv[1], sys.argv[2] )
	return 0

if __name__ == '__main__':
	main()

