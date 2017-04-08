import tftp

def test_create_receive_packet_format_string():
    filename = ''
    assert tftp.get_receive_format_string(filename) == ''
