# Pledge Fighter Similarity Engine

The intellectual core of **Pledge Fighter** is a Stanford MOSS-grade code similarity detection engine tailored for C++ source code. It identifies shared structural patterns and code reuse even when users rename identifiers, alter whitespace, reformat brackets, or insert comments.

## Architecture & Algorithm Pipeline

1. **C++ Lexical Tokenization (`tokenizer/cpp_tokenizer.py`)**
   - Extracts all C++ keywords, types, control-flow statements, identifiers, operators, and literals.
   - Maps each token to exact line, column, and character offsets `(start_line, start_col, end_line, end_col)` to enable pinpoint visual highlighting on the student's own source code.
   - Strips single-line (`//`) and multi-line (`/* ... */`) comments while preserving source coordinates.

2. **Structural Normalization (`normalizer/normalizer.py`)**
   - Normalizes variable and local function identifiers (`ID`) and literals (`NUM`, `STR`, `CHAR`) to defeat trivial obfuscation (e.g. variable renaming).
   - Preserves all language keywords (`if`, `for`, `while`, `return`, `class`, `template`, etc.), control structures, and operators.

3. **K-Gram Generation & Karp-Rabin Rolling Hash (`fingerprint/winnowing.py`)**
   - Forms sliding windows of $k$ consecutive normalized tokens ($k$-grams).
   - Computes rolling hashes with polynomial base $B=257$ and modulo $M=10^9+7$ in $O(1)$ time per token.

4. **Winnowing Algorithm (Schleimer, Wilkerson, Aiken 2003)**
   - In each sliding window of $w$ hashes, selects the minimum hash value.
   - Applies the standard MOSS rightmost tie-breaking rule: if multiple hashes match the minimum in a window, the rightmost occurrence is selected.
   - Yields a sparse, robust fingerprint set that guarantees detection of matches $\ge w + k - 1$ tokens while resisting localized edits.

5. **Matching & Region Coalescing (`comparison/matcher.py`)**
   - Builds an inverted index of fingerprints to find shared hashes.
   - Verifies token sequences to prevent false hash collisions.
   - Coalesces adjacent or overlapping matching token spans into contiguous line-bounded match regions.

6. **Honest Metrics Calculation (`scoring/metrics.py`)**
   - Computes directional coverage $Coverage(A \to B)$ and $Coverage(B \to A)$.
   - Computes symmetric harmonic similarity score.
   - Reports match counts and matching line numbers.
   - Adheres to honest reporting principles: frames results as structural code similarity, never as an accusation or probability of cheating.
