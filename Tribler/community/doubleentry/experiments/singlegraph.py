import sys

from Tribler.community.doubleentry.database import Persistence
from Tribler.community.doubleentry.graph import GraphDrawer

"""
Takes a directory with sqlite/doubleentry.db as input and generates a graph from the db.
"""


class SingleGraphDrawer:

    def __init__(self, working_directory):
        persistence = Persistence(working_directory)
        graph_drawer = GraphDrawer(persistence)
        graph_drawer.setup_graph()
        graph_drawer.draw_graph()


def main():
    """
    Main method to start a Double Entry community that listens to commandline input.
    """
    print 'Number of arguments:', len(sys.argv), 'arguments.'

    if len(sys.argv) == 2:
        path = str(sys.argv[1])
        print 'Using path: %s' % path
        SingleGraphDrawer(path)
    else:
        print "Failure: takes one argument <path to sqlite/doubleentry>"
        exit(1)

if __name__ == "__main__":
    main()
