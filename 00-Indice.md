# Tablero

## Pendientes (lo que dejé a medias)
```dataview
TABLE proyecto, siguiente
FROM "Chats"
WHERE estado = "en-curso"
SORT fecha DESC
```

## Proyectos activos
```dataview
LIST
FROM "Proyectos"
WHERE estado = "activo"
```
