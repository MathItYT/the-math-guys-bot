Para demostrar que el algoritmo proporcionado es matemáticamente correcto, es decir, que para una lista arbitraria $L$ no vacía, la función `maximum(L)` retorna un número entero $n$ tal que para todo elemento $l$ de la lista, $n \geq l$ y además $n$ está dentro de la lista, utilizaremos una **demostración por inducción** sobre la longitud de la lista.

### **Base de la inducción**

Consideremos el caso más simple donde la lista $L$ tiene **únicamente un elemento**.

- **Caso**: $|L| = 1$

    Sea $L = [a]$, donde $a$ es un entero.

    Al ejecutar `maximum(L)`, la función verifica si la longitud de la lista es 1:

    ```py
    if len(x) == 1:
        return x[0]
    ```

    Entonces, retorna $a$. Claramente, $a$ es el único elemento de la lista, por lo tanto, cumple que para todo $l \in L$, $a \geq l$ (ya que $l = a$) y $a$ está en la lista.

    **Conclusión**: La propiedad se cumple para $|L| = 1$.

### **Paso inductivo**

Supongamos que la propiedad se cumple para cualquier lista de longitud $k$, es decir, para cualquier lista $L'$ con $|L'| = k$, `maximum(L')` retorna el máximo elemento de $L'$.

Ahora, consideremos una lista $L$ de longitud $k + 1$:

- **Caso inductivo**: $|L| = k + 1$

    Sea $L = [a_1, a_2, \dots, a_{k}, a_{k+1}]$.

    Al ejecutar `maximum(L)`, la función realiza la siguiente llamada recursiva:

    ```py
    prev = maximum(x[:-1])
    ```

    Aquí, `x[:-1]` corresponde a la lista $L' = [a_1, a_2, \dots, a_{k}]$, que tiene longitud $k$. Por hipótesis inductiva, `maximum(L')` retorna el máximo elemento de $L'$, denotémoslo por $m$.

    Luego, el algoritmo compara $m$ con el último elemento de $L$, es decir, $a_{k+1}$:

    ```py
    if prev > x[-1]:
        return prev
    return x[-1]
    ```

    - **Subcaso 1**: Si $m > a_{k+1}$, entonces $m$ es mayor que todos los elementos de $L'$, y por lo tanto, también es mayor que $a_{k+1}$. Por lo tanto, $m$ es el máximo de $L$.
    
    - **Subcaso 2**: Si $m \leq a_{k+1}$, entonces $a_{k+1}$ es mayor o igual que todos los elementos de $L'$ (incluyendo a $m$), por lo tanto, $a_{k+1}$ es el máximo de $L$.

    En ambos subcasos, `maximum(L)` retorna el elemento correcto que es el máximo de la lista $L$.

    **Conclusión**: La propiedad se mantiene para una lista de longitud $k + 1$.

### **Conclusión de la inducción**

Por el principio de inducción matemática, la propiedad se cumple para cualquier lista no vacía $L$ de enteros, es decir, `maximum(L)` retorna un número entero $n$ que es mayor o igual a todos los elementos de $L$ y que además pertenece a la lista $L$.