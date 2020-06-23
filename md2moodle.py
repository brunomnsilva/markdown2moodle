# Markdown to Moodle XML 
#
# This script parses a markdown file (containing quizes) and outputs Moodle's XML Quiz format.
#
# The specification of Moodle XML format: https://docs.moodle.org/38/en/Moodle_XML_format
#
# Please see README.md for markdown format details and script usage.
#
# Credits to https://github.com/goFrendiAsgard/markdown-to-moodle-xml.git for the original code.
# This is a significant evolution of his code, but maintains the basic ideas.
#
# ---
#
# This script contains all classes and functions used to implement a finite state machine (FSM)
# used to parse a markdown file. This enables a more robust approach to the parsing mechanism,
# together with localized error detection in the parsed file.
#
# The currently implemented FSM is illustrated in 'markdown2moodle.png' and can be further
# extended to include other states.
#
# ---
#
# This script is organized into the following sections:
#
# Section 0 - Global constants
# Section 1 - REGEX patterns, helpers and transformations over text 
# Section 2 - Quiz class, helper functions and constants
# Section 3 - FSM implementation
# Section 4 - FSM Markdown Parser
# Section 5 - Main 

import os
import sys
import re
import hashlib
import random
import json
import base64
from markdown import markdown

if sys.version_info[0] == 3:
    from urllib.request import urlopen
else:
    from urllib import urlopen

######################################################################
# Section 0 - Global constants
######################################################################

CONFIG = {
    # Produce debugging information while parsing
    'debug' : False,
    
    # quiz answer numbering | allowed values: 'none', 'abc', 'ABCD' or '123'
    'answer_numbering' : 'abc', 
    # quiz shuffle answers | 1 -> true ; 0 -> false
    'shuffle_answers' : '1',

    # pygments code snapshot generator
    'pygments.font_size' : 16,
    'pygments.line_numbers' : False,

    # pygments code snapshot | additional dump to disk of generated images
    'pygments.dump_image' : False,
    'pygments.dump_image_id' : 1, #e,g, 1.png and incremented for each image
}

######################################################################
# Section 1 - REGEX patterns, helpers and transformations over text 
######################################################################

##
# REGEX PATTERNS

NEW_LINE = '\n'
HEADER_PATTERN = re.compile(r'^\s*# (.*)$')
QUESTION_PATTERN = re.compile(r'^(\s*)\*(\s)(.*)$')
CORRECT_ANSWER_PATTERN = re.compile(r'^(\s*)-(\s)!(.*)$')
WRONG_ANSWER_PATTERN = re.compile(r'^(\s*)-(\s)(.*)$')
SWITCH_PRE_TAG_PATTERN = re.compile(r'^```.*$')
EMPTY_LINE_PATTERN = re.compile(r'^\s*$')
IMAGE_PATTERN = re.compile(r'!\[.*\]\((.+)\)')
MULTI_LINE_CODE_PATTERN = re.compile(r'```(.*)\n([\s\S]+)```', re.MULTILINE)
SINGLE_LINE_CODE_PATTERN = re.compile(r'`([^`]+)`')
SINGLE_DOLLAR_LATEX_PATTERN = re.compile(r'\$(.+)\$')
DOUBLE_DOLLAR_LATEX_PATTERN = re.compile(r'\$\$(.+)\$\$', re.MULTILINE)
BLOCKCODE_PATTERN = re.compile(r'^(\s*)```(.*)$')

##
# Regex helpers

def is_header(string):
    return False if get_header(string) is None else True

def is_question(string):
    return False if get_question(string) is None else True

def is_answer(string):
    return is_correct_answer(string) or is_wrong_answer(string)

def is_correct_answer(string):
    return False if get_correct_answer(string) is None else True

def is_wrong_answer(string):
    return False if get_wrong_answer(string) is None else True

def is_blank(string):
    return re.match(EMPTY_LINE_PATTERN, string)

def is_blockcode(string):
    return re.match(BLOCKCODE_PATTERN, string)

def is_eof(string):
    return string == "EOF"

## 
# REGEX matching  and grouping

def get_header(string):
    match = re.match(HEADER_PATTERN, string)
    if match:
        return match.group(1)
    return None

def get_question(string):
    match = re.match(QUESTION_PATTERN, string)
    if match:
        return match.group(3)
    return None


def get_correct_answer(string):
    match = re.match(CORRECT_ANSWER_PATTERN, string)
    if match:
        return match.group(3)
    return None


def get_wrong_answer(string):
    match = re.match(WRONG_ANSWER_PATTERN, string)
    if match:
        return match.group(3)
    return None

##
# REGEX and XML/HTML text transformations

def wrap_cdata(content):
    """Wraps content inside a CDATA xml block."""
    return '<![CDATA[' + content + ']]>'

def sanitize_entities(text):
    """Converts <, > and & to html entities."""

    text = text.replace('#','\\#')
    #unfortunately, this order is important
    text = text.replace('&','&amp;')
    text = text.replace('>','&gt;')
    text = text.replace('<','&lt;')
        
    return text

def render_answer(text):
    """Replaces any allowed contents, e.g., code and images
     and returns the CDATA content."""

    text = re.sub(SINGLE_LINE_CODE_PATTERN, replace_single_line_code, text)
    text = re.sub(SINGLE_DOLLAR_LATEX_PATTERN, replace_latex, text)

    return wrap_cdata( markdown( text ) ) 

def render_question(text, md_dir_path):
    """Replaces any allowed contents, e.g., code and images
     and returns the CDATA content."""

    text = re.sub(MULTI_LINE_CODE_PATTERN, replace_multi_line_code, text)
    text = re.sub(SINGLE_LINE_CODE_PATTERN, replace_single_line_code, text)
    text = re.sub(IMAGE_PATTERN, replace_image_wrapper(md_dir_path), text)
    text = re.sub(DOUBLE_DOLLAR_LATEX_PATTERN, replace_latex, text)
    text = re.sub(SINGLE_DOLLAR_LATEX_PATTERN, replace_latex, text)
    text = wrap_cdata( markdown_custom(text) )
    return text

def markdown_custom(text):
    """Just calls markdown, but may be extended in the future."""
    #return markdown(text, extensions=['tables'])
    return markdown(text, extensions=['nl2br'])
    #return markdown(text)

def replace_latex(match):
    code = match.group(1)
    code = code.replace('(', r'\left(')
    code = code.replace(')', r'\right)')
    return r'\\(' + code + r'\\)'

def replace_single_line_code(match):
    """
    Produces the output for an inline markdown code bock.

    Output should only be wrapped inside a <code> tag.
    """
    code = match.group(1)
    code = sanitize_entities(code)

    return '<code>' + code + '</code>'


def replace_multi_line_code(match):
    lexer = match.group(1)
    code = match.group(2)

    if not lexer:
        lexer = ''
    
    to_image = True if lexer.find('{img}') > 0 else False

    if to_image:
        lexer = lexer.replace('{img}', '')
        return convert_code_image_base64(lexer, code)
    else:
        #sanitize entities before any conversion to XML
        code = sanitize_entities(code)
        return '<pre><code>' + code + '</code></pre>'


def replace_image_wrapper(md_dir_path):
    def replace_image(match):
        file_name = match.group(1)
        if (not os.path.isabs(file_name)) and ('://' not in file_name):
            file_name = os.path.join(md_dir_path, file_name)
        return build_image_tag(file_name)
    return replace_image


def build_image_tag(file_name):
    extension = file_name.split('.')[-1]
    try:
        data = urlopen(file_name).read()
    except Exception:
        f = open(file_name, 'rb')
        data = f.read()
    base64_image = (base64.b64encode(data)).decode('utf-8')
    src_part = 'data:image/' + extension + ';base64,' + base64_image
    return '<img style="display:block;" src="' + src_part + '" />'

def convert_code_image_base64(lexer_name, code):
    """Converts a code snippet to an image in base64 format."""
    
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import ImageFormatter
    from pygments.lexers import ClassNotFound
    import tempfile

    if not lexer_name:
        lexer_name = 'pascal'
    try:
        lexer = get_lexer_by_name(lexer_name)
    except ClassNotFound:
        lexer = get_lexer_by_name('pascal')

    imgBytes = highlight(code, lexer,\
                        ImageFormatter(font_size=CONFIG['pygments.font_size'],\
                            line_numbers = CONFIG['pygments.line_numbers']))

    if CONFIG['pygments.dump_image']:
        img_id = CONFIG['pygments.dump_image_id']

        imgFile = './' + str(img_id) + '.png'
        with open(imgFile, 'wb') as imageOut:
            imageOut.write(imgBytes)
        
        img_id += 1
        CONFIG['pygments.dump_image_id'] = img_id

    temp = tempfile.NamedTemporaryFile()
    temp.write(imgBytes)
    temp.seek(0)

    extension = 'png'
    base64_image = (base64.b64encode(temp.read())).decode('utf-8')
    src_part = 'data:image/' + extension + ';base64,' + base64_image
    
    temp.close()
    return '<img style="display:block;" src="' + src_part + '" />'


######################################################################
# Section 2 - Quiz class, helper functions and constants
######################################################################

class QuizError(Exception):
    pass

class Quiz(dict):
    def __init__(self, *args, default=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.section = [] 
        self.current_question = {}

        self.is_valid = False

    def consume_header(self, line):
        """Starts a new section with this header."""

        self.section = []
        self[get_header(line)] = self.section

    def consume_question(self, line):
        """Starts a new question with this content."""

        self.current_question = {'text': get_question(line), 'answers': []}
        self.section.append(self.current_question)

    def append_to_question(self, line): 
        """Appends content to current question."""

        #TODO: there's a problem enforcing line breaks in the output
        self.current_question['text'] += line + '\n'

    def consume_answer(self, line):
        """Appends the answer from this content to the current question."""

        if is_correct_answer(line):

            current_answer = {
                'text': get_correct_answer(line),
                'correct': True
                }
            
            self.current_question['answers'].append(current_answer)

        elif is_wrong_answer(line):

            current_answer = {
                'text': get_wrong_answer(line),
                'correct': False
                }
            
            self.current_question['answers'].append(current_answer)

        else:
            #some other content, ignore.
            pass

    def current_question_has_correct_answers(self):
        correct_answers = [x for x in self.current_question['answers'] if x['correct']]
        correct_answer_count = len(correct_answers)
        
        return (correct_answer_count >= 1)

    def validate(self):
        """Must call after successful parse of document."""
        self.__complete()
        self.is_valid = True        

    def __complete(self):
        """Completes parsed information with 'fraction' values for answers."""

        for key in self:
            section = self[key]
            for question in section:
                correct_answers = [x for x in question['answers'] if x['correct']]
                correct_answer_count = len(correct_answers)
                
                if correct_answer_count < 1:
                    self.is_valid = False
                    raise QuizError("No correct answer(s) for %s" % (question['text']))

                question['single'] = correct_answer_count == 1
                weight = round(100.0 / correct_answer_count, 7)
                for answer in question['answers']:
                    if answer['correct']:
                        answer['weight'] = weight
                    else:
                        answer['weight'] = 0

    def export_xml_to_file(self, md_file_name):
        """Produces the XML file outputs; one for each specified category in the md file."""
        if self.is_valid:            
            md_dir_path = os.path.dirname(os.path.abspath(md_file_name))

            for section_caption in self:
                section = self[section_caption]
                xml_file = open(create_output_filename(md_file_name, section_caption), 'w')
                xml_file.write(section_to_xml(section_caption, section, md_dir_path))

        else:
            print("Quiz is not marked as valid for export.")

    def export_xml_to_string(self, md_file_name):
        """Produces the XML output and returns the resulting text."""
        if self.is_valid:
            md_dir_path = os.getcwd()
            result = {}            
            for section_caption in self:
                section = self[section_caption]
                result[section_caption] = section_to_xml(section_caption, section, md_dir_path)
            return json.dumps(result, indent=2)
        else:
            print("Quiz is not marked as valid for export.")
            return ""
        
        
def create_output_filename(md_file_name, section_caption):
    """Generates and sanitizes .xml output filename.

    - All extensions and spaces are removed;
    - Forward slashes '/' (possible in section caption for sub-categories)
        are replaced with hyphens.
    """

    section_caption = section_caption.replace('/','-').replace(' ','')
    md_name = md_file_name.replace('.md','')

    output_file_name = md_name + '_' + section_caption + '.xml'

    return output_file_name

def section_to_xml(section_caption, section, md_dir_path):
    """Convert a parsed section to XML

    Keyword arguments:
    section_caption -- Title of section (used to assign category)
    section -- dictionary mapped content from 'md_script_to_dictionary'
    md_dir_path -- path of the markdown file
    """

    xml = '<?xml version="1.0" ?><quiz>'
    
    #create dummy question to specify category for questions
    xml += '<question type="category"><category><text>' + section_caption + '</text></category></question>'
    
    #add parsed questions
    for index, question in enumerate(section):
        xml += question_to_xml(question, index, md_dir_path)
    xml += '</quiz>'
    return xml


def question_to_xml(question, index, md_dir_path):
    """
    Converts a parsed question to XML.

    <name> is automatically generated from a hash (question text + rand)
    <single> is derived from correct answers (1/0)
    <questiontext> is encoded in CDATA and html format
    """

    #convert question text to CDATA html
    rendered_question_text = render_question(question['text'], md_dir_path)

    index_part = str(index + 1).rjust(4, '0')
    q_part = (question['text'] + str(random.random())).encode('utf-8')
    question_single_status = ('true' if question['single'] else 'false')
    
    xml = '<question type="multichoice">'
    # question name
    xml += '<name><text>'
    xml += index_part + hashlib.md5(q_part).hexdigest()
    xml += '</text></name>'
    # question text
    xml += '<questiontext format="html"><text>'
    xml += rendered_question_text
    xml += '</text></questiontext>'
    # answer
    for answer in question['answers']:
        xml += answer_to_xml(answer)
    
    # other properties
    xml += '<shuffleanswers>' + CONFIG['shuffle_answers'] + '</shuffleanswers>'
    xml += '<single>' + question_single_status + '</single>'
    xml += '<answernumbering>' + CONFIG['answer_numbering'] + '</answernumbering>'
    xml += '</question>'
    return xml


def answer_to_xml(answer):
    """Produces the XML output for an answer."""

    text = answer['text']

    #make any necessary transformatins to answer
    text = render_answer(text)

    xml = '<answer fraction="'+str(answer['weight'])+'">'
    xml += '<text>'+text+'</text>'
    xml += '</answer>'
    return xml


######################################################################
# Section 3 - FSM implementation
######################################################################

class InitializationError(Exception):
    """Signals that the FSM is not properly configured to run."""
    pass

class TransitionError(Exception):
    """Signals that a transition forced by the parsing is not valid."""
    pass

class StateMachine:
    """
    Provides the definition of a finite state machine in python that 
    enables to change state and run a parsed line within that state,
    i.e., the FSM will run a delegate function according to its current
    state.
    """
    def __init__(self):
        self.handlers = {}
        self.state = None
        self.endStates = []

    def add_state(self, name, handler, end_state=0):
        """Adds a state (name) and its handler function."""

        name = name.upper()
        self.handlers[name] = handler
        if end_state:
            self.endStates.append(name)

    def set_start(self, name):
        """Sets the start state (name).
        The state must have been previously added through 'add_state' method. 
        """
        self.state = name.upper()

    def run(self, quest, line_text, line_number):
        """Executes the handler for the current state."""

        try:
            handler = self.handlers[self.state]
        except:
            raise InitializationError("must call .set_start() before .run()")
        if not self.endStates:
            raise  InitializationError("at least one state must be an end_state")
    
        if CONFIG['debug']:
            print("In state %25s | Processing: %s" %(self.state, line_text))
        
        newState = handler(quest, line_text, line_number)
        self.state = newState.upper()

        if self.state in self.endStates and CONFIG['debug']:
            print("Success! Reached an end state:", newState)



######################################################################
# Section 4 - FSM Markdown Parser
######################################################################

##
# FSM State handlers - These implement the transitions and their actions
#
# Each handler receives the current quiz, the currently parsed line
# line number. Line numbers aren't currently used within each state,
# but may be useful in the future for some reason.

def state_start(quiz, line_text, line_number):
    
    if is_blank(line_text):
        state = "start"
    elif is_header(line_text):
        quiz.consume_header(line_text)
        state = "parse_header"
    elif is_question(line_text):
        quiz.consume_question(line_text)
        state = "parse_question"
    else:
        raise TransitionError("Expecting a header or a question")

    return state

def state_parse_header(quiz, line_text, line_number):
    
    if is_blank(line_text):
        # do nothing
        state = "parse_header"
    elif is_question(line_text):
        quiz.consume_question(line_text)
        state = "parse_question"
    else:
        raise TransitionError("Expecting a question")

    return state

def state_parse_question(quiz, line_text, line_number):

    if is_blank(line_text):
        # do nothing
        state = "parse_question"
    elif is_blockcode(line_text):
        quiz.append_to_question(line_text)
        state = "parse_question_codeblock"
    elif is_answer(line_text):
        quiz.consume_answer(line_text)
        state = "parse_answer"
    elif is_header(line_text) or is_question(line_text) or is_eof(line_text):
        raise TransitionError("Expecting text, codeblock or answer")
    else:
        quiz.append_to_question(line_text)
        state  = "parse_question"
        pass

    return state

def state_parse_question_codeblock(quiz, line_text, line_number):

    # In a codeblock we accept everything until it closes
    if is_eof(line_text):
        raise TransitionError("Expecting closing codeblock")
    elif is_blockcode(line_text):
        quiz.append_to_question(line_text)
        state = "parse_question"
    else:
        quiz.append_to_question(line_text)
        state = "parse_question_codeblock"

    return state

def state_parse_answer(quiz, line_text, line_number):

    if is_blank(line_text):
        # do nothing
        state = "parse_answer"
    elif is_answer(line_text):
        quiz.consume_answer(line_text)
        state = "parse_answer"
    elif is_question(line_text):
        if quiz.current_question_has_correct_answers():
            quiz.consume_question(line_text)
            state = "parse_question"
        else:
            raise TransitionError("Expecting at least one correct answer in previous question")
    elif is_header(line_text):
        if quiz.current_question_has_correct_answers():
            quiz.consume_header(line_text)
            state = "parse_header"
        else:
            raise TransitionError("Expecting at least one correct answer in previous question")
    elif is_eof(line_text):
        if quiz.current_question_has_correct_answers():
            # mark as valid and go to end state
            quiz.validate()
            state = "end"
        else:
            raise TransitionError("Expecting at least one correct answer in previous question")
    else:
        raise TransitionError("Expecting answer, question or header")

    return state

def state_end(quiz, line_text, line_number):
    """End state."""
    pass
    
##
# The Parser loop

def parse_file(md_script):
    """
    Parses the markdown file one line at a time and returns a Quiz

    :param md_script: list of file lines
	:type md_script: list
    """

    # Create Quiz
    quiz = Quiz()

    # Initialize state machine
    m = StateMachine()
    
    m.add_state("start", state_start)
    m.add_state("parse_header", state_parse_header)
    m.add_state("parse_question", state_parse_question)
    m.add_state("parse_answer", state_parse_answer)
    m.add_state("parse_question_codeblock", state_parse_question_codeblock)
    m.add_state("end", state_end, end_state=1)

    m.set_start("start")

    # Parse file lines
    md_lines = md_script.split(NEW_LINE)
    md_lines.append("EOF")
    line_number = 1
    try:
        for md_row in md_lines:
            md_row = md_row.rstrip('\r')
            md_row = md_row.rstrip('\n')
            
            m.run(quiz, md_row, line_number)

            line_number += 1
        
    except TransitionError as e:
        print("Error at line %d: %s." % (line_number, e))
        quiz = None

    return quiz

######################################################################
# Section 5 - Main
######################################################################

if __name__ == '__main__':
    # very basic argument usage
    if len(sys.argv) > 3:
        print("Usage details: python md2moodle.py <md_file> [stdout]")
        sys.exit()

    try:
        md_file_name = sys.argv[1]

        md_file = open(md_file_name, 'r')
        md_script = md_file.read()

        quiz = parse_file(md_script)

        if quiz:
            if len(sys.argv) > 2:
                #outputs to JSON containing the XML per section
                xml = quiz.export_xml_to_string(md_file_name)
                print(xml)
            else:
                #creates and outputs to XML files
                quiz.export_xml_to_file(md_file_name)
                print("XML file(s) successfully generated!")

    except Exception as e:
        print(e)