#!/usr/bin/env python
'''Module that defines two parser classess for block-structured data,
   for untyped and typed data, as well as auxilary classes for
   exceptions.  Can be called directly to perform unit tests'''

import io
import re
import sys
import unittest
import parser_errors as err
import block


class BlockParser:
    '''Parser class to parse file in block format'''

    def __init__(self):
        '''constructor, initializes parser and resets it'''
        self._states = ['in_block', 'not_in_block', 'error']
        self._comment_pattern = re.compile(r'#.*')
        self._block_begin_pattern = re.compile(r'begin\s+(\w+)')
        self._block_end_pattern = re.compile(r'end\s+(\w+)')
        self._state = None
        self._current_block = None
        self._blocks = None
        self._match = None
        self._line_nr = None
        self._line_int = 10
        self._verbose = 0
        self._reset()

    def set_verbosity(self, verbosity_level):
        '''set verbosity level of the parser, useful for debugging
             level 0: no feedback
             level 1: print line numbers parsed
             level 2: show state changes as well'''
        self._verbose = verbosity_level

    def is_verbose(self):
        '''return True if the parser should be verbose, False otherwise
           (True for levels greater than 0'''
        return self._verbose > 0

    def is_trace(self):
        '''return True if the parser should print trace information,
           False otherwise (True for levels greater than 1'''
        return self._verbose > 1

    def set_line_interval(self, skip_lines):
        '''set the number of lines interval for verbose output'''
        self._line_int = skip_lines

    def get_line_interval(self):
        '''returns the number of lines interval for verbose output'''
        return self._line_int

    def _reset(self):
        '''internal function to reset the parser between calls to the parse
           method'''
        self._set_state('not_in_block')
        self._current_block = None
        self._blocks = []
        self._match = None
        self._line_nr = 0

    def _is_in_state(self, state):
        '''checks whether the parser's current state is the given state'''
        return state == self.get_state()

    def get_state(self):
        '''return the parser's current state'''
        return self._state

    def _set_state(self, new_state):
        '''set the parser's state, after checking it is valid'''
        if self.is_trace():
            sys.stderr.write(
                'change state from {0} to {1}\n'.format(
                    self._state, new_state))
        if new_state in self._states:
            self._state = new_state
        else:
            raise err.UnknownStateError(new_state)

    def _is_begin_block(self, line):
        '''checks whether this is a line indicating the beginning of a
           block, if so, temporarilly store the match object'''
        self._match = self._block_begin_pattern.match(line)
        return self._match is not None

    def _is_end_block(self, line):
        '''checks whether this  is a line indicating the end of a block,
           if so, temporarilly store the match object'''
        self._match = self._block_end_pattern.match(line)
        return self._match is not None

    def _preprocess(self, line):
        '''takes a line, strips leading and trailing whitespace, and removes
           comments'''
        return self._comment_pattern.sub('', line).strip()

    def _end_matches_begin(self):
        '''returns true if begin and end block match, false otherwise'''
        return self._match.group(1) == self._current_block.get_name()

    def _init_block(self):
        '''creates a new block'''
        self._current_block = block.Block(self._match.group(1))
        self._match = None

    def _is_data(self, line):
        '''returns true if the line contains data, false otherwise'''
        return len(line) > 0

    def _add_data(self, line):
        '''add given line as data to the current block'''
        self._current_block.add_data(line)

    def _finish_block(self):
        '''adds the block to the list of blocks, and resets current block'''
        finished_block = self._current_block
        self._current_block = None
        self._match = None
        return finished_block

    def get_line_nr(self):
        '''return the line number the parser has reached in the file'''
        return self._line_nr

    def _incr_line_nr(self):
        '''incredment the current line number'''
        self._line_nr += 1
        if self.is_verbose() and self._line_nr % self._line_int == 0:
            sys.stderr.write('parsing line {0}\n'.format(self._line_nr))

    def get_blocks(self):
        '''Returns the lists of blocks parsed so far, usefule if the
           parser raises an extension.  Note that when using the
           iterator mode, this list will always be empty'''
        return self._blocks

    def parse_iter(self, block_file):
        '''takes a file to parse and acts as an iterator over the
           the blocks contained in the file'''
        self._reset()
        for line in block_file:
            self._incr_line_nr()
            line = self._preprocess(line)
            if self._is_in_state('not_in_block'):
                if self._is_begin_block(line):
                    self._init_block()
                    self._set_state('in_block')
                elif self._is_end_block(line):
                    raise err.DanglingEndBlockError(self)
            elif self._is_in_state('in_block'):
                if self._is_end_block(line):
                    if self._end_matches_begin():
                        yield self._finish_block()
                        self._set_state('not_in_block')
                    else:
                        raise err.NonMatchingBlockDelimitersError(self)
                elif self._is_begin_block(line):
                    raise err.NestedBlocksError(self)
                elif self._is_data(line):
                    self._add_data(line)
            else:
                raise err.UnknownStateError(self.get_state())
        if self._is_in_state('in_block'):
            raise err.NonClosedBlockError(self)

    def parse(self, block_file):
        '''takes a file to parse and returns a list of blocks contained
           in the file'''
        for finished_block in self.parse_iter(block_file):
            self._blocks.append(finished_block)
        return self._blocks


class TypedBlockParser(BlockParser):
    '''implements a parser for typed block structured data'''

    def __init__(self):
        '''constructor for the typed block parser'''
        BlockParser.__init__(self)
        pattern = r'\s*begin\s+(\w+)(?:\s*\[\s*(\w+)\s*\])?'
        self._block_begin_pattern = re.compile(pattern)

    def _init_block(self):
        '''creates a new typed block'''
        self._current_block = block.TypedBlock(self._match.group(1),
                                               self._match.group(2))
        self._match = None


class ParserTest(unittest.TestCase):
    '''Tests for the parser class'''

    def test_constructor(self):
        '''create a parser, check initial state'''
        parser = BlockParser()
        self.assertEqual(parser.get_line_nr(), 0)
        self.assertEqual(parser.get_state(), 'not_in_block')
        self.assertEqual(parser.get_blocks(), [])

    def test_parse_blocks(self):
        '''parse data from two blocks and check'''
        data = '''
            Some initial text,
            on two lines.
            begin b1
                0.31
                0.21  # this is inline comment
                0.41
            end b1
            This is just some text
            begin b2
                0.42
                # this is a comment
                0.22

                0.12
                0.32
            end b2
            # some final comments
            and some ordinary text.
            '''
        block_file = io.StringIO(data)
        parser = BlockParser()
        blocks = parser.parse(block_file)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].get_name(), 'b1')
        self.assertEqual(blocks[1].get_name(), 'b2')
        self.assertEqual(len(blocks[0].get_data()), 3)
        self.assertEqual(len(blocks[1].get_data()), 4)
        self.assertEqual(blocks[0].get_data(),
                         ['0.31', '0.21', '0.41'])
        self.assertEqual(blocks[1].get_data(),
                         ['0.42', '0.22', '0.12', '0.32'])

    def test_processing(self):
        '''parse a block, and test sorting of data'''
        data = '''
            begin b1
                0.31
                0.21
                0.41
            end b1'''
        block_file = io.StringIO(data)
        parser = BlockParser()
        blocks = parser.parse(block_file)
        list(map(lambda x: x.sort_data(), blocks))
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].get_name(), 'b1')
        self.assertEqual(blocks[0].get_data(),
                         ['0.21', '0.31', '0.41'])

    def test_nested_blocks(self):
        '''parse nested blocks, check for exception'''
        data = '''
            begin b1
                0.31
                0.21
                begin b2
                    0.42
                    0.22
                    0.12
                    0.32
                end b2
                0.41
            end b1
            '''
        block_file = io.StringIO(data)
        parser = BlockParser()
        with self.assertRaises(err.NestedBlocksError):
            parser.parse(block_file)

    def test_nonmatching_begin_end(self):
        '''parse non-matching begin/end blocks, check for exception'''
        data = '''
            begin b1
                0.31
                0.21
            end b2
            '''
        block_file = io.StringIO(data)
        parser = BlockParser()
        with self.assertRaises(err.NonMatchingBlockDelimitersError):
            parser.parse(block_file)

    def test_dangling_end(self):
        '''parse dangling end blocks, check for exception'''
        data = '''
            begin b1
                0.31
                0.21
            end b1
            end b2
            '''
        block_file = io.StringIO(data)
        parser = BlockParser()
        with self.assertRaises(err.DanglingEndBlockError):
            parser.parse(block_file)

    def test_nonclosed_block(self):
        '''parse missing end block, check for exception'''
        data = '''
            begin b1
                0.31
                0.21
            '''
        block_file = io.StringIO(data)
        parser = BlockParser()
        with self.assertRaises(err.NonClosedBlockError):
            parser.parse(block_file)


class TypedParserTest(unittest.TestCase):
    '''tests for TypedParser'''
    def test_typed_constructor(self):
        '''create a TypedParser, check initial state'''
        parser = TypedBlockParser()
        self.assertEqual(parser.get_line_nr(), 0)
        self.assertEqual(parser.get_state(), 'not_in_block')
        self.assertEqual(parser.get_blocks(), [])

    def test_typed_parse_blocks(self):
        '''parse data from two blocks and check'''
        data = '''
            Some initial text,
            on two lines.
            begin b1[float]
                0.31
                0.21  # this is inline comment
                0.41
            end b1
            This is just some text
            begin b2[float]]
                0.42
                # this is a comment
                0.22

                0.12
                0.32
            end b2
            # some final comments
            and some ordinary text.
            '''
        block_file = io.StringIO(data)
        parser = TypedBlockParser()
        blocks = parser.parse(block_file)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].get_name(), 'b1')
        self.assertEqual(blocks[0].get_type(), 'float')
        self.assertEqual(blocks[1].get_name(), 'b2')
        self.assertEqual(blocks[1].get_type(), 'float')
        self.assertEqual(len(blocks[0].get_data()), 3)
        self.assertEqual(len(blocks[1].get_data()), 4)
        self.assertEqual(blocks[0].get_data(),
                         [0.31, 0.21, 0.41])
        self.assertEqual(blocks[1].get_data(),
                         [0.42, 0.22, 0.12, 0.32])

    def test_typed_processing_default_type(self):
        '''parse a block, and test sorting of data'''
        data = '''
            begin b1
                0.31
                0.21
                0.41
            end b1'''
        block_file = io.StringIO(data)
        parser = TypedBlockParser()
        blocks = parser.parse(block_file)
        list(map(lambda x: x.sort_data(), blocks))
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].get_name(), 'b1')
        self.assertEqual(blocks[0].get_data(),
                         ['0.21', '0.31', '0.41'])

    def test_typed_parse_iter_blocks(self):
        '''parse data from two blocks and check'''
        data = '''
            Some initial text,
            on two lines.
            begin b1[float]
                0.31
                0.21  # this is inline comment
                0.41
            end b1
            This is just some text
            begin b2[float]]
                0.42
                # this is a comment
                0.22

                0.12
                0.32
            end b2
            # some final comments
            and some ordinary text.
            '''
        block_file = io.StringIO(data)
        parser = TypedBlockParser()
        blocks = parser.parse(block_file)
        block_file.seek(0)
        block_nr = 0
        for parsed_block in parser.parse_iter(block_file):
            self.assertEqual(str(blocks[block_nr]),
                             str(parsed_block))
            block_nr += 1


if __name__ == '__main__':
    unittest.main()
