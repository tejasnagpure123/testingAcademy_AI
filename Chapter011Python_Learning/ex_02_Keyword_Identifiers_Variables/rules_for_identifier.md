# Rules for Identifiers in Python

Identifiers are names used to identify a variable, function, class, module, or other object. Here are the rules for creating identifiers in Python:

1.  **Identifiers can be a combination of letters in lowercase (a-z) or uppercase (A-Z) or digits (0-9) or an underscore (_).**

    *   **Valid examples:**
        ```python
        myVariable = 10
        Name = "Alice"
        _privateVar = 20
        variable123 = 30
        ```

2.  **An identifier cannot start with a digit.**

    *   **Invalid examples:**
        ```python
        # 1variable = 40  # SyntaxError: invalid decimal literal
        ```

    *   **Valid alternative:**
        ```python
        variable1 = 40
        ```

3.  **Keywords cannot be used as identifiers.** Keywords are reserved words in Python with special meanings.

    *   **Invalid examples:**
        ```python
        # if = 50         # SyntaxError: invalid syntax
        # for = "loop"    # SyntaxError: invalid syntax
        ```

    *   **Valid alternative:**
        ```python
        if_condition = True
        for_loop_counter = 0
        ```

4.  **Special symbols like !, @, #, $, % etc. cannot be used in an identifier.**

    *   **Invalid examples:**
        ```python
        # my-variable = 60  # SyntaxError: can't assign to operator
        # @name = "Bob"     # SyntaxError: invalid syntax
        ```

    *   **Valid alternative:**
        ```python
        my_variable = 60
        user_name = "Bob"
        ```

5.  **Identifiers can be of any length.**

    *   **Example:**
        ```python
        thisIsAVeryLongAndDescriptiveVariableName = 100
        ```

### Examples from Lab006_Identifier.py

```python
age=65
print(age)
age="Hello"
print(age)

_ = 12
print(_)
_ = _ + 1
print(_)

abc234="abc234"
print(abc234)

namne="John Doe"

# name=> Identifier
# = => Assignment Operator
# "John Doe" => String Literal
print(namne)
```