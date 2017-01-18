"""
This module has been written to convert transcribed commentaries from text
files to EpiDoc compatible XML, see http://www.stoa.org/epidoc/gl/latest/ 
and http://sourceforge.net/p/epidoc/wiki/Home/ for more information on EpiDoc.

Funding is provided by an ERC funded project studying Arabic commentaries on
the Hippocratic Aphorisms. The Principal Investigator is Peter E. Pormann,
The University of Manchester.


It is anticipated the module will be used via the function process_text_files()
which attempts to to process any file with a .txt extension within a specified
directory. Each text file base name should end in an underscore followed by a
numerical value, e.g. file_1.txt, file_2.txt, etc. The numerical value is
subsequently used when creating the title section <div> element, e.g. 
<div n="1" type="Title_section"> for file_1.txt. 

If processing succeeds two XML files will be created in a folder called XML.
The XML file names start with the text file base name and end in _main.xml (for
the main XML) and _apps.xml (for the apparatus XML). For example for file_1.txt
the XML files will be file_1_main.xml and file_1_app.xml.

If processing fails error messages will be saved to a file with the .err 
extension in the folder ./errors


The commentaries should be utf-8 text files with the following format.

Part 1. A main body of text consisting of:

i.  A first block of text containing an optional intro section and the title,
    if an intro section exists a line containing '++' identifies the division
    between the intro (which comes first) and the title
ii. A series of numbered aphorism/commentary pairs each consisting of: 
    a. A first line containing the aphorism number, this is a numerical value
       followed by the '.' character, i.e. the string 'n.' for aphorism n.
    b. A second line containing the aphorism.
    c. Additional line containing one or more commentaries, each commentary 
       on a single line.
     
This main body of text contains symbols referring to witnesses and footnotes 
in the following formats:

i.  References to witnesses have the form [WW LL] where WW is a code to  
    identify the witness document, and LL is a location in the document.
ii. Footnote references (for textual variations, omissions, additions, correxi
    or conieci) have two forms. Let tttt represent a word of text without a
    variant, vvvv represent a word of text with a variation, and *n* identify
    footnote number n. Form a. is for single word variations, and form b. for
    multiple word variations:
    a. ttt tttt *n*vvvv tttt tttt 
    b. ttt tttt *n*vvvv vvvv vvvv# tttt tttt 
 
Part 2. After the main body of text is the list of numbered and ordered
        footnotes. A footnote is a single line with the following format:
   
i.   The line starts with the footnote number enclosed within a pair of 
     asterisks, e.g. for footnote n the line starts with string '*n*'.
ii.  The footnote contains a mix of witness text (i.e. title, aphorisms and 
     commentary) and symbols devised to describe omissions, additions, 
     correxi, conieci and standard variations obtained by comparing two 
     witness documents.
iii. The footnote line ends with a '.' character.
 
The 5 footnote types should have the following formats, where n is the footnote
number, W1 and W2 are witness codes, and ssss, tttt and uuuu represent segments
of witness text:

Omissions can have only one form.
Form 1: *n*ssss ] W1: om. W2.
This means the text 'ssss' is found in witness W1 but not W2.

Additions can have three forms depending on whether the addition applies to one
or both witnesses, and for the latter case whether the addition is the same or
not for both witnesses.
Form 1: *n*ssss ] add. tttt W1.
This means both witnesses have 'ssss' and W1 adds 'tttt'.
Form 2: *n*ssss ] add. tttt W1, W2.
This means both witnesses have 'ssss', and both add 'tttt' (e.g. the editor 
felt the need to omit tttt).
Form 3: *n*ssss ] add. tttt W1: uuuu W2.
This means both witnesses have 'ssss', W1 adds 'tttt' whereas W2 adds 'uuuu'.

Correxi can have two forms, depending on whether the witness texts are the same
or not.
Form 1: *n*ssss ] correxi: tttt W1, W2.
This means the text 'tttt' is found in witnesses W1 and W2, the editor has
corrected this to 'ssss'.
Form 2: *n*ssss ] correxi: tttt W1: uuuu W2.
This means the text 'tttt' is found in witness W1, whereas W2 has 'uuuu'. The
editor has corrected these to 'ssss'.

Conieci can have two forms, depending on whether the witness texts are the same
or not.
Form 1: *n*ssss ] conieci: tttt W1, W2.
This means the text 'tttt' is found in witnesses W1 and W2, the editor
conjectures that this should be 'ssss'.
Form 2: *n*ssss ] conieci: tttt W1: uuuu W2.
This means the text 'tttt' is found in witness W1, whereas W2 has 'uuuu'. The
editor conjectures that these should be 'ssss'.

Standard variations can have only one form.
Form 1: *n*ssss ] W1: tttt W2.
This means witness W1 has text 'ssss' whereas W2 has 'tttt'.


This module generates the EpiDoc XML to sit within the <body> element. A
suitable XML template file containing all other XML is also required. The
template file should contain the string '#INSERT#' at the location where 
additional EpiDoc XML should be inserted, e.g. 

<TEI .... >
<teiHeader>
    ....
</teiHeader>
    <text>
        <body>   
#INSERT#             
        </body>
    </text>
</TEI>


The XML <div> elements generated are:
 - intro (optional)
 - Title_section (numbered)
 - aphorism_commentary_unit (numbered)
 - commentary (within aphorism_commentary_unit)
 - aphorism (within aphorism_commentary_unit)

Written by Jonathan Boyle, IT Services, The University of Manchester. 
"""


# Import the string and os modules
import string, os


# Define an Exception
class StringProcessingException(Exception):
    pass


def process_references(text): 
    """
This helper function searches a line of text for witness references with the
form [WW LL] and returns a string containing the original text with each
witness reference replaced with XML with the form
<locus target="WW">LL</locus>.

'\\n' characters are added at the start and end of each XML insertion so each
instance of XML is on its own line.

It is intended this function is called by function process_file() for each line
of text from the main body of the text document before processing footnote
references using the process_footnotes() function. 
    """
    
    # Create a string to contain the return value
    result = ''
    
    while True:
        # Try to partition this line at the first '[' character
        text_before, sep, text_after = text.partition('[')
     
        # Note: if sep is zero there are no more witnesses to add
     
        # Add text_before to the result string
        if len(text_before) > 0:
            result += text_before
            # If there is a witness to add start a new line
            if len(sep) > 0:
                result += '\n'
    
        # If sep has zero length we can stop because there are no more 
        # witness references
        if len(sep) == 0: 
            break
       
        # Try to split text_after at the first ']' character
        reference, sep, text = text_after.partition(']')
    
        # If this partition failed then something went wrong, so throw an error
        if len(sep) == 0:
            raise StringProcessingException('Unable to partition string at "]" when looking for a reference')
            
        # Partition the reference into witness and location (these are 
        # separated by the ' ' character)
        witness, sep, page = reference.partition(' ')
        
         # If this partition failed there is an error
        if len(sep) == 0:
            raise StringProcessingException('Unable to partition reference {} because missing " " character'.format(reference))

        # Add the witness and location XML to the result string
        result += '<locus target="' + witness + '">' + page + '</locus>'
        
        # If text has zero length we can stop
        if len(text) == 0:
            break
        else:
            # There is more text to process so start a new line
            result += '\n'
        
    return result
    
    
    
def process_omission(footnote, xml_app, oss='    '):
    """    
This helper function processes a footnote line describing an omission, i.e.
footnotes which contain the string 'om.'.

The textual variation MUST include only only two witnesses, hence omissions
with two witnesses are not allowed since it would make no sense for both
witnesses to omit the same text. Therefore the following should be true:
1. The footnote line contains one colon character.
2. The footnote line doesn't contain commas.

The first input argument must be the footnote line with the following stripped
from the start and end of the string:
1. All whitespace
2. '*n*' (where n is the footnote number) from the start of the string
3. '.' character from the end of the string

The footnote is expected to contain a single ':' character and have the 
following format:
1. The footnote line before the ':' character is a string of witness text, 
   followed by the ']' character, followed by a single witness code.
2. The footnote line after the ':' character contains an 'om.' followed by a 
   single witness code.

The second input argument should be a list containing the apparatus XML, this 
function will add XML to this list.

The third input argument is the string defining a unit of offset in the XML, 
this defaults to four space characters.

It is intended this function is called by process_footnotes() for omission
footnotes.
""" 
       
    # Partition the footnote line at ':'
    part1, sep, part2 = footnote.partition(':')
                
    # Partition part1 at ']'
    text, sep, wit = part1.partition(']')
             
    # Remove whitespace from text
    text = text.strip()

    # Add the witness to the XML (remember to strip whitespace)
    xml_app.append(oss + '<rdg wit="#' + wit.strip() + '">' + text + '</rdg>')
                
    # Partition part2 at 'om.' to extract witness
    junk, sep, wit = part2.partition('om.')
    
   # Add witness to the XML
    xml_app.append(oss + '<rdg wit="#' + wit.strip() + '">')
    xml_app.append(oss*2 + '<gap reason="omission"/>')
    xml_app.append(oss + '</rdg>')      
    
    
     
def process_addition(footnote, xml_app, oss='    '):
    """    
This helper function processes a footnote line describing an addition, i.e.
footnotes containing the string 'add.'

The textual variation must include only only two witnesses, however additions 
with two witnesses are are allowed, and this function will work with multiple
witnesses.  

The first input argument must be the footnote line with the following stripped
from the start and end of the string:
1. All whitespace
2. '*n*' (where n is the footnote number) from the start of the string
3. '.' character from the end of the string 

The footnote is expected to include the string 'add.'. The text after 'add.' 
should have one of the following formats:
format 1: the witness text followed by a space and a single witness code
format 2: the witness text followed by a space and multiple witnesses codes 
          separated by commas
format 3: multiple pairs of witness text + witness code, each pair separated
          by a ':' character

The text before the string 'add' is not important for this function. 

The second input argument should be a list containing the apparatus XML, this 
function will add XML to this list.

The third input argument is the string defining the unit of offset for the XML,
this default to four space characters.

It is intended this function is called by process_footnotes() for addition
footnotes.
   """
    
    # Partition the footnote line at add.
    junk, sep, part2 = footnote.partition('add.')
                            
    # Now process part2, which could have one of two formats
    # 1. Multiple text/witness pairs, each separated by :
    # 2. Single text and one or more witness(es), multiple witnesses are
    #    separated by ','
            
    # Deal with case 1                    
    if ':' in part2:
        # Split part2 at ':' (remove whitespace first)
        part2 = part2.strip().split(':')
        
        for variant in part2:            
            # Strip whitespace and partition at last ' '
            text, sep, wit = variant.strip().rpartition(' ') 
            
            # Add to the XML
            xml_app.append(oss + '<rdg wit="#' + wit + '">')
            xml_app.append(oss*2 + '<add reason="add_scribe">' + text.strip() + '</add>')
            xml_app.append(oss + '</rdg>')              
            
    else:
            # Deal with case 2
            wits = []
            text = part2
            
            # First deal with sources after ',' by partitioning at last comma
            while ',' in text:
                text, sep, wit = text.rpartition(',')
                wits.append(wit.strip())
            
            # Partition at last ' '
            text, sep, wit = text.rpartition(' ')
            wits.append(wit)
            
            # Add the witness XML
            for wit in wits:
                xml_app.append(oss + '<rdg wit="#' + wit + '">')
                xml_app.append(oss*2 + '<add reason="add_scribe">' + text.strip() + '</add>')
                xml_app.append(oss + '</rdg>')  
  
  
    
def process_correxi(footnote, xml_app, oss='    '):
    """    
This helper function processes a footnote line describing correxi, i.e.
corrections by the editor, these contain the string 'correxi'.

The first input argument must be the footnote line with the following stripped
from the start and end of the string:
1. All whitespace
2. '*n*' (where n is the footnote number) from the start of the string
3. '.' character from the end of the string

The footnote is expected to contain at least one ':' character and have the 
following format:
1. The footnote line before the first ':' character contains a string of
   witness text, followed by a ']' character.
2. The footnote line after the ':' character has one of two formats:
   format 1: multiple pairs of witness text + witness code, each pair separated
             by a ':' character
   format 2: a single witness text followed by a space and a list of comma
             separated witness codes
             
The second input argument should be a list containing the apparatus XML, this 
function will add XML to this list.

The third input argument is a string defining the unit of offset for the XML,
this defaults to four space characters.

It is intended this function is called by process_footnotes() for correxi
footnotes.
    """
    
    # Partition at first ':'
    part1, sep, part2 = footnote.partition(':')
               
    # Partition part 1 at ']'
    text, sep, junk = part1.partition(']')
            
    # Add text xml_app
    xml_app.append(oss + '<rdg>')
    xml_app.append(oss*2 + '<choice>')
    xml_app.append(oss*3 +  '<corr>' + text.strip() + '</corr>')
    xml_app.append(oss*2 + '</choice>')
    xml_app.append(oss + '</rdg>')
                        
    # Now process part2, which could have one of two formats
    # 1. Multiple text/witness pairs, each separated by :
    # 2. Single text and witness(es), multiple witnesses are separated by ','
            
    # Deal with case 1                    
    if ':' in part2:
        # Split part2 at ':' (remove whitespace first)
        variants = part2.strip().split(':')
        
        for var in variants:
            # Strip whitespace and partition at last ' '
            text, sep, wit = var.strip().rpartition(' ') 
            
            # Add to the XML
            xml_app.append(oss + '<rdg wit="#' + wit + '">' + text + '</rdg>')
            
    else:
            # Deal with case 2
            wits = []
            text = part2
            
            # First deal with sources after ','
            while ',' in text:
                text, sep, wit = text.rpartition(',')
                wits.append(wit.strip())
            
            # Partition at last ' '
            text, sep, wit = text.rpartition(' ')
            wits.append(wit)
            
            # Add the witness XML
            for wit in wits:
                xml_app.append(oss + '<rdg wit="#' + wit + '">' + text.strip() + '</rdg>')
  
    

def process_conieci(footnote, xml_app, oss='    '):
    """    
This helper function processes a footnote line describing a conieci, i.e.
conjectures by the editor, these contain the string 'conieci'.

The first input argument is the footnote line with following stripped from the
start and end of the string:
1. All whitespace
2. '*n*' (where n is the footnote number) from the start of the string
3. '.' character from the end of the string

The footnote is expected to contain at least one ':' character and have the 
following format:
1. The footnote line before the first ':' character contains a string of 
   witness text followed by a ']' character.
2. The footnote line after the ':' character has one of two formats:
   format 1: multiple pairs of variant + witness, each separated by the ':' 
             character
   format 2: a single variant followed by a space and a list of comma separated
             witnesses
             
The second input argument should be a list containing the apparatus XML, this 
function will add XML to this list.

The third input argument is the string defining a unit of offset for the XML,
this defaults to four space characters.

It is intended this function is called by process_footnotes() for conieci
footnotes.
    """
    
    # Partition at first ':'
    part1, sep, part2 = footnote.partition(':')
            
    # Partition part 1 at ']'
    text, sep, junk = part1.partition(']')

    # Add text xml_app
    xml_app.append(oss + '<rdg>')
    xml_app.append(oss*2 + '<choice>')
    xml_app.append(oss*3 +  '<corr type="conjecture">' + text.strip() + '</corr>')
    xml_app.append(oss*2 + '</choice>')
    xml_app.append(oss + '</rdg>')
            
    # Now process part 2, which could have one of two formats
    # 1. Multiple variants/witnesses separated by :
    # 2. Single textual variant and witnesses separated by ','
                        
    # Deal with case 1                    
    if ':' in part2:
        # Split part2 at ':' (remove whitespace first)
        vars = part2.strip().split(':')
                
        for var in vars:
            # Strip whitespace and partition at last ' '
            text, sep, wit = var.strip().rpartition(' ') 
                    
            # Add to the XML
            xml_app.append(oss + '<rdg wit="#' + wit + '">' + text + '</rdg>')
        
    else:
        # Deal with case 2
        wits = []
        text = part2
        
        # First deal with sources after ','
        while ',' in text:
            text, sep, wit = text.rpartition(',')
            wits.append(wit.strip())
            
        # Partition at last ' '
        text, sep, wit = text.rpartition(' ')
        wits.append(wit)
            
        # Add the witness XML
        for wit in wits:
            xml_app.append(oss + '<rdg wit="#' + wit + '">' + text.strip() + '</rdg>')



def process_standard_variant(footnote, xml_app, oss='    '):
    """    
This helper function processes a footnote line describing a standard textual 
variation, i.e. not an omission, addition, correxi or conieci.

The textual variation MUST include only only two witnesses, hence the following
should be true:
1. The footnote line should contain one colon character.
2. The footnote line should not contain commas.

The first input argument is the footnote line with the following stripped from
the start and end of the string:
1. All whitespace
2. '*n*' (where n is the footnote number) from the start of the string
3. '.' character from the end of the string 

The footnote is expected to contain one ':' character and have the following
format:
1. Before the colon is witness text, followed by a ']' character, followed by
   a witness code.
2. After the colon is witness text, followed by a final space character, 
   followed by a witnesses code.

The second input argument should be a list containing the apparatus XML, this 
function will add XML to this list.

The third input argument is the string defining a unit of offset for the XML, 
this defaults to four space characters.

It is intended this function is called by process_footnotes() for footnotes
describing standard variations.
    """        
   
    # Split this footnote line at the ':' character
    part1, sep, part2 = footnote.partition(':')
               
    # Split part 1 at the ']' character to separate the text from the witness
    text, sep, wits = part1.partition(']')
            
    # Remove whitespace from text
    text = text.strip()        
    
    # Add the single witness to the XML (remember to strip whitespace)    
    xml_app.append(oss + '<rdg wit="#' + wits.strip() + '">' + text.strip() + '</rdg>')
     
    # Process the single witness by partitioning part2 at last ' '
    text, sep, wit = part2.rpartition(' ')
    
    # Add the single witness to the XML (remember to strip whitespace)    
    xml_app.append(oss + '<rdg wit="#' + wit + '">' + text.strip() + '</rdg>') 
    
    

def process_footnotes(string_to_process, next_footnote, footnotes, n_offset=0, oss='    '):    
    """
This helper function takes a single string containing text and processes any
embedded footnote symbols (describing additions, omissions, correxi, conieci
and standard textual variations) to generate XML. It also deals with any XML
generated using function process_references().
The output is two lists of XML, one for the main text, the other for the 
apparatus.

Input arguments:

string_to_process This string contains the text to be processed. This should 
                  contain a single line from the text file being processed, 
                  e.g. a title, aphorism or commentary. 
                  This string may already contain XML generated using the 
                  process_references() function i.e. XML identifying witnesses
                  with each <locus> XML on a new line.
next_footnote     This is the number of the next footnote to be located and
                  processed. 
footnotes         This is a Python list containing all the footnotes, i.e. 
                  obtained from the end of the text file being processed. 
n_offset          This is the number of offsets to use when creating the main
                  XML to be inserted in the <body> element in the XML template 
                  file. The default value is 0.
oss               A string defining the unit of offset in the XML, the default
                  value is four space characters.

Output arguments:

1. A Python list containing XML for the main text.
2. A Python list containing XML for the critical apparatus. 
3. The number of the next footnote to be processed when this function completes.
                  
It is intended this function is called by process_file() on each line of text
from the main document body. 
    """
    
    # Create lists to contain the XML
    xml_main = []
    xml_app = []

    while True:
     
        # Use string partition to try to split this text at the next footnote symbol
        footnote_symbol = '*' + str(next_footnote) + '*'
        text_before_symbol, sep, string_to_process = string_to_process.partition(footnote_symbol)
        
        # If the partition failed sep will have zero length and the next 
        # footnote is not in this line, hence we can stop processing and return
        if len(sep) == 0:
            # Add text_before_symbol to the XML and stop processing      
            for next_line in text_before_symbol.splitlines():
                xml_main.append(oss*n_offset + next_line.strip())
            break
    
        # We know sep has non-zero length and we are dealing with a footnote.
        # Now use string partition to try to split text_before_symbol at a '#'
        # character.
        next_text_for_xml, sep, base_text = text_before_symbol.partition('#')
        
        # If the above partition failed the footnote refers to a single word
        if len(sep) == 0:
            # Use rpartition to partition at the LAST space in the
            # string before the footnote symbol 
            next_text_for_xml, sep, base_text = text_before_symbol.rpartition(' ')
            
        # Check we succeeded in partitioning the text before the footnote
        # at '#' or ' '. If we didn't there's an error.
        if len(sep) == 0:
            raise StringProcessingException('Unable to partition text before footnote symbol {}'.format(footnote_symbol))
            
        # Add the next_text_for_xml to xml_main
        for next_line in next_text_for_xml.splitlines():
            xml_main.append(oss*n_offset + next_line.strip())                    
        
        # Create XML for this textural variation for xml_main
        next_string = '<app n="' \
                    + str(next_footnote) \
                    + '" type="footnote" xml:id="begin_fn' \
                    + str(next_footnote) \
                    + '"><rdg>' \
                    + base_text \
                    + '</rdg><anchor xml:id="end_fn' \
                    + str(next_footnote) \
                    + '"/>'
        
        # Add next_string to the xml_main, remember this may contain '\n'
        # characters and XML from a witness reference                 
        for next_line in next_string.splitlines():
            xml_main.append(oss*n_offset + next_line)
                     
        # Close the XML for the main text
        xml_main.append(oss*n_offset + '</app>')
        
        # Add initial XML to xml_app (for the apparatus XML file)
        xml_app.append('<app> from="#begin_fn' + str(next_footnote) + \
                        '" to="#end_fn' + str(next_footnote) + '">')
        
        # Get the corresponding footnote
        footnote_line = footnotes[next_footnote-1]
        
        # Use rstrip to remove whitespace and the '.' character from the end
        # of the footnote string
        footnote_line = footnote_line.rstrip(' .')
        
        # Use partition to remove the footnote symbol from the start of 
        # footnote_line
        junk, sep, footnote_line = footnote_line.partition(footnote_symbol)
        
        # Now process the footnote line - deal with each case individually to 
        # aid readability and make future additions easier
        processed = False        
        
        # Now process the footnote

        # Case 1 - omission
        if not processed and 'om.' in footnote_line:
            process_omission(footnote_line, xml_app, oss)
            processed = True
            
        # Case 2 - addition
        if not processed and 'add.' in footnote_line:
            process_addition(footnote_line, xml_app, oss)      
            processed = True
            
        # Case 3 - correxi
        if not processed and 'correxi' in footnote_line:
            process_correxi(footnote_line, xml_app, oss)      
            processed = True
            
        # Case 4 - conieci
        if not processed and 'conieci' in footnote_line:
            process_conieci(footnote_line, xml_app, oss)      
            processed = True
            
        # Remaining case - standard variation
        if not processed:
            process_standard_variant(footnote_line, xml_app, oss) 
            processed = True

        # Close the XML
        xml_app.append('</app>')
                         
        # Increment the footnote number
        next_footnote += 1

        # Test to see if there is any more text to process
        if len(string_to_process) == 0:
            break

    return xml_main, xml_app, next_footnote



def get_next_non_empty_line(text, next_line_to_process=0):
    """
A helper function to get the next non-empty line in a list of strings, i.e. a 
function to bypass empty lines
.
The input arguments are:

text                    a list containing the lines of text
next_line_to_process    location in list to start looking for next empty line

The output arguments are:

1. The first non-empty line found
2. The next location in the list to look for a non-empty line
    """
    
    while True:
        
        # Get next line and remove whitespace 
        line = text[next_line_to_process].strip()
       
        # Ignore empty lines
        if len(line) == 0:
            next_line_to_process += 1
        else:
            break
     
    next_line_to_process += 1
    return line, next_line_to_process



def test_footnotes(footnotes):
    """
A function to test all footnotes have the correct format. The input argument 
should be a python list containing the footnotes.
The function returns a python list containing the error messages.
    """
    
    # Initialise n_footnote
    n_footnote = 1

    # Initialise list to hold error messages
    errors = [] 
    
    for footnote in footnotes:
       
        # Strip any whitespace
        footnote = footnote.strip()       
       
        # Discard any empty lines
        if len(footnote) == 0:
            continue
        
        # Test there are two '*' characters
        if footnote.count('*') != 2:
            error = 'Error in footnote ' + str(n_footnote) + ': should contain two "*" characters'
            errors.append(error)        
         
        # Test the first character is a '*' and remove it
        if footnote[0] != '*':
            error = 'Error in footnote ' + str(n_footnote) + ': first character is not an "*"'
            errors.append(error)
        footnote = footnote.lstrip('*')
        
        # Test the last character is a '.'
        if footnote[-1] != '.':
            error = 'Error in footnote ' + str(n_footnote) + ': last character is not an "."'
            errors.append(error)

        # Partition at the next '*' and check the footnote number
        n, sep, footnote = footnote.partition('*')
        
        if int(n) != n_footnote:
            error = 'Error in footnote ' + str(n_footnote) + ': expected footnote ' + \
                str(n_footnote) + ' but found footnote ' + n
            errors.append(error)
        
        # Check the footnote contains one ']'
        if footnote.count(']') != 1:
            error = 'Error in footnote ' + str(n_footnote) + ': should contain one "]" character'
            errors.append(error)        
        
        # Check for known illegal characters
        # If contains a 'codd' give an error and stop further processing
        if 'codd' in footnote:
            error = 'Error in footnote ' + str(n_footnote) + ': contains "codd"'
            errors.append(error)    
            n_footnote += 1
            continue
        
        # If contains a ';' give an error and stop further processing
        if ';' in footnote:
            error = 'Error in footnote ' + str(n_footnote) + ': contains ";"'
            errors.append(error)
            n_footnote += 1
            continue
        
        processed = False
                    
        # Test omission has the correct format
        # Errors tested for:
        # - should not contain any ','
        # - should contain one ':'
        # - text after ':' should be ' om. '
        if not processed and 'om.' in footnote:

            processed = True
            
            if ',' in footnote:
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': omission should not contain "," character'
                errors.append(error)
                
            if footnote.count(':') != 1:
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': omission should contain one ":" character'
                errors.append(error)
               
            part1, sep, part2 = footnote.partition(':')
            if part2[0:5] != ' om. ':
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': omission must contain " om. " after ":"'
                errors.append(error)

        # Test addition has the correct format
        # Errors tested for:
        #  - text after ']' should be ' add. '
        if not processed and 'add.' in footnote:
            
            processed = True
            
            part1, sep, part2 = footnote.partition(']')
            if part2[0:6] != ' add. ':
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': addition must contain " add. " after "]"'
                errors.append(error)
    
        # Test correxi have the correct format
        # Errors tested for:
        # - text after ']' should be ' correxi: '
        if not processed and 'correxi' in footnote:
            
            processed = True
            
            # Partition at ']'
            part1, sep, part2 = footnote.partition(']')
            
            if part2[0:10] != ' correxi: ':
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': correxi must contain " correxi: " after "]"'
                errors.append(error)
    
        # Test conieci have the correct format
        # Errors tested for:
        # - text after ']' should be ' conieci: '
        if not processed and 'conieci' in footnote:
            
            processed = True
            
            # Partition at ']'
            part1, sep, part2 = footnote.partition(']')
            
            if part2[0:10] != ' conieci: ':
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': conieci must contain " conieci: " after "]"'
                errors.append(error)
         
        # Test standard variations have the correct format
        # Errors tested for:
        # - should not contain any ','
        # - should contain one ':'
        if not processed:
      
            if ',' in footnote:
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': standard variation should not contain "," character'
                errors.append(error)
                
            if footnote.count(':') != 1:
                error = 'Error in footnote ' + str(n_footnote) + \
                    ': standard variation should contain one ":" character'
                errors.append(error)
    
        # Increment footnote number
        n_footnote += 1
        
    return errors



def save_error(base_name, error_messages):
    """
A helper function to save error messages to file. The input arguments are

base_name: the base name for the error file
error_messages: a list containing the error messages

Error messages will be saved to a file with the .err extension in the folder 
./errors
    """
    
    if not os.path.exists('./errors'):
        os.mkdir('./errors')
        
    with open('./errors/' + base_name + '.err', 'w' ,encoding="utf-8") as f:
        for e in error_messages:
            f.write(e + '\n')



def process_file(folder, text_file, template_file, n_offset=0, oss ='    '):
    """
A function to process a text file containing symbols representing references to
witnesses and symbols and footnotes defining textual variations, omissions,
additions, correxi or conieci. This function uses these symbols to produce
files containing EpiDoc compatible XML.

The input arguments are:

folder          The folder containing the text file
text_file       The name of the text file
template_file   The name of the XML template file containing the string 
                '#INSERT#' at the location in which to insert XML for the 
                <body> element.
n_offset        The number of offsets to use when creating the XML inserted in
                the <body> element in the main XML template file. The default
                value is 0.
oss             A string defining the unit of offset in the XML, default value
                is four space characters.

The text file base name is expected to end with an underscore followed by a 
numerical value, e.g. file_1.txt, file_2.txt, etc. This numerical value is 
used when creating the title section <div> element, e.g. 
<div n="1" type="Title_section"> for file_1.txt.

If processing succeeds two XML files will be created in folder ./XML with file
names that start with the text file base name and ending in _main.xml (for the
main XML) and _apps.xml (for the apparatus XML). For example for file_1.txt the
XML files will be file_1_main.xml and file_1_app.xml.

Error messages are saved in a file in the ./errors folder.

After successful processing the function returns True, if an error is detected
this function returns False.

It is intended this function is called by process_text_files().
    """
    
    # Open the file
    with open(folder+'/'+text_file,'r',encoding="utf-8") as f:
        # Read in file
        full_text = f.read()
        
    # Extract the file basename
    base_name, sep, rhs = text_file.rpartition('.')
    if len(sep) == 0:
        message = ['Error processing document: {}'.format(text_file)]
        message.append('  File name has incorrect format')
        save_error(text_file, message)
        return False
        
    # Delete any error file associated with this text file
    if os.path.isfile('./errors/' + base_name + '.err'):
        os.remove('./errors/' + base_name + '.err')
        
    # Set XML file names
    xml_main_file = './XML/' + base_name + '_main.xml'
    xml_app_file  = './XML/' + base_name + '_app.xml'
    
    # Extract the document number, it is expected this is at the end of the 
    # base name following an '_'
    junk, sep, doc_num = base_name.rpartition('_')
    if len(sep) == 0:
        message = ['Error processing document: {}'.format(text_file)]
        message.append('  File name has incorrect format')
        save_error(base_name, message)
        return False

    # Find where text containing the block of footnotes starts, i.e. the 
    # last line containing '*1*', if this fails write to the error file and 
    # return
    fn_start = full_text.rfind('*1*')
    if fn_start == -1:
        message = ['Error processing document: {}'.format(text_file)]
        message.append('  Problem finding location of "*1*"')
        save_error(base_name, message)
        return False
    
    # Check this is different to the first location of *1*, if this isn't true
    # write to the error file and return
    fn1_ref_loc = full_text.find('*1*')
    if fn1_ref_loc == fn_start:
        message = ['Error processing document: {}\n'.format(text_file)]
        message.append('  Can only find one instance of "*1*"\n')  
        save_error(base_name, message)        
        return False
        
    # Check whether this document has an optional intro section, if it has it
    # will contain the characters '++' in the main text
    if '++' in full_text[:fn_start]:
        include_intro = True
    else:
        include_intro = False        
    
    # Split the file into the main text and the footnotes
    # NOTE: this wastes memory as it takes an extra copy of the text in the 
    # file, hence for large files it would be better to modify to use
    # fn_txt_start to define an offset when accessing the footnotes.
    main_text = full_text[:fn_start].splitlines()
    footnotes = full_text[fn_start:].splitlines()
    
    # Test the footnotes
    errors = test_footnotes(footnotes)
    
    # If there are errors save them to file and return
    if len(errors) != 0:
        save_error(base_name, errors)      
        return False
         
    #Create lists to contain the XML
    xml_main = []
    xml_app = []

    # Initialise footnote number
    next_footnote_to_find = 1

    # Initialise number of the next line of text to process 
    # (Python indexing starts at 0)
    next_line_to_process = 0
    
    # Define string in template_file which identifies the location for 
    # inserting the main XML
    template_marker = '#INSERT#'

    # Deal with the first block of text which should contain an optional intro and the title
    # ======================================================================================

    # First deal with intro (if there is one)
    # ---------------------
    if include_intro:
        # Generate the opening XML for the intro
        xml_main.append(oss*n_offset + '<div type="intro">')
        xml_main.append(oss*(n_offset+1) + '<p>')
        
        # Get the next line of text
        line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)        
        
        # Loop over lines of text containing the intro
        process_more_intro = True
        
        while process_more_intro:
            
            # Process any witnesses in this line. If this fails with a 
            # StringProcessingException print an error and return
            try:
                line_ref = process_references(line)
            except StringProcessingException as err:
                message = ['Error processing document: {}'.format(text_file)]
                message.append('  Unable to process references in line {} (document intro)\n'.format(next_line_to_process))
                message.append('  Message: ' + str(err))
                save_error(base_name, message)
                return False
            
            # Process any footnotes in line_ref. If this fails with a 
            # StringProcessingException print an error and return
            try:
                xml_main_to_add, xml_app_to_add, next_footnote_to_find = \
                process_footnotes(line_ref, next_footnote_to_find, footnotes, n_offset+2,oss)
            except StringProcessingException as err:
                message = ['Error processing document: {}'.format(text_file)]
                message.append('  Unable to process footnotes in line {} (document intro)'.format(next_line_to_process))
                message.append('  Message: ' + str(err))
                save_error(base_name, message)
                return False
            
            # Add to the XML
            xml_main.extend(xml_main_to_add)
            xml_app.extend(xml_app_to_add)
            
            # Get the next line and test if we have reached the end of the intro
            line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)       
            if '++' == line:
                process_more_intro = False
        
        # Add XML to close the intro section
        xml_main.append(oss*(n_offset+1) + '</p>')
        xml_main.append(oss*n_offset + '</div>')
     
     
    # Now process the title 
    # ---------------------
       
    # Generate the opening XML for the title
    xml_main.append(oss*n_offset + '<div n="' + doc_num + '" type="Title_section">')
    xml_main.append(oss*(n_offset+1) + '<ab>')

    # Get the first non-empty line of text
    line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)
    
    # Loop over the lines in the title
    process_more_title = True
    
    while process_more_title:
    
        # Process any witnesses in this line. If this raises an exception then
        # print an error message and return
        try:
            line_ref = process_references(line)
        except StringProcessingException as err:
            message = ['Error processing document: {}'.format(text_file)]
            message.append('  Unable to process references in line {} (title line)'.format(next_line_to_process))
            message.append('  Message: ' + str(err))
            save_error(base_name, message)
            return False
    
        # Process any footnotes in line_ref, if this fails print to the error
        # file and return
        try:
            xml_main_to_add, xml_app_to_add, next_footnote_to_find = \
                process_footnotes(line_ref, next_footnote_to_find, footnotes, n_offset+2,oss)
        except StringProcessingException as err:
            message = ['Error processing document: {}'.format(text_file)]
            message.append('  Unable to process footnotes in line {} (title line)'.format(next_line_to_process))
            message.append('  Message: ' + str(err))
            save_error(base_name, message)
            return False
        
        # Add the return values to the XML lists
        xml_main.extend(xml_main_to_add)
        xml_app.extend(xml_app_to_add)
        
        # Get the next line of text
        line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)
        
        # Test if we have reached the first aphorism
        if line == '1.':
            process_more_title = False
            
    # Close the XML for the title
    xml_main.append(oss*(n_offset+1) + '</ab>')
    xml_main.append(oss*n_offset + '</div>')

    # Now process the rest of the main text
    # =====================================
    
    # Initialise n_aphorism    
    n_aphorism = 1
        
    while next_line_to_process < len(main_text):
        
        # Check the text in this line contains the correct aphorism number
        # If it doesn't print a message and stop
        if line[:-1] != str(n_aphorism):
            message = ['Error processing document: {}'.format(text_file)]
            message.append('  Unable to find expected aphorism number ({}) in line {}'.format(n_aphorism,next_line_to_process))
            message.append('  Instead line {} contains the value: {}\n'.format(next_line_to_process-1,line[:-1]))
            save_error(base_name, message)
            return False
            
        # Add initial XML for the aphorism + commentary unit
        xml_main.append(oss*n_offset + \
            '<div n="' + \
            str(n_aphorism) + \
            '" type="aphorism_commentary_unit">')
        
        # Add initial XML for this aphorism
        xml_main.append(oss*(n_offset+1) + '<div type="aphorism">')
        xml_main.append(oss*(n_offset+2) + '<p>')
          
        # Get the next line of text 
        line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)  
        
        # Now process any witnesses in it. If this fails with a 
        # StringProcessingException print an error and return
        try:
            line_ref = process_references(line)
        except StringProcessingException as err:
            message = ['Error processing document: {}'.format(text_file)]
            message.append('  Unable to process references in line {} (aphorism {})'.format(next_line_to_process,n_aphorism))
            message.append('  Message: ' + str(err))
            save_error(base_name, message)
            return False

        # Process any footnotes in line_ref, if there are errors write to the 
        # error file and return
        try:
            xml_main_to_add, xml_app_to_add, next_footnote_to_find = \
                process_footnotes(line_ref, next_footnote_to_find, footnotes, n_offset+3,oss)
        except StringProcessingException as err:
            message = ['Error processing document: {}'.format(text_file)]
            message.append('  Unable to process footnotes in line {} (aphorism {})'.format(next_line_to_process,n_aphorism))
            message.append('  Message: ' + str(err))
            save_error(base_name, message)
            return False
            
        # Add the XML
        xml_main.extend(xml_main_to_add)
        xml_app.extend(xml_app_to_add)
        
        # Close the XML for the aphorism
        xml_main.append(oss*(n_offset+2) + '</p>')
        xml_main.append(oss*(n_offset+1) + '</div>')
        
        # Get the next line of text
        line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)          
        
        # Now loop over commentaries     
        process_more_commentary = True
        
        while process_more_commentary:
        
            # Add initial XML for this aphorism's commentary
            xml_main.append(oss*(n_offset+1) + '<div type="commentary">')
            xml_main.append(oss*(n_offset+2) + '<p>')
        
            # Now process any witnesses in this line. If this fails with a 
            # StringProcessingException print an error and return
            try:
                line_ref = process_references(line)
            except StringProcessingException as err:
                message = ['Error processing document: {}'.format(text_file)]
                message.append('  Unable to process references in line {} (commentary for aphorism {})\n'.format(next_line_to_process,n_aphorism))
                message.append('  Message: ' + str(err))
                save_error(base_name, message)
                return False
                
            # Process any footnotes in line_ref. If this fails with a 
            # StringProcessingException print an error and return
            try:
                xml_main_to_add, xml_app_to_add, next_footnote_to_find = \
                process_footnotes(line_ref, next_footnote_to_find, footnotes, n_offset+3,oss)
            except StringProcessingException as err:
                message = ['Error processing document: {}'.format(text_file)]
                message.append('  Unable to process footnotes in line {} (commentary for aphorism {})'.format(next_line_to_process,n_aphorism))
                message.append('  Message: ' + str(err))
                save_error(base_name, message)
                return False
        
            # Add the XML
            xml_main.extend(xml_main_to_add)
            xml_app.extend(xml_app_to_add)
        
            # Close the XML for this commentary
            xml_main.append(oss*(n_offset+2) + '</p>')
            xml_main.append(oss*(n_offset+1) + '</div>')
            
            # If there are more lines to process then get the next line and
            # test if we have reached the next aphorism
            if next_line_to_process < len(main_text):
                line, next_line_to_process = get_next_non_empty_line(main_text, next_line_to_process)       
                if line[:-1].isdigit():                
                    process_more_commentary = False
            else:
                break
            
        # Close the XML for the aphorism + commentary unit
        xml_main.append(oss*n_offset +'</div>')
        
        # Increment the aphorism number          
        n_aphorism += 1
    
    # Create output files
    # ===================
    
    # Create folder for XML
    if not os.path.exists('./XML'):
        os.mkdir('./XML')
    
    # Embed xml_main into the XML in the template
    
    # Open the template file
    f = open(template_file, 'r' ,encoding="utf-8")
    
    # Read in template file
    template = f.read()
    f.close()
    
    # Split the template at template_marker
    part1, sep, part2 = template.partition(template_marker)

    # Test the split worked     
    if len(sep) == 0:
        message = ['Error processing document: {}'.format(text_file)]
        message.append('  Unable to find template marker text ({}) in file {}'.format(template_marker,template_file))
        save_error(base_name, message)
        return False
                
    # Save main XML to file
    with open(xml_main_file, 'w' ,encoding="utf-8") as f:
    
        f.write(part1)

        for s in xml_main:
            f.write(s + '\n')
        
        f.write(part2)
    
    # Save app XML to file
    with open(xml_app_file, 'w' ,encoding="utf-8") as f:

        for s in xml_app:
            f.write(s + '\n')
    
    return True



def process_text_files(text_folder, template_file, n_offset=0, offset_size=4):    
    """
A function to process all files with the .txt extension in a directory. These
files are expected to be utf-8 text files containing symbols representing
references to witnesses and symbols and footnotes defining textual variations,
omissions, additions, correxi or conieci. For each text file this function will
attempt to use the symbols to produce files containing EpiDoc compatible XML.

The text file base name is expected to end with an underscore followed by a 
numerical value, e.g. file_1.txt, file_2.txt, etc. This numerical value is 
used when creating the title section <div> element, e.g. 
<div n="1" type="Title_section"> for file_1.txt. 

The input arguments are:

text_folder     The folder containing the text file
template_file   The name of the XML template file containing the string 
                '#INSERT#' at the location in which to insert XML for the 
                <body> element.
n_offset        The number of offsets to use when creating the XML inserted in
                the <body> element in the main XML template file. The default
                value is 0.
offset_size     The number of space characters to use for each XML offset. The
                default value is 4.

If processing succeeds two XML files will be created in folder ./XML with file
names starting with the text file base name and ending in _main.xml (for the
main XML) and _apps.xml (for the apparatus XML). For example for file_1.txt the
XML files will be file_1_main.xml and file_1_app.xml.

If processing fails error messages will be saved to a file with the .err 
extension in the folder ./errors
    """

    # Test that the template file exists
    if not os.path.isfile('./' + template_file):
        print('Error: template file {} not found'.format(template_file))
        return    
    
    
    # Test that the working folder exists
    if not os.path.exists(text_folder):
        print('Error: path {} for text files not found'.format(text_folder))
        return
    
    files = os.listdir(text_folder)
    
    for file in files:
        if file.endswith(".txt"):
            print('Processing: {}'.format(file))
            success = process_file(text_folder, file, template_file, n_offset, ' '*offset_size)
            
            # Test for success
            if not success:
                print('Error: unable to process {}, see file in errors folder.'.format(file))
    