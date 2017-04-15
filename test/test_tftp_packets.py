import tftp

# All of these tests are about creating a format string for a receive packet.
def test_get_receive_packet_with_no_filename():  #TODO raise an exception?
    filename = ''
    assert tftp.create_receive_packet(filename) == ''

def test_get_receive_packet_with_shortest_filename():
    filename = 'a'
    assert tftp.create_receive_packet(filename) == '\x00\x01a\x00octet\x00'

#  def test_shortest_filename():
#      filename = '1'
#      #TODO explain where this comes from; struct packing stuff.
#      assert tftp.get_receive_format_string(filename) == '!H1sB5sB'

#  def test_longer_filename():
#      filename = '12'
#      assert tftp.get_receive_format_string(filename) == '!H2sB5sB'
