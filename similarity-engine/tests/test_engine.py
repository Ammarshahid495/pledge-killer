"""
Comprehensive Tests for Pledge Fighter Stanford MOSS-grade Similarity Engine.
"""

import os
import sys

# Add the similarity-engine directory to sys.path
engine_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if engine_dir not in sys.path:
    sys.path.insert(0, engine_dir)

from engine import SimilarityEngine

CODE_BASE = """
#include <iostream>
using namespace std;

int fibonacci(int n) {
    if (n <= 1) {
        return n;
    }
    int a = 0;
    int b = 1;
    for (int i = 2; i <= n; i++) {
        int next = a + b;
        a = b;
        b = next;
    }
    return b;
}

int main() {
    int num;
    cout << "Enter number: ";
    cin >> num;
    cout << "Result: " << fibonacci(num) << endl;
    return 0;
}
"""

CODE_RENAMED_VARS = """
#include <iostream>
using namespace std;

int fibonacci(int limit) {
    if (limit <= 1) {
        return limit;
    }
    int first = 0;
    int second = 1;
    for (int step = 2; step <= limit; step++) {
        int val = first + second;
        first = second;
        second = val;
    }
    return second;
}

int main() {
    int target;
    cout << "Enter number: ";
    cin >> target;
    cout << "Result: " << fibonacci(target) << endl;
    return 0;
}
"""

CODE_DIFFERENT_FORMATTING_COMMENTS = """
#include <iostream>
using namespace std;

// Function to calculate fibonacci
int fibonacci(int n) 
{
    /* base case */
    if (n <= 1) 
    {
        return n;
    }
    
    int a = 0;
    int b = 1;

    // loop calculation
    for (int i = 2; i <= n; i++) 
    {
        int next = a + b;
        a = b;
        b = next;
    }
    return b;
}

int main() 
{
    int num;
    cout << "Enter number: ";
    cin >> num;
    cout << "Result: " << fibonacci(num) << endl;
    return 0;
}
"""

CODE_COMPLETELY_DIFFERENT = """
#include <vector>
#include <string>
#include <algorithm>
#include <iostream>

struct Student {
    std::string name;
    double gpa;
};

bool compareStudents(const Student& s1, const Student& s2) {
    return s1.gpa > s2.gpa;
}

int main() {
    std::vector<Student> roster = {{"Alice", 3.9}, {"Bob", 3.7}};
    std::sort(roster.begin(), roster.end(), compareStudents);
    for (const auto& s : roster) {
        std::cout << s.name << ": " << s.gpa << "\\n";
    }
    return 0;
}
"""

CODE_MALFORMED = """
#include <iostream
int main( {
    unknown syntax &&& !!! (((
    return 0
"""


def test_identical_source_code():
    engine = SimilarityEngine(k=6, w=3, min_matching_tokens=6)
    sub1 = engine.process_source("sub1", CODE_BASE)
    sub2 = engine.process_source("sub2", CODE_BASE)

    res = engine.compare_submissions(sub1, sub2)
    assert res.similarity_a_to_b >= 95.0
    assert res.similarity_b_to_a >= 95.0
    assert res.symmetric_similarity >= 95.0
    assert len(res.regions) > 0


def test_renamed_variables():
    engine = SimilarityEngine(k=6, w=3, min_matching_tokens=6)
    sub1 = engine.process_source("sub1", CODE_BASE)
    sub2 = engine.process_source("sub2", CODE_RENAMED_VARS)

    res = engine.compare_submissions(sub1, sub2)
    assert res.symmetric_similarity >= 80.0
    assert len(res.regions) > 0


def test_formatting_and_comments_immunity():
    engine = SimilarityEngine(k=6, w=3, min_matching_tokens=6)
    sub1 = engine.process_source("sub1", CODE_BASE)
    sub2 = engine.process_source("sub2", CODE_DIFFERENT_FORMATTING_COMMENTS)

    res = engine.compare_submissions(sub1, sub2)
    assert res.symmetric_similarity >= 95.0


def test_completely_different_code():
    engine = SimilarityEngine(k=8, w=4, min_matching_tokens=8)
    sub1 = engine.process_source("sub1", CODE_BASE)
    sub2 = engine.process_source("sub2", CODE_COMPLETELY_DIFFERENT)

    res = engine.compare_submissions(sub1, sub2)
    assert res.symmetric_similarity < 15.0


def test_malformed_code_safe():
    engine = SimilarityEngine(k=6, w=3, min_matching_tokens=6)
    sub1 = engine.process_source("sub1", CODE_BASE)
    sub2 = engine.process_source("sub2", CODE_MALFORMED)

    res = engine.compare_submissions(sub1, sub2)
    assert isinstance(res.symmetric_similarity, float)
