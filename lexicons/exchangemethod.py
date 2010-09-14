#!/usr/bin/env python

"""
Implements the exchange method as described in

@article{Spaeth77,
  Author = {Sp{\"a}th, Helmuth},
  Journal = {European Journal of Operations Research},
  Number = {1},
  Pages = {23--31},
  Title = {Computational Experiences with the Exchange Method},
  Volume = {1},
  Year = {1977}}

The class is ExchangeMethod. It requires a list (of words, or word-pos
pairs --- anything hashable should do).  It randomly partitions that
list into a list of sets, and then performs the exchange method
according to an objective function and the scoring dictionary
provided.

The default objective function is the one used by

@inproceedings{HatzivassiloglouMcKeown97,
  Author = {Hatzivassiloglou, Vasileios and McKeown, Kathleen R.},
  Booktitle = {Proceedings of the 35th Annual Meeting of the ACL
              and the 8th Conference of the European Chapter of the ACL},
  Pages = {174--181},
  Publisher = {ACL},
  Title = {Predicting the Semantic Orientation of Adjectives},
  Year = {1997}}

However, other objective functions can be supplied, with the keyword
argument objective_function when building ExchangeMethod objects.  The
presumption is just that the supplied objective function will take a
list of sets as its first argument and a scoring dictionary d as its
second argument.

If this program is called with no arguments, then it runs a very short
demo with an intuitive scoring function and the default objective
function.

For additional details, see the 'Sentiment lexicons' handout from
Linguist 287 / CS 424P: Extracting Social Meaning and Sentiment,
Stanford, Fall 2010.

---Chris Potts
"""

import sys
from copy import deepcopy
from math import factorial
from random import randint, shuffle

######################################################################

class ExchangeMethod:
    """
    Implements the exchange method for clustering, though the real
    work of the algorithm.
    """
    def __init__(self, words, d, k=2, objective_function=None):
        """
        Arguments
        words -- a list (the members should be hashable, so that they can be in sets)
        d -- the scoring dictionary
        
        Keyword arguments
        objective_function -- the function we're trying to minimize (default: self.hatzivassiloglou_mckeown_objective_function, defined here)
        k -- the number of clusters (default: 2)
        """
        self.words = words
        self.d = d
        self.k = k
        self.initial_cells = random_partition(self.words, self.k)        
        if objective_function:
            self.objective_function = objective_function
        else:
            self.objective_function = self.hatzivassiloglou_mckeown_objective_function

    def initial_objective_value(self):
        """The value of the objective function for self.initial_cells."""
        return self.objective_function(self.initial_cells, self.d)
    
    def run(self):
        """
        Controls the iterative optimization. The real work is done by
        self.exchange().
        """        
        cells = deepcopy(self.initial_cells)        
        # Initial value of the objective function.
        obj_val = self.objective_function(cells, self.d)    
        # We exit this loop when a call to exchange() yields no
        # improvement over obj_val.
        iteration_counter = 1 # Just for the progress report and the output, for reference.
        while True:
            # Progress report.
            sys.stderr.write("\nIteration %s. Objective function value %s\n" % (iteration_counter, obj_val))
            # Perform an exchange.
            cells, new_obj_val = self.exchange(cells, obj_val)
            if new_obj_val < obj_val:
                obj_val = new_obj_val
                iteration_counter += 1
            # Exit the entire method as a way of exiting the while loop.
            else:
                return [cells, iteration_counter, obj_val]

    def exchange(self, cells, obj_val):
        """
        Performs the exchanges that form the heart of the optimization
        algorithm. The calling method exchange_method() checks to see
        whether obj_val changes from input to output.
        
        Arguments
        cells (list of sets) -- the partition of words
        obj_val (float) -- the objective function value before this iteration
        words (list) -- the original word list, which we iterate over
        d -- the scoring dictionary
        
        Output
        cells (list of sets) -- the potentially different partition
        obj_val (float) -- the best improvement possible
        """
        total = len(self.words)
        for i, w in enumerate(self.words):
            # Over-writing progress report and informal speed assessment.
            sys.stderr.write("\r",) ; sys.stderr.write("\tEvaluating word %s of %s" % (i+1, total)) ; sys.stderr.flush()
            # Get the membership for w.
            w_cell_index = self.current_cell_index(w, cells)
            # Calculate the objective values for making this change.
            candidate_objective_values = []
            for other_cell_index in xrange(len(cells)):
                # Check only distinct values for cells, and never move a word out of a singleton cell.
                if other_cell_index != w_cell_index and len(cells[w_cell_index]) > 1:
                    # This copy is made for the hypothetical objective
                    # function calculation.  This could be optimized, by
                    # passing cells itself with index points for which
                    # cells to change, and how, but probably at a loss of
                    # generality when it comes to the objective functions
                    # we can accommodate.
                    temp_cells = deepcopy(cells)
                    temp_cells[w_cell_index] = cells[w_cell_index] - set([w])
                    temp_cells[other_cell_index] = cells[other_cell_index] | set([w])                
                    new_val = self.objective_function(temp_cells, self.d)
                    # Add a new index iff it would lead to an improvement.
                    if new_val < obj_val:                    
                        candidate_objective_values.append((new_val, other_cell_index))                
                # Determine which objective change is the most beneficial, if any.
                if candidate_objective_values:
                    # The best objective function is the smallest one.
                    obj_val, max_cell_index = sorted(candidate_objective_values)[0]
                    # Make the change.
                    cells[w_cell_index] = cells[w_cell_index] - set([w])
                    cells[max_cell_index] = cells[max_cell_index] | set([w])
        return [cells, obj_val]

    def hatzivassiloglou_mckeown_objective_function(self, cells, d):
        """
        The function we are minimizing, by minimizing the sum of the total
        distances for the members of cells.

        Arguments:
        cells (list of sets) -- the partition
        d -- the scoring dictionary

        Output: float

        Optimization:

        It is prohibitively costly to iterate over (cell x cell) in
        the inner loop. If cell has 1000 members, then we need to
        check 1000**2 = 1,000,000 pairs, and we need to do that every
        time we check a word. Thus, the algorithm below takes a
        short-cut.  It first calculates the cardinality of the set of
        all two membered subsets of cell:

        cell_pair_size = len(cls)! / ((len(cls) - 2)! * 2!)

        It then iterates through the keys in d. For each key k = (w1,
        w2), if both w1 and 2 are in cell, then d[k] is added to the
        inner sum and 1 is subtracted from cell_pair_size.  Once we've
        gone through d, we add

        cell_pair_size * 0.5

        to the inner sum.  If cell_pair_size began as 900 and 800 were
        found to have values in d, then we add 100 * 0.5 = 50 at the
        end.  This saves having to iterate through the 100 missing
        values.
        """    
        outer_sum = 0.0    
        for cell in cells:
            inner_sum = 0.0
            # Cardinality of the set of all two-members subsets of
            # cell.  We will deduct 1 every time we find a value for
            # cell in d.
            cell_pair_size = binomial_coefficient(cell, k=2)        
            for key, val in d.iteritems():
                if key[0] in cell and key[1] in cell and key[0] != key[1]:
                    inner_sum += 1.0 - d[key]
                    cell_pair_size -= 1
            inner_sum += cell_pair_size * 0.5
            outer_sum += inner_sum/len(cell)
        return outer_sum
            
    def current_cell_index(self, w, cells):
        """The index of the cell in cells that contains w."""
        for i in xrange(len(cells)):
            if w in cells[i]:
                return i
        raise Exception("Word %s was not found in any cell!" % w)

######################################################################
# HELPER METHODS

def random_partition(x, k):
    """
    Shuffle a deep copy of the input list, pick k random breakpoints
    and return the partition, as a list of sets.
    
    Input
    x -- a list
    k -- the number of cells (raises an exception if len(x) < k)
    
    Output
    cells -- a k-membered list of sets
    """
    # Make sure this is feasible.
    if len(x) < k:
        raise Exception("The number of cells cannot exceed the number of elements in the list. Your list has %s elements and your k is %s" % (len(x), k))
    x_copy = deepcopy(x)
    shuffle(x_copy)    
    # Get the breakpoints.
    breakpoints = set([])
    while len(breakpoints) < k-1:
        breakpoints.add(randint(1, len(x)-2))
    breakpoints = sorted(list(breakpoints))
    # Add initial and final indices, for the iteration.
    breakpoints.insert(0,0)
    breakpoints.append(len(x))
    # Create the partition by iterating through pairs (start, finish)
    # drawn from breakpoints.
    cells = []
    i = 0
    while i < len(breakpoints)-1:
        start = breakpoints[i]
        finish = breakpoints[i+1]
        cells.append(set(x[start:finish]))
        i += 1
    return cells

def binomial_coefficient(x, k=2):
    """
    Calculates len(x) choose k, where k defaults to 2.
    
    Arguments
    x (something iterable) -- the input elements
    
    Keyword argument
    k (int) -- is the size of the subsets to count
        
    Output
    bc (int) -- the number of k-member subsets of x
    """
    n = len(x)
    bc = 1
    if n >= 2:
        bc = factorial(n) / (factorial(n - k) * factorial(k))
    return bc

######################################################################
# QUICK TEST

def quicktest():
    d = {                         
        #                         0.4
        # Terrible   Awful   Bad   *  Good   Great   Excellent
        #         0.9     0.9             0.9     0.9
        #             0.8                    0.8
        ("good", "great"):0.9,
        ("good", "excellent"):0.8,
        ("great","excellent"):0.9,
        #
        ("good", "bad"):0.4,
        ("good", "awful"):0.3,
        ("good", "terrible"):0.2,
        ("great", "bad"):0.3,
        ("great", "awful"):0.2,
        ("great", "terrible"):0.1,
        ("excellent", "bad"):0.2,
        ("excellent", "awful"):0.1,
        ("excellent", "terrible"):0.01,
        #
        ("bad", "awful"):0.9,
        ("bad", "terrible"):0.8,
        ("awful", "terrible"):0.9}
        
    words = ["good", "great",  "bad", "terrible", "excellent"]

    # Build the optimizer.
    em = ExchangeMethod(words, d, k=2)

    # Check out its initial partition.
    for i, cell in enumerate(em.initial_cells):
        print "<cluster n=%s iteration=0>" % (i+1)
        for w in sorted(list(cell)):
            print w
        print "</cluster>\n"

    # Optimize.
    cells, iterations, obj_val = em.run()
    
    # Check out its initial partition.
    print "\n\n"
    for i, cell in enumerate(cells):
        print "<cluster n=%s iteration=%s>" % (i+1, iterations)
        for w in sorted(list(cell)):
            print w
        print "</cluster>\n"

    # Compare the objective function values.
    print "Initial objective value: %s" % em.initial_objective_value()
    print "Final objective value: %s" % obj_val
    
if __name__ == "__main__":
    quicktest()
    
######################################################################


