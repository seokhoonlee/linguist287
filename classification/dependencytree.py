#!/usr/bin/env python

"""
This is code for mapping the string output of Stanford dependency
structures to computational objects that behave like dependency
structures should.

In addition to basic functionality for dealing with these objects qua
graphs, there are also methods (of Tree objects) for marking nodes
with scopal relations, as discussed in the 'Sentiment classification'
handout for Linguist 287, Stanford, Fall 2010.

Right now, the code implements two kinds of scope-marking:
monotonicity and veridicality.  It is set up so that it is fairly
straightforward to accommodate new relations, by adding a marking
method to Tree and expanding the values of the scope_marking attribute
of Node.

If called from the command-line (via the main method), this program
will try to parse and scope-mark a command-line argument.  If none is
given, it randomly selects from a small list of parse strings and
returns the marked-up version of that.

Tree objects have a method to_graphviz() that returns the code for a
dot file of the sort that Graphviz can turn into an image:

http://www.graphviz.org/

For applications of this scope marking in the context of sentiment
analysis, see the 'Sentiment classification' handout mentioned just
above.

---Chris Potts, 2010-09-30
"""

######################################################################


import sys
if sys.version_info < (2, 4):
    print "This program requires a version of Python at least as high as 2.4. \
    You're running version %s.%s.%s" % sys.version_info[0:3]
    sys.exit(2)
import re
from random import randint
from operator import itemgetter

######################################################################

# These are the two kinds of scope marking currently implemented. To
# add more, or change these, write new functions that use
# Tree.scope_marking() and also update the Node class so that the
# attribute scope_markings initializes the default values and the
# method update_marking() handles changes.
VERIDICALITY = "veridicality"
MONOTONICITY = "monotonicity"

# Indicates that a node is in the scope of a downward entailing operator.
DOWNWARD = "NPOL"
# No marking for nodes in upward entailing environments (the default).
UPWARD = ""
# Indicates that a node is in an non-veridical environment.
NONVERIDICAL = "_NONVER"
# No marking for nodes in veridical environments.
VERIDICAL = ""

# This listing approximates the semantic property of downward entailingness.
DOWNWARD_MORPHEMES = ("not", "never", "nothing", "no", "n't", "nowhere", "none", "few", "seldom", "rarely")

# This listing approximates the semantic property of nonveridicality.
NONVERIDICAL_MORPHEMES = ('accept', 'accepts', 'accepted', 'accepting',
                          'advertise', 'advertises', 'advertised', 'advertising',
                          'advocate', 'advocates', 'advocated', 'advocating',
                          'affirm', 'affirms', 'affirmed', 'affirming',
                          'agree', 'agrees', 'agreed', 'agreeing',
                          'allege', 'alleges', 'alleged', 'alleging',
                          'allow', 'allows', 'allowed', 'allowing',
                          'annoy', 'annoys', 'annoyed', 'annoying',
                          'appear', 'appears', 'appeared', 'appearing', 
                          'argue', 'argues', 'argued', 'arguing',
                          'ask', 'asks', 'asked', 'asking',
                          'assert', 'asserts', 'asserted', 'asserting',
                          'assume', 'assumes', 'assumed', 'assuming',
                          'assure', 'assures', 'assured', 'assuring',
                          'believe', 'believes', 'believed', 'believing',
                          'boast', 'boasts', 'boasted', 'boasting',
                          'calculate', 'calculates', 'calculated', 'calculating',
                          'claim', 'claims', 'claimed', 'claiming',
                          'comment', 'comments', 'commented', 'commenting',
                          'concern', 'concerns', 'concerned', 'concerning',
                          'confided', 'confides', 'confided', 'confiding',
                          'conjecture', 'conjectures', 'conjectured', 'conjecturing',
                          'consider', 'considers', 'considered', 'considering',
                          'contemplate', 'contemplates', 'contemplated', 'contemplating', 
                          'decided', 'decides', 'decided', 'deciding',
                          'declare', 'declares', 'declared', 'declaring',
                          'deduce', 'deduces', 'deduced', 'deducing',
                          'deem', 'deems', 'deemed', 'deeming',
                          'demand', 'demands', 'demanded', 'demanding',
                          'desire', 'desires', 'desired', 'desiring',
                          'determine', 'determines', 'determined', 'determining',
                          'doubt', 'doubts', 'doubted', 'doubting',
                          'exclaim', 'exclaims', 'exclaimed', 'exclaiming',
                          'expected', 'expects', 'expected', 'expecting',
                          'fantasize', 'fantasizes', 'fantasized', 'fantasizing',
                          'fear', 'fears', 'feared', 'fearing',
                          'feel', 'feels', 'felt', 'feeling',
                          'grumble', 'grumbles', 'grumbled', 'grumbling',
                          'guess', 'guesses', 'guessed', 'guessing',
                          'hear', 'hears', 'heard', 'hearing',
                          'hope', 'hopes', 'hoped', 'hoping',
                          'imply', 'implies', 'implied', 'implying',
                          'imagine', 'imagines', 'imagined', 'imagining',
                          'infer', 'infers', 'inferred', 'inferring',
                          'insinuate', 'insinuates', 'insinuated', 'insinuating',
                          'maintain', 'maintains', 'maintained', 'maintaining',
                          'mumble', 'mumbles', 'mumbled', 'mumbling',
                          'opine', 'opines', 'opined', 'opining',
                          'pledge', 'pledges', 'pledged', 'pledging',
                          'pray', 'prays', 'prayed', 'praying',
                          'predict', 'predicts', 'predicted', 'predicting',
                          'presume', 'presumes', 'presumed', 'presuming',
                          'pretend', 'pretends', 'pretended', 'pretending',
                          'proclaim', 'proclaims', 'proclaimed', 'proclaiming',
                          'pronounce', 'pronounces', 'pronounced', 'pronouncing',
                          'propose', 'proposes', 'proposed', 'proposing',
                          'question', 'questions', 'questioned', 'questioning',
                          'reckon', 'reckons', 'reckoned', 'reckoning',
                          'recommend', 'recommends', 'recommended', 'recommending',
                          'report', 'reports', 'reported', 'reporting',
                          'respond', 'responds', 'responded', 'responding',
                          'say', 'says', 'said', 'saying',
                          'seem', 'seems', 'seemed', 'seeming',
                          'shout', 'shouts', 'shouted', 'shouting',
                          'suspect', 'suspects', 'suspected', 'suspecting',
                          'think', 'thinks', 'thought', 'thinking',
                          'tell', 'tells', 'told', 'telling',
                          'want', 'wants', 'wanted', 'wanting',
                          'wish', 'wishes', 'wished', 'wishing',
                          'wonder', 'wonders', 'wondered', 'wondering'
                          )

# This tuple approximates the semantic property of non-veridicality.
NONVERIDICAL_RELATIONS = ("xcomp", "ccomp", "pcomp")

# These relations do not propagate scope: items in syntactic scope of
# an operator by strict structural considerations are excluded if
# their immediate link is through one of these.
NONSCOPE_RELATIONS = ("dep", "conj_but", "conj_and", "parataxis", "advcl", "rcmod")

######################################################################

class Tree:
    """
    Tree objects, the central object of this program. Tree objects are
    basically sets of Edge objects.  For convenience, they also have
    node attributes, since we often deal with the nodes independently
    of the edges.
    """
    def __init__(self, s):
        """
        Input
        s -- Stanford dependency parse string

        Attributes:
        edges -- a list of Edge objects
        nodes -- a list of Node objects
        
        """
        # Pull out the relations.
        edge_re = re.compile(r"(\w+)\((.+?),\s+([^\)]+)\)", re.MULTILINE | re.DOTALL)
        edges = edge_re.findall(s)
        self.edges = map(Edge, edges)
        self.nodes = self.get_nodes()

    def polarity_marking(self):
        """
        Propagates upward and downard entailingness around the tree,
        marking each node for this property.       
        """
        self.scope_marking(DOWNWARD, self.downward_spread)

    def veridicality_marking(self):
        """
        Propagates veridicality and nonveridicality around the tree,
        marking each node for this property.      
        """                  
        self.scope_marking(NONVERIDICAL, self.nonveridical_spread)
        
    def scope_marking(self, marking, spread_function):
        """
        Abstract class for handling scope marking of various kinds.
        The basic intuition is that the property of interest spreads
        up from a daughter node D to the mother, and then to all the
        daughters of that mother that are to the left of D.
        NONSCOPE_RELATIONS can block this propagation.

        Arguments
        marking -- the marking to add
        spread_function -- function for handling the intial spread (for self.polarity_marking(), this is
        self.downward_daughters(); for self.veridicality_marking(), this is self.nonveridical_daughters())
        """
        # Propagate the basic markings.
        for mom in self.nodes:
            for daught in spread_function(mom):                
                mom.update_marking(marking)
                for d_prime in self.daughters(mom, blockers=NONSCOPE_RELATIONS):                   
                    if daught != d_prime and daught.index < d_prime.index:
                        d_prime.update_marking(marking)
                        for n2 in self.nodes:
                            if self.path(d_prime, n2, blockers=NONSCOPE_RELATIONS) and daught.index < n2.index:    
                                n2.update_marking(marking)

    def downward_spread(self, n):
        """
        Returns the set of daughters of Node n that are downward
        entailing.  The two ways this can happen: (i) the daughter
        itself is marked as DOWNWARD and (ii) the daughter has a
        determiner daughter that is DOWNWARD.
        """
        dd = []
        if n.scope_markings[MONOTONICITY] == DOWNWARD:
            dd.append(n)
        for daught in self.daughters(n):
            if daught.scope_markings[MONOTONICITY] == DOWNWARD:
                dd.append(daught)
            else:
                # This spreads to determiner relations, allowing them to exter their semantic influence.
                for grand_daught in self.daughters(daught):
                    if self.get_edge(daught, grand_daught).rel in ("det", "amod") and grand_daught.scope_markings[MONOTONICITY] == DOWNWARD:
                        dd.append(daught)
        return dd

    def nonveridical_spread(self, n):
        """Returns the set of daughters of Node n that are nonveridical entailing."""
        dd = []
        if n.scope_markings[VERIDICALITY] == NONVERIDICAL:
            dd.append(n)
        for daught in self.daughters(n):
            # The first conjunct ensures veridicality. The second helps limit to the syntactic environments we want.
            if daught.scope_markings[VERIDICALITY] == NONVERIDICAL and self.get_edge(n, daught).rel in ("xcomp", "ccomp", "pcomp"):
                dd.append(daught)
        return dd
    
    def words(self):
        """Returns the list of words in linear order."""        
        return [n.word for n in self.nodes]
    
    def words_with_scope_markings(self):
        """Returns the list of words with scope-marking labels in linear order."""
        marked_nodes = []
        for node in self.nodes:
            sm = []
            for key, val in sorted(node.scope_markings.items()):
                sm.append(val)
            marked_nodes.append(node.word + "".join(sm))
        return marked_nodes
    
    def get_edge(self, x, y):
        """Returns the edge from Node x to Node y if there is one, else None."""
        for e in self.edges:
            if e.from_node == x and e.to_node == y:
                return e
        return None
    
    def daughters(self, x, blockers=NONSCOPE_RELATIONS):
        """Returns the list of daughters of Node x."""
        daughts = []
        for n in self.nodes:
            e = self.get_edge(x, n)
            if e and e.rel not in blockers:
                daughts.append(n)
        return daughts

    def path(self, x, y, blockers=NONSCOPE_RELATIONS):
        """Returns True if there is a path from Node x to Node y, else False."""
        daughts = self.daughters(x, blockers=NONSCOPE_RELATIONS)
        if y in daughts:
            return True
        else:
            for daught in daughts:
                if self.path(daught, y, blockers=blockers):
                    return True
        return False

    def get_nodes(self):
        """
        Utility function. Returns the set of nodes, ordered by their
        linear order in the string.  We use a dictionary from strings
        to nodes to get the set of unique nodes because Node objects
        aren't hashable.
        """
        nodes = {}        
        for e in self.edges:
            nodes[unicode(e.from_node)] = e.from_node
            nodes[unicode(e.to_node)] = e.to_node
        return sorted(nodes.values(), cmp=((lambda x, y : cmp(x.index, y.index))))

    def nodes_by_index(self):
        """
        Returns a dict from node position indices to Node objects.
        """
        nodes = {}        
        for e in self.edges:
            nodes[e.from_node.index] = e.from_node
            nodes[e.to_node.index] = e.to_node
        return nodes
        
    def __str__(self):
        """String of nodes, one per line."""
        return "\n".join(map(str, self.edges))

    def to_graphviz(self, caption=""):
        """
        Map the current tree to its Graphviz code. Graphviz can then
        map this code to various image formats.

        Keyword argument
        caption -- a string to include as a label for the tree (default: "")
        """        
        s = "digraph g {\n"
        s += 'label="%s"; fontsize="14"\n' % caption
        fontsize=12;
        for node in self.nodes:
            s += "\t" + node.to_graphviz() + "\n"
        for edge in self.edges:
            s += "\t" + edge.to_graphviz() + "\n"
        s += "}"
        return s

######################################################################
    
class Edge:
    """
    An Edge is two Node objects and an edge relation.

    Attributes:
    rel -- the edge relation
    from_node -- a Node
    to_node -- a Node
    start -- the index of from_node (for linear ordering)
    finish -- the index of to_node (for linear ordering)
    """
    def __init__(self, tup):
        rel, from_node, to_node = tup
        self.rel = rel
        self.from_node = Node(from_node)
        self.to_node = Node(to_node)
        self.start, self.finish = sorted([self.from_node.index, self.to_node.index])

    def __str__(self):
        """String output mimicking the input format."""
        return "%s(%s, %s)" % (self.rel, self.from_node, self.to_node)

    def to_graphviz(self):
        """
        Graphviz code string. This method is called by
        Tree.to_graphviz().
        """
        return '"%(f)s-%(fi)s" -> "%(t)s-%(ti)s" [label="%(r)s"]' % {"f":self.from_node.word,
                                                                     "fi":self.from_node.index,
                                                                     "t":self.to_node.word,
                                                                     "ti":self.to_node.index,
                                                                     "r":self.rel}
    
######################################################################
    
class Node:
    """
    A Node object has a label, an index, and attributes for polarity
    and verdicality marking. The marking is handled by a dict valued
    attribute self.scope_markings, which is set to record lexical
    values here. The method update_marking handles changes to the
    markings.
    """
    def __init__(self, s):
        word, index = s.rsplit("-", 1)
        self.word = word
        # Deal with the nonce subindexing of the Stanford parser.
        if index.find("'") > -1:
            self.index = int(index.rstrip("'")) + 5000
        else:
            self.index = int(index)
        # Lexical values for the scope-marking properties.
        self.scope_markings = {}
        if self.word in DOWNWARD_MORPHEMES:
            self.scope_markings[MONOTONICITY] = DOWNWARD
        else:
            self.scope_markings[MONOTONICITY] = UPWARD
        if self.word in NONVERIDICAL_MORPHEMES:
            self.scope_markings[VERIDICALITY] = NONVERIDICAL
        else:
            self.scope_markings[VERIDICALITY] = VERIDICAL

    def update_marking(self, marking):
        """
        Update scope_markings with marking, checking to make
        sure that we make the appropriate change to the current
        values.
        """        
        if marking in (UPWARD, DOWNWARD):
            self.scope_markings[MONOTONICITY] = marking
        elif marking in (VERIDICAL, NONVERIDICAL):
            self.scope_markings[VERIDICALITY] = marking

    def __eq__(self, node):
        """True iff both word and index match. (Ignores the scope marking.)"""
        return self.word == node.word and self.index == node.index

    def __neq__(self, node):
        """True iff __eq__ says False."""
        return not self.__eq__(node)

    def __str__(self, polarity=False, veridicality=False):
        """
        Simple string representation, with options for showing
        polarity and intensionality. If no keyword arguments are
        given, the output mimicks the input string.

        Keyword arguments
        polarity -- include any polarity marking (default: False)
        veridicality -- include an veridicality marking (default: False)
        """
        pol_mark = ""
        ver_mark = ""
        if polarity:
            pol_mark = "_" + self.polarity
        if veridicality:
            ver_mark = "_" + self.veridicality            
        return "%s%s%s-%s" % (self.word, pol_mark, ver_mark, self.index)

    def to_graphviz(self):
        """
        Graphviz code string. NEGATIVE nodes are black with white
        lettering, and NONVERIDICAL nodes are diamond shaped. This
        method is called by Tree.to_graphviz().
        """
        style ="unfilled"
        shape = "oval"
        fontcolor = "black"
        if self.scope_markings[MONOTONICITY] == DOWNWARD:
            style = "filled"
            fontcolor = "white"
        if self.scope_markings[VERIDICALITY] == NONVERIDICAL:
            shape = "Mdiamond"
        return '"%(w)s-%(i)s" [label="%(w)s", color="black", fontcolor="%(fc)s", style="%(style)s", shape="%(shape)s"];' % {"w":self.word,
                                                                                                                            "i":self.index,
                                                                                                                            "style":style,
                                                                                                                            "fc":fontcolor,
                                                                                                                            "shape":shape}
        
######################################################################

def demo(argv):
    """
    Parse a command-line tree or parse a randomly selected element of
    samples, displaying a number of forms, including scope-marked
    linearized output.
    """
    samples = (
        "[det(movie-2, the-1), nsubj(amazing-4, movie-2), cop(amazing-4, was-3)]",
        "[det(movie-2, the-1), nsubj(good-5, movie-2), cop(good-5, was-3), advmod(good-5, very-4)]",
        "[det(movie-2, the-1), nsubj(good-6, movie-2), cop(good-6, was-3), neg(good-6, not-4), advmod(good-6, very-5)]",
        "[dep(enjoy-3, i-1), advmod(enjoy-3, always-2), nn(movies-5, horror-4), dobj(enjoy-3, movies-5)]",
        "[dep(enjoy-3, i-1), advmod(enjoy-3, rarely-2), nn(movies-5, horror-4), dobj(enjoy-3, movies-5)]",
        "[amod(people-2, few-1), nsubj(saw-3, people-2), det(movie-6, this-4), amod(movie-6, excellent-5), dobj(saw-3, movie-6)]",
        "[amod(people-2, many-1), nsubj(saw-3, people-2), det(movie-6, this-4), amod(movie-6, excellent-5), dobj(saw-3, movie-6)]",
        "[det(reviews-2, the-1), nsubj(said-3, reviews-2), complm(good-9, that-4), det(movie-6, the-5), nsubj(good-9, movie-6), aux(good-9, would-7), cop(good-9, be-8), ccomp(said-3, good-9), nsubj(was-13, it-12), conj_but(said-3, was-13), neg(was-13, n't-14)]",
        "[nsubj(predicted-2, i-1), complm(outstanding-7, that-3), nsubj(outstanding-7, it-4), aux(outstanding-7, would-5), cop(outstanding-7, be-6), ccomp(predicted-2, outstanding-7)]",
        "[det(point-3, no-2), prep_at(impress-7, point-3), aux(impress-7, did-4), det(movie-6, this-5), nsubj(impress-7, movie-6), dobj(impress-7, me-8)]",
        "[nsubj(think-4, i-1), aux(think-4, do-2), neg(think-4, n't-3), complm(idea-9, that-5), cop(idea-9, is-6), det(idea-9, a-7), amod(idea-9, good-8), ccomp(think-4, idea-9)]",
        "[det(musician-2, every-1), nsubj(tuned-3, musician-2), poss(instrument-5, her-4), dobj(tuned-3, instrument-5)]",
        "[det(musician-2, no-1), nsubj(tuned-3, musician-2), poss(instrument-5, her-4), dobj(tuned-3, instrument-5)]",
        "[det(musician-3, no-1), amod(musician-3, good-2), nsubj(play-5, musician-3), aux(play-5, would-4), nn(music-7, elevator-6), dobj(play-5, music-7)]",
        "[poss(instrument-2, her-1), nsubjpass(tuned-4, instrument-2), auxpass(tuned-4, was-3), det(musician-7, every-6), agent(tuned-4, musician-7)]",
        "[advmod(felt-4, rarely-1), aux(felt-4, have-2), nsubj(felt-4, i-3), advmod(unhappy-6, so-5), acomp(felt-4, unhappy-6), det(thought-9, the-8), prep_at(felt-4, thought-9), prep_of(thought-9, it-11)]")    
    tree_string = ""
    if len(sys.argv) > 1:
        tree_string = sys.argv[1]
    else:
        # Get a random sample tree.
        tree_string = samples[randint(0,len(samples)-1)]
    tree = Tree(tree_string)
    print "======================================================================"
    print tree
    print "----------------------------------------"
    print "Terminals:"
    print tree.words()
    print "----------------------------------------"
    print "Terminals with polarity and veridicality marking:"
    tree.polarity_marking()
    tree.veridicality_marking()
    print tree.words_with_scope_markings()
    print "----------------------------------------"
    print "Graphviz format:"
    print tree.to_graphviz()
      
if __name__ == "__main__":
    demo(sys.argv)
