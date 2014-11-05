#!/usr/bin/python
import string

####################################################################
### >>> parse_tag( ' A:4 A:5 B:7' )
### ([4, 5, 7], ['A', 'A', 'B'])
### >>> parse_tag( ' A4,A5,B7' )
### ([4, 5, 7], ['A', 'A', 'B'])
### >>> parse_tag( '4 5 7' )
### ([4, 5, 7], ['', '', ''])
### >>> parse_tag( 'A:4 5 7' )
### ([4, 5, 7], ['A', 'A', 'A'])
### >>> parse_tag( 'A:4 5 B:7' )
### ([4, 5, 7], ['A', 'A', 'B'])
### >>> parse_tag( 'A1-3,11,13-15')
### ([1, 2, 3, 11, 13, 14, 15], ['A', 'A', 'A', 'A', 'A', 'A', 'A'])
### >>> parse_tag( 'A1-3,B11,13-15')
### ([1, 2, 3, 11, 13, 14, 15], ['A', 'A', 'A', 'B', 'B', 'B', 'B'])
### >>> parse_tag( 'A1-3,B11,C13-15')
### ([1, 2, 3, 11, 13, 14, 15], ['A', 'A', 'A', 'B', 'C', 'C', 'C'])
####################################################################

def parse_tag( tag ):

    if isinstance( tag, list ):
        tag = string.join( tag, ' ' )
    
    int_vector = []
    char_vector= []
    
    xchar = ''

    tag = tag.replace(',',' ')
    tag = tag.replace(';',' ')
    
    for subtag in tag.split(' '):

        if subtag == '': 
            continue

        if '-' in subtag: # '1-10' or 'A1-10' or 'A:1-10' or 'A:1-A:10'
            ( start, stop ) = subtag.split('-')  
            ( start_idx, start_char ) = parse_tag( start )
            ( stop_idx, stop_char ) = parse_tag( stop )
            assert( ( start_char[0] == stop_char[0] ) or ( stop_char[0] == '' ) )
            if start_char[0] != '': 
                xchar = start_char[0]
            subtag = string.join([xchar+str(x) for x in xrange(start_idx[0],stop_idx[0]+1)], ' ')
            int_vector.extend( parse_tag( subtag )[0] )
            char_vector.extend( parse_tag( subtag )[1] )
            continue

        try: # 100
            xint = int(subtag)
        except: # A:100 or A100
            if ':' in subtag: # A:100
                subtag = subtag.split(':')
                xchar = subtag[0]
                xint = int(subtag[-1])
            else: # A100
                for x in xrange( len( subtag ) ):
                    try:
                        xint = int(subtag[x:])
                        break
                    except:
                        xchar = subtag[x]
          
        int_vector.append( xint )
        char_vector.append( xchar )

    assert( len(int_vector) == len(char_vector) ) 
    return int_vector, char_vector

##########################################################
##########################################################

if __name__=='__main__':

    import argparse

    parser = argparse.ArgumentParser(description='.')
    parser.add_argument('tag', nargs='*')
    args=parser.parse_args()

    if isinstance( args.tag, list ): args.tag = string.join( args.tag, ' ' )
    print parse_tag( args.tag )

