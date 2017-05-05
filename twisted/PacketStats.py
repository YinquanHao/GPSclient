from twisted.web import resource

class PacketStats(resource.Resource):
    """
    Listens in on HTTP to any request.
    Returns x,y,z triple of ints.
    x - amount of packets received
    y - amount of packets that successfully went through processing
    z - amount of packets that did not go successfully through processing

    """
    isLeaf = True
    PACKETS_RECEIVED = 0
    PACKETS_PROCESSED = 0
    def render_GET(self, request):
        request.setHeader("content-type", "text/plain")
        return str(self.PACKETS_RECEIVED) + "," + str(self.PACKETS_PROCESSED) + "," + str(self.PACKETS_RECEIVED - self.PACKETS_PROCESSED)
