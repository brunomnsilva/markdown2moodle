# DummyCategory

* Whats the truthfulness of the following statement: *"We can achieve a time complexity of $O(1)$ for a sequential search in an array"*.
    - True
    - !False

* Consider the following function:

```cpp{img}
int func(int *arr, int arrSize) {
    int val = 0;
    for(int i=0; i<arrSize; i++) {
        for(int j=0; j<2; j++) {
            val += arr[i];
        }
    }
    return val;
}
```

What's its time complexity?
    - $O(1)$
    - !$O(n)$
    - $O(log\;n)$
    - $O(n^2)$

* Consider the following function:

$$fib(n)=\left\{\begin{matrix} 1 & n = 0\\  1 & n = 1\\ fib(n-1) + fib(n-2) & n > 1 \end{matrix}\right.$$

Mark the correct statements about `fib(n)`:

    - !It's a recursive function

    - It's defined for all integers

    - It has $O(n)$ time complexity

    - !It has $O(2^n)$ time complexity

# DummyCategory/Subcategory

* What's the *access policy* of the ADT Queue?
    - !FIFO
    - LIFO
    - Based onrank
    - Based on key

* Consider the following code that uses the ADT Stack:

```cpp
PtStack s1 = stackCreate(10);
PtStack s2 = stackCreate(10);
for(int i=0; i<4; i++) {
    stackPush(s1, (i+1) );
}
int elem1, elem2;
while(!stackIsEmpty(s1)) {
    stackPop(s1, &elem1);
    if(!stackIsEmpty(s2)) {
        stackPop(s2, &elem2);
        stackPush(s2, (elem1 + elem2) );
    } else {
        stackPush(s2, elem1);
    }
}
//s1 = ? s2 = ?
```

What's the contents of the stacks `s1` e `s2` (from **bottom to top**) after the second loop?
    - !`s1 = {} e s2 = {10}`
    - `s1 = {1,2,3,4} e s2 = {4,7,9,10}`
    - `s1 = {} e s2 = {6}`
    - Other answer

* Consider the parcial specification of the ADT Complex and the following code:

```cpp{img}
#define COMPLEX_OK      0
#define COMPLEX_NULL    1

/**
 * @brief Retrieve the imaginary part of the complex number.
 *
 * @param c [in] PtComplex pointer to the number's data structure.
 * @param im [out] Address of variable to hold result
 *
 * @return COMPLEX_OK and imaginary part assigned to '*im'
 * @return COMPLEX_NULL if 'c' is NULL
 */
int complexIm (PtComplex c, double *im);

//----

PtComplex a = complexCreate(1, 8);
```

How to get the imaginary component of the complex number `a`?
    - !`double im = 0; complexIm(a, &im);`
    - `int im = complexIm(a);`
    - `double im = a->im;`
    - `double im = 0; complexIm(a, im);`

* Consider the following two approaches for implementing the **ADT Stack** using an *array list*:

![](stack_arraylist.png)

Which one would you choose for better eficiency?

    - !Approach **A**
    - Approach **B**

