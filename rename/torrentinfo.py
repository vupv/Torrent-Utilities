#!/usr/bin/env python2
import sys, getopt, os.path, re, time;

class TextFormatter:
	NONE = 0x000000; NORMAL = 0x000001; BRIGHT = 0x000002; WHITE = 0x000004; GREEN = 0x000008; RED = 0x000010; CYAN = 0x000020; YELLOW = 0x000040; MAGENTA = 0x000080; DULL = 0x000100;
	def Format (self, format, string = ''):
		self.Output (string);
	def Output (self, string):
		sys.stdout.write (string);

class ANSIColour (TextFormatter):
	escape = chr (0x1b);
	mapping = [(TextFormatter.NORMAL, '[0m'), (TextFormatter.BRIGHT, '[1m'), (TextFormatter.DULL, '[22m'), (TextFormatter.WHITE, '[37m'), (TextFormatter.GREEN, '[32m'), (TextFormatter.CYAN, '[36m'), (TextFormatter.YELLOW, '[33m'), (TextFormatter.RED, '[31m'), (TextFormatter.MAGENTA, '[35m'),];
	def Format (self, format, string = ''):
		codestring = '';
		for name, code in ANSIColour.mapping:
			if format & name: codestring += ANSIColour.escape + code;
		self.Output (codestring + string);

class StringBuffer:
	def __init__ (self, string):
		self.string = string;
		self.index = 0;
	def IsEOF (self):
		return self.index >= len (self.string);
	def Peek (self):
		if self.IsEOF (): raise StringBuffer.BufferOverrun, 1;
		return self.string [self.index];
	def Get (self, length):
		last = self.index + length;
		if last > len (self.string): raise StringBuffer.BufferOverrun, last - len (self.string);
		segment = self.string [self.index : last];
		self.index = last;
		return segment;
	def GetUpto (self, character):
		buffer = '';
		while not self.IsEOF ():
			next = self.Get (1);
			if next == character: return buffer;
			buffer += next;
		raise StringBuffer.CharacterExpected, character;
	class BufferOverrun (Exception): pass;
	class CharacterExpected (Exception): pass;


class Torrent:
	def __init__ (self, filename, string):
		self.filename = filename;
		self.value = Torrent.Parse (string);
		if not self.value.__class__ is Dictionary: raise UnexpectedType, (self.value__class__, Dictionary);
	def Dump (self, formatter, tabchar, depth = 0):
		self.value.Dump (formatter, tabchar, depth);
	def __getitem__ (self, key):
		return self.value [key];
	def __contains__ (self, key):
		return key in self.value;
	def Parse (string):
		type = string.Peek ();
		for exp, parser in TypeLookup:
			if exp.match (type): return parser (string);
		raise Torrent.UnknownTypeChar, (type, string);
	def LoadTorrent (filename):
		handle = file (filename, 'rb');
		return Torrent (filename, StringBuffer (handle.read ()));
	Parse = staticmethod (Parse);
	LoadTorrent = staticmethod (LoadTorrent);
	class UnknownTypeChar (Exception): pass;
	class UnexpectedType (Exception): pass;

class String:
	def __init__ (self, string):
		self.length = int (string.GetUpto (':'));
		self.value = string.Get (self.length);
		self.isprintable = String.IsPrintable (self);
	def Dump (self, formatter, tabchar, depth):
			formatter.Format (TextFormatter.NONE, '%s%s\n' % (tabchar * depth, self.value));
	def __cmp__ (self, other):
		return cmp (self.value, other.value);
	def __hash__ (self):
		return hash (self.value);
	def __add__ (self, value):
		string = self.value + value.value;
		return String (StringBuffer ('%d:%s' % (len (string), string)));
	def IsPrintable (string):
		for char in string.value:
			if ord (char) < 32 or ord (char) > 127: return False;
		return True;
	IsPrintable = staticmethod (IsPrintable);

class Integer:
	def __init__ (self, string):
		string.Get (1);
		self.value = int (string.GetUpto ('e'));
	def Dump (self, formatter, tabchar, depth):
		formatter.Format (TextFormatter.CYAN, '%s%d\n' % (tabchar * depth, self.value));
	def DumpAsDate (self, formatter, tabchar, depth):
		formatter.Format (TextFormatter.MAGENTA, time.strftime ('%Y/%m/%d %H:%M:%S %Z\n', time.gmtime (self.value)));
	def DumpAsSize (self, formatter, tabchar, depth):
		size = float (self.value);
		sizes = ['B', 'KB', 'MB', 'GB'];
		while size > 1024 and len (sizes) > 1:
			size /= 1024;
			sizes = sizes [1 :];
		formatter.Format (TextFormatter.CYAN, '%s%.1f%s\n' % (tabchar * depth, size + 0.05, sizes [0]));
	def __add__ (self, value):
		return Integer (StringBuffer ('i%de' % (self.value + value.value)));

class Dictionary:
	def __init__ (self, string):
		string.Get (1);
		self.value = { };
		while string.Peek () != 'e':
			key = String (string);
			self.value [key] = Torrent.Parse (string);
		string.Get (1);
	def Dump (self, formatter, tabchar, depth):
		keys = self.value.keys ();
		keys.sort ();
		for key in keys:
			formatter.Format (TextFormatter.NORMAL | TextFormatter.GREEN);
			if depth < 2: formatter.Format (TextFormatter.BRIGHT);
			key.Dump (formatter, tabchar, depth);
			formatter.Format (TextFormatter.NORMAL);
			self.value [key].Dump (formatter, tabchar, depth + 1);
	def __getitem__ (self, key):
		for name, value in self.value.iteritems ():
			if name.value == key: return value;
		raise KeyError, key;
	def __contains__ (self, key):
		for name, value in self.value.iteritems ():
			if name.value == key: return True;
		return False;

class List:
	def __init__ (self, string):
		string.Get (1);
		self.value = [];
		while string.Peek () != 'e':
			self.value.append (Torrent.Parse (string));
		string.Get (1);
	def Dump (self, formatter, tabchar, depth):
		if len (self.value) == 1:
			self.value [0].Dump (formatter, tabchar, depth);
		else:
			for index in range (len (self.value)):
				formatter.Format (TextFormatter.BRIGHT | TextFormatter.YELLOW, '%s%d\n' % (tabchar * depth, index));
				formatter.Format (TextFormatter.NORMAL);
				self.value [index].Dump (formatter, tabchar, depth + 1);
	def Join (self, separator):
		separator = String (StringBuffer ('%d:%s' % (len (separator), separator)));
		return reduce (lambda x, y: x + separator + y, self.value);
	def __len__ (self):
		return len (self.value);
	def __iter__ (self):
		return self.value.__iter__ ();
	def __getitem__ (self, index):
		return self.value [index];

TypeLookup = [(re.compile ('d'), Dictionary), (re.compile ('l'), List), (re.compile ('[0-9]'), String), (re.compile ('i'), Integer)];
TabChar = '';

def GetCommandlineArguments (appname, arguments):
	try:
		options, arguments = getopt.getopt (arguments, 'hndbf', ['help', 'nocolour', 'dump', 'basic', 'files']);
	except getopt.GetoptError:
		ShowUsage (appname);
	if not arguments: ShowUsage (appname);
	optionsmap = [(('-n', '--nocolour'), 'nocolour'), (('-d', '--dump'), 'dump'), (('-b', '--basic'), 'basic'), (('-f', '--files'), 'files')];
	setoptions = { };
	for option, value in options:
		if option in ['-h', '--help']: ShowUsage (appname);
		for switches, key in optionsmap:
			if option in switches: setoptions [key] = value;
	return setoptions, arguments;

def ShowUsage ( appname ):
	sys.exit ( '%s [ -h -n ] filename1 [ ... filename ]\n\n' % appname +
			   '    -h --help      Displays this message\n' +
			   '    -b --basic     Shows basic file information (default)\n' +
			   '    -f --files     Shows files within the torrent\n' +
			   '    -d --dump      Dumps the whole file hierarchy\n' +
			   '    -n --nocolour  No ANSI colour\n' );

def GetFormatter (nocolour):
	return { True : TextFormatter, False : ANSIColour } [nocolour] ();

def StartLine (formatter, prefix, depth, postfix = '', format = TextFormatter.NORMAL):
	formatter.Format (TextFormatter.BRIGHT | TextFormatter.GREEN, '%s%s' % (TabChar * depth, prefix));
	formatter.Format (format, '%s%s' % (TabChar, postfix));

def GetLine (formatter, prefix, key, torrent, depth = 1, isdate = False, format = TextFormatter.NORMAL):
	StartLine (formatter, prefix, depth, format = format);
	if key in torrent:
		if isdate:
			if torrent [key].__class__ is Integer:
				torrent [key].DumpAsDate (formatter, '', 0);
			else:
				formatter.Format (TextFormatter.BRIGHT | TextFormatter.RED, '[Not An Integer]');
		else:
			torrent [key].Dump (formatter, '', 0);
	else:
		formatter.Format (TextFormatter.NORMAL, '\n');

def Dump (formatter, torrent):
	torrent.Dump (formatter, TabChar, 1);

def Basic (formatter, torrent):
	GetLine (formatter, '', 'name', torrent ['info'], format = TextFormatter.NORMAL);

def BasicFiles (formatter, torrent):
	if not 'files' in torrent ['info']:
		infotorrent = torrent ['info'];
		torrent ['info'] ['length'].DumpAsSize (formatter, '', 0);
	else:
		filestorrent = torrent ['info'] ['files'];
		numfiles = len (filestorrent);
		if numfiles > 1:
			lengths = [filetorrent ['length'] for filetorrent in filestorrent];
		else:
			filestorrent [0] ['length'].DumpAsSize (formatter, '', 0);

def ListFiles (formatter, torrent):
	if not 'info' in torrent: sys.exit ('Missing "info" section in %s' % torrent.filename);
	StartLine (formatter, 'files', 1, postfix = '\n');
	if not 'files' in torrent ['info']:
		formatter.Format (TextFormatter.YELLOW | TextFormatter.BRIGHT, '%s%d' % (TabChar * 2, 0));
		formatter.Format (TextFormatter.NORMAL, '\n');
		torrent ['info'] ['name'].Dump (formatter, TabChar, 3);
		torrent ['info'] ['length'].DumpAsSize (formatter, TabChar, 3);
	else:
		filestorrent = torrent ['info'] ['files'];
		for index in range (len (filestorrent)):
			formatter.Format (TextFormatter.YELLOW | TextFormatter.BRIGHT, '%s%d' % (TabChar * 2, index));
			formatter.Format (TextFormatter.NORMAL, '\n');
			if filestorrent [index] ['path'].__class__ is String:
				filestorrent [index] ['path'].Dump (formatter, TabChar, 3);
			else:
				filestorrent [index] ['path'].Join (os.path.sep).Dump (formatter, TabChar, 3);
			filestorrent [index] ['length'].DumpAsSize (formatter, TabChar, 3);

if __name__ == "__main__":
	try:
		settings, filenames = GetCommandlineArguments (os.path.basename (sys.argv [0]), sys.argv [1:]);
		formatter = GetFormatter ('nocolour' in settings);
		if 'nocolour' in settings: del settings ['nocolour']
		for filename in filenames:
			torrent = Torrent.LoadTorrent (filename);
			if settings and not 'basic' in settings:
				if 'dump' in settings:
					Dump (formatter, torrent);
				elif 'files' in settings:
					Basic (formatter, torrent);
					ListFiles (formatter, torrent);
			else:
				Basic (formatter, torrent);
				BasicFiles (formatter, torrent);
	except SystemExit, message:
		sys.exit (message);
	except KeyboardInterrupt:
		pass;
