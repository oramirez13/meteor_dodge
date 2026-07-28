# Conceptos Intermedios usados en Meteor Dodge

Este documento explica las estructuras de nivel intermedio que aparecen en el codigo, para que puedas estudiarlas por separado y entender lo que hace cada linea.

---

## 1. Comprension de Listas (List Comprehension)

### Sintaxis basica

```python
[nueva_expresion for elemento in lista_original if condicion]
```

### Donde aparece en el juego

```python
self.bullets = [b for b in self.bullets if not b.is_off_screen()]
```

### Que hace

Crea una **nueva lista** recorriendo la original, elemento por elemento:

1. Toma cada `b` de `self.bullets`
2. Verifica la condicion: `not b.is_off_screen()` (la bala sigue en pantalla)
3. Si la condicion es `True`, incluye `b` en la nueva lista
4. Si la condicion es `False`, la omite

### Equivalente sin comprension

```python
nueva_lista = []
for b in self.bullets:
    if not b.is_off_screen():
        nueva_lista.append(b)
self.bullets = nueva_lista
```

La comprension hace exactamente lo mismo en una sola linea.

### Variante: crear lista con solo los valores que nos interesan

```python
self.explosions = [e for e in self.explosions if e.is_alive()]
```

Filtra: conserva solo las explosiones cuyo `is_alive()` devuelve `True`.

---

## 2. Diccionarios Anidados

### Sintaxis basica

```python
nivel = {
    1: {
        "nombre": "Nebula",
        "velocidad": 5,
    },
    2: {
        "nombre": "Storm",
        "velocidad": 7,
    },
}
```

### Donde aparece en el juego

```python
LEVELS = {
    1: {
        "name": "Nebula",
        "background": "background_01.png",
        "meteor_min_speed": 3,
        "meteor_max_speed": 5,
        "spawn_rate": 30,
        "ammo_type": "normal",
    },
    2: {
        "name": "Storm",
        "background": "background_02.png",
        # ...
    },
}
```

### Que hace

- El diccionario `LEVELS` tiene **5 claves** (1, 2, 3, 4, 5), una por nivel.
- Cada valor es **otro diccionario** con la configuracion de ese nivel.
- Para acceder a un valor concreto: `LEVELS[1]["name"]` devuelve `"Nebula"`.
- Para obtener el nivel actual: `LEVELS[self.current_level]`.

### Ventaja

Los datos de los 5 niveles estan en un solo lugar. Si quieres cambiar la velocidad de un nivel, lo haces una vez. Sin diccionarios anidados tendrias 5 variables separadas o 5 listas paralelas, que son mas dificiles de mantener.

---

## 3. Slicing con `[:]` para Iteracion Segura

### Sintaxis basica

```python
for elemento in lista[:]:      # copia superficial de la lista
    lista.remove(elemento)     # modificar la original mientras iteras
```

### Donde aparece en el juego

```python
for bullet in self.bullets[:]:
    for meteor in self.meteors[:]:
        if bullet_rect.colliderect(meteor.get_rect()):
            self.meteors.remove(meteor)
            self.bullets.remove(bullet)
```

### Que hace

- `self.bullets[:]` crea una **copia** de la lista (con el operador slicing `[:]`).
- El bucle `for` itera sobre la **copia**.
- Cuando encuentras una colision, eliminas elementos de la **original** con `.remove()`.
- Como el bucle recorre la copia, eliminar elementos de la original no afecta la iteracion.

### Por que es necesario

Sin la copia `[:]`, si eliminas un elemento mientras iteras, los indices se desplazan y el bucle se salta el siguiente elemento. Esto causa bugs intermitentes dificiles de detectar.

### Ejemplo del problema

```python
lista = [1, 2, 3, 4, 5]
for i, n in enumerate(lista):   # MAL: itera sobre la original
    if n == 2:
        lista.remove(n)
    print(i, n)
# Imprime: 0 1, 1 2, 2 4, 3 5
# El 3 se salto porque al borrar el 2, el 3 paso al indice 2
# y el contador i ya avanzo a 2
```

---

## 4. Parametros Opcionales con Valores por Defecto

### Sintaxis basica

```python
def funcion(param1, param2=None):
    if param2 is None:
        param2 = "valor por defecto"
```

### Donde aparece en el juego

```python
def spawn_meteor(self, speed=None, speed_range=None):
    if len(self.meteors) < MAX_METEORS:
        if speed is not None:
            meteor = Meteor(self.meteor_images, (speed, speed))
        elif speed_range is not None:
            meteor = Meteor(self.meteor_images, speed_range)
        else:
            data = self.get_level_data()
            meteor = Meteor(self.meteor_images,
                (data["meteor_min_speed"], data["meteor_max_speed"]))
        self.meteors.append(meteor)
```

### Que hace

- `speed=None` significa: si el que llama no pasa este argumento, usa `None`.
- La funcion revisa: si pasaron speed exacto, usalo; si pasaron un rango, usalo; si no pasaron nada, usa los valores del nivel actual.
- Esto permite llamar a `spawn_meteor()` de 3 formas distintas segun el contexto.

---

## 5. El Bloque `if __name__ == "__main__"`

```python
if __name__ == "__main__":
    game = Game()
    game.run()
```

- `__name__` es una variable especial que Python asigna a cada archivo.
- Cuando ejecutas `python meteor_dodge.py` directamente, `__name__` vale `"__main__"`.
- Cuando importas el archivo desde otro (`from meteor_dodge import Game`), `__name__` vale `"meteor_dodge"` y el bloque no se ejecuta.
- Esto permite reutilizar las clases del juego desde otros scripts sin que el juego arranque solo.

---

## Resumen

| Concepto | Lo usas en | Que estudiar |
|---|---|---|
| List comprehension | Filtrar listas (balas, meteoros) | Estructura `[x for x in lista if cond]` |
| Diccionarios anidados | LEVELS, self.backgrounds | Acceder con `dict[clave][subclave]` |
| Slicing `[:]` | `for x in lista[:]` | Copia de lista, diferencia entre `[:]` y `list()` |
| Parametros opcionales | `spawn_meteor(speed=None)` | Valores por defecto, `is None` |
| `__name__ == "__main__"` | Entry point del juego | Ejecucion directa vs importacion |
