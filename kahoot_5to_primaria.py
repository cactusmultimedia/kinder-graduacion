import openpyxl, random

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Kahoot"

# Kahoot format: Question, Answer 1, Answer 2, Answer 3, Answer 4, Time (s), Correct
ws.append(["Question", "Answer 1", "Answer 2", "Answer 3", "Answer 4", "Time (s)", "Correct"])

questions = [
    ("¿Cuánto es 342 + 589?", "831", "921", "731", "941", 1),
    ("¿Cuánto es 12 x 8?", "96", "88", "104", "92", 1),
    ("¿Cuánto es 450 / 9?", "50", "45", "40", "55", 1),
    ("¿Cuántos lados tiene un hexágono?", "6", "5", "7", "8", 1),
    ("¿Cuánto es 3/4 + 1/4?", "1", "2", "1/2", "3/8", 1),
    ("Área de un rectángulo de 5cm x 8cm?", "40 cm²", "13 cm²", "35 cm²", "45 cm²", 1),
    ("¿Cuánto es 1000 - 456?", "544", "554", "534", "564", 1),
    ("¿Qué palabra es un sustantivo propio?", "México", "perro", "bonito", "correr", 1),
    ("¿Cuál es el plural de lápiz?", "lápices", "lápizes", "lapices", "lápis", 1),
    ("¿Qué tipo de palabra es rápido?", "adverbio", "sustantivo", "adjetivo", "verbo", 1),
    ("¿Antónimo de feliz?", "triste", "contento", "alegre", "enojado", 1),
    ("¿Qué signo se usa para preguntar?", "¿?", "¡!", "…", ",", 1),
    ("¿La palabra hermoso es un?", "adjetivo", "sustantivo", "verbo", "artículo", 1),
    ("Planeta más cercano al Sol?", "Mercurio", "Venus", "Tierra", "Marte", 1),
    ("¿Qué necesitan las plantas para fotosíntesis?", "luz solar", "oxígeno", "nitrógeno", "agua salada", 1),
    ("¿Cuántos huesos tiene el adulto?", "206", "106", "306", "406", 1),
    ("¿Qué órgano bombea la sangre?", "corazón", "pulmones", "cerebro", "estómago", 1),
    ("¿El agua hierve a los ___ °C?", "100", "50", "90", "110", 1),
    ("Océano más grande del mundo?", "Pacífico", "Atlántico", "Índico", "Ártico", 1),
    ("¿Cuántos continentes hay?", "6", "5", "7", "4", 1),
    ("Capital de México?", "CDMX", "Guadalajara", "Monterrey", "Puebla", 1),
    ("¿Qué país tiene forma de bota?", "Italia", "Francia", "España", "Grecia", 1),
    ("¿Qué cordillera está en Sudamérica?", "Andes", "Himalaya", "Alpes", "Urales", 1),
    ("¿Año en que Colón llegó a América?", "1492", "1500", "1498", "1482", 1),
    ("¿Qué civilización hizo Machu Picchu?", "Inca", "Maya", "Azteca", "Olmeca", 1),
    ("Primer presidente de México?", "Guadalupe Victoria", "Benito Juárez", "Miguel Hidalgo", "Porfirio Díaz", 1),
    ("¿Año de Independencia de México?", "1810", "1821", "1812", "1808", 1),
    ("Derecho universal de los niños?", "educación", "trabajar", "votar", "manejar", 1),
    ("¿Qué es un acuerdo?", "regla aceptada por todos", "una opinión", "un castigo", "un juego", 1),
    ("Símbolo patrio de México?", "el águila real", "la serpiente", "el jaguar", "el venado", 1),
]

random.shuffle(questions)

for q, o1, o2, o3, o4, correct in questions:
    opts = [o1, o2, o3, o4]
    correct_text = opts[correct - 1]
    random.shuffle(opts)
    new_idx = opts.index(correct_text) + 1
    ws.append([q, opts[0], opts[1], opts[2], opts[3], 20, new_idx])

path = "/Users/navirami/Desktop/kahoot_5to_primaria.xlsx"
wb.save(path)
print(f"Listo! {len(questions)} preguntas -> {path}")
