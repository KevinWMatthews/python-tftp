import tftp

# All of these tests are about creating a format string for a receive packet.
def test_no_filename_fails():   #TODO raise an exception?
    filename = ''
    assert tftp.get_receive_format_string(filename) == ''

def test_shortest_filename():
    filename = '1'
    #TODO explain where this comes from; struct packing stuff.
    assert tftp.get_receive_format_string(filename) == '!H1sB5sB'
